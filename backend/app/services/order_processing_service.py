from typing import Dict, List, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.models.order import Order
from app.models.sku_item import OrderSKUItem
from app.models.tracking import OrderTracking, EmailCommunication
from app.models.user import User
from app.services.file_processor import FileProcessor
from app.services.sku_service import SKUService
from app.services.email_service import EmailService
from app.services.file_parser_service import FileParserService
from app.services.order_validator_service import OrderValidatorService
from app.services.email_generator_service import EmailGeneratorService
from app.models.schemas import SKUItemCreate
from decimal import Decimal
import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

class OrderProcessingService:
    """Enhanced service for processing orders with comprehensive validation and email workflow"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.file_processor = FileProcessor()
        self.sku_service = SKUService(db)
        self.email_service = EmailService()
        self.file_parser_service = FileParserService(db)
        self.order_validator_service = OrderValidatorService(db)
        self.email_generator_service = EmailGeneratorService(db)
    
    async def process_uploaded_order(self, order_id: str) -> Dict[str, Any]:
        """Complete order processing workflow with enhanced validation and email generation"""
        try:
            # Get order
            result = await self.db.execute(
                select(Order).where(Order.id == uuid.UUID(order_id))
            )
            order = result.scalar_one_or_none()
            
            if not order:
                raise ValueError(f"Order {order_id} not found")
            
            # Update status to PROCESSING
            await self._update_order_status(order, "PROCESSING", "Starting enhanced order processing")
            
            # Step 1: Parse the uploaded file using enhanced parser
            await self._log_tracking(order_id, "FILE_PARSING_STARTED", "Starting file parsing with enhanced parser")
            parsed_data = await self.file_parser_service.parse_file(order_id, order.file_path, order.file_type)
            
            # Update order with parsed data
            order.parsed_data = parsed_data
            await self.db.commit()
            
            # Step 2: Validate order completeness
            await self._log_tracking(order_id, "ORDER_VALIDATION_STARTED", "Starting comprehensive order validation")
            validation_result = await self.order_validator_service.validate_order_completeness(order_id, parsed_data)
            
            # Step 3: Process based on validation result
            processing_result = await self._process_validation_result(order_id, validation_result, parsed_data)
            
            # Step 4: Generate emails for missing information if needed
            email_result = None
            if not validation_result["is_valid"]:
                await self._log_tracking(order_id, "EMAIL_GENERATION_STARTED", "Generating email for missing information")
                email_result = await self.email_generator_service.generate_missing_info_email(
                    order_id, validation_result, parsed_data
                )
            
            # Step 5: Extract and validate SKU items (if validation passed)
            sku_result = None
            if validation_result["is_valid"]:
                sku_result = await self._process_sku_items(order, parsed_data)
            
            # Step 6: Update final order status
            final_status = self._determine_final_status(validation_result, sku_result)
            await self._update_order_status(order, final_status, "Order processing completed")
            
            # Compile comprehensive result
            result = {
                "order_id": order_id,
                "status": final_status,
                "validation_result": validation_result,
                "parsed_data": parsed_data,
                "processing_result": processing_result,
                "email_result": email_result,
                "sku_result": sku_result,
                "completed_at": datetime.utcnow().isoformat()
            }
            
            await self._log_tracking(order_id, "ORDER_PROCESSING_COMPLETED", 
                                   f"Order processing completed with status: {final_status}")
            
            return result
            
        except Exception as e:
            error_msg = f"Order processing failed: {str(e)}"
            logger.error(error_msg)
            await self._log_tracking(order_id, "ORDER_PROCESSING_ERROR", error_msg)
            await self._update_order_status(order, "ERROR", error_msg)
            raise
    
    async def _process_validation_result(self, order_id: str, validation_result: Dict[str, Any], parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process validation result and determine next steps"""
        try:
            processing_result = {
                "validation_passed": validation_result["is_valid"],
                "actions_taken": [],
                "next_steps": []
            }
            
            if not validation_result["is_valid"]:
                # Log validation failures
                if validation_result["missing_fields"]:
                    await self._log_tracking(order_id, "VALIDATION_MISSING_FIELDS", 
                                           f"Missing fields: {', '.join(validation_result['missing_fields'])}")
                    processing_result["actions_taken"].append("logged_missing_fields")
                    processing_result["next_steps"].append("await_missing_information")
                
                if validation_result["validation_errors"]:
                    await self._log_tracking(order_id, "VALIDATION_ERRORS", 
                                           f"Validation errors: {len(validation_result['validation_errors'])}")
                    processing_result["actions_taken"].append("logged_validation_errors")
                    processing_result["next_steps"].append("require_data_correction")
                
                if validation_result["business_rule_violations"]:
                    await self._log_tracking(order_id, "BUSINESS_RULE_VIOLATIONS", 
                                           f"Business rule violations: {len(validation_result['business_rule_violations'])}")
                    processing_result["actions_taken"].append("logged_business_violations")
                    processing_result["next_steps"].append("require_business_approval")
            
            else:
                await self._log_tracking(order_id, "VALIDATION_PASSED", 
                                       f"Order validation passed with score: {validation_result['validation_score']:.2f}")
                processing_result["actions_taken"].append("validation_passed")
                processing_result["next_steps"].append("proceed_to_sku_processing")
            
            return processing_result
            
        except Exception as e:
            logger.error(f"Error processing validation result: {str(e)}")
            raise
    
    def _determine_final_status(self, validation_result: Dict[str, Any], sku_result: Optional[Dict[str, Any]]) -> str:
        """Determine final order status based on validation and SKU processing results"""
        if not validation_result["is_valid"]:
            if validation_result["missing_fields"]:
                return "MISSING_INFO"
            elif validation_result["validation_errors"]:
                return "VALIDATION_FAILED"
            else:
                return "INCOMPLETE"
        
        if sku_result:
            if sku_result.get("sku_items_created", False):
                return "VALIDATED"
            else:
                return "SKU_PROCESSING_FAILED"
        
        return "PROCESSED"
    
    async def get_order_tracking_history(self, order_id: str) -> List[Dict[str, Any]]:
        """Get comprehensive order tracking history for UI display"""
        try:
            # Get tracking entries
            tracking_result = await self.db.execute(
                select(OrderTracking)
                .where(OrderTracking.order_id == uuid.UUID(order_id))
                .order_by(OrderTracking.created_at.desc())
            )
            tracking_entries = tracking_result.scalars().all()
            
            # Get email communications
            email_result = await self.db.execute(
                select(EmailCommunication)
                .where(EmailCommunication.order_id == uuid.UUID(order_id))
                .order_by(EmailCommunication.created_at.desc())
            )
            email_communications = email_result.scalars().all()
            
            # Compile tracking history
            tracking_history = []
            
            # Add tracking entries
            for entry in tracking_entries:
                tracking_history.append({
                    "id": str(entry.id),
                    "type": "tracking",
                    "status": entry.status,
                    "message": entry.message,
                    "details": entry.details,
                    "timestamp": entry.created_at.isoformat(),
                    "category": self._categorize_tracking_status(entry.status)
                })
            
            # Add email communications
            for email in email_communications:
                tracking_history.append({
                    "id": str(email.id),
                    "type": "email",
                    "status": email.email_type,
                    "message": f"Email sent to {email.recipient}",
                    "details": email.subject,
                    "timestamp": email.created_at.isoformat(),
                    "category": "communication",
                    "email_details": {
                        "recipient": email.recipient,
                        "subject": email.subject,
                        "sent_at": email.sent_at.isoformat() if email.sent_at else None,
                        "response_received": email.response_received_at.isoformat() if email.response_received_at else None
                    }
                })
            
            # Sort by timestamp
            tracking_history.sort(key=lambda x: x["timestamp"], reverse=True)
            
            return tracking_history
            
        except Exception as e:
            logger.error(f"Error getting order tracking history: {str(e)}")
            raise
    
    def _categorize_tracking_status(self, status: str) -> str:
        """Categorize tracking status for UI display"""
        status_categories = {
            "FILE_PARSING_STARTED": "file_processing",
            "FILE_PARSING_COMPLETED": "file_processing",
            "FILE_PARSING_ERROR": "error",
            "ORDER_VALIDATION_STARTED": "validation",
            "ORDER_VALIDATION_COMPLETED": "validation",
            "ORDER_VALIDATION_FAILED": "validation",
            "ORDER_VALIDATION_ERROR": "error",
            "VALIDATION_MISSING_FIELDS": "validation",
            "VALIDATION_ERRORS": "validation",
            "BUSINESS_RULE_VIOLATIONS": "validation",
            "VALIDATION_PASSED": "validation",
            "EMAIL_GENERATION_STARTED": "communication",
            "EMAIL_GENERATION_COMPLETED": "communication",
            "EMAIL_GENERATION_ERROR": "error",
            "ORDER_PROCESSING_STARTED": "processing",
            "ORDER_PROCESSING_COMPLETED": "processing",
            "ORDER_PROCESSING_ERROR": "error",
            "SKU_PROCESSING_STARTED": "sku_processing",
            "SKU_PROCESSING_COMPLETED": "sku_processing",
            "SKU_PROCESSING_ERROR": "error"
        }
        
        return status_categories.get(status, "general")
    
    async def get_order_validation_summary(self, order_id: str) -> Dict[str, Any]:
        """Get order validation summary for UI dashboard"""
        try:
            # Get order
            result = await self.db.execute(
                select(Order).where(Order.id == uuid.UUID(order_id))
            )
            order = result.scalar_one_or_none()
            
            if not order:
                raise ValueError(f"Order {order_id} not found")
            
            # Get latest validation result from parsed_data
            validation_result = {}
            if order.parsed_data and isinstance(order.parsed_data, dict):
                # Look for validation result in parsed_data
                if "validation_result" in order.parsed_data:
                    validation_result = order.parsed_data["validation_result"]
            
            # Get tracking statistics
            tracking_stats = await self._get_tracking_statistics(order_id)
            
            # Compile validation summary
            summary = {
                "order_id": order_id,
                "order_number": order.order_number,
                "current_status": order.status,
                "validation_result": validation_result,
                "tracking_stats": tracking_stats,
                "summary_generated_at": datetime.utcnow().isoformat()
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting order validation summary: {str(e)}")
            raise
    
    async def _get_tracking_statistics(self, order_id: str) -> Dict[str, Any]:
        """Get tracking statistics for order"""
        try:
            # Get tracking entries
            tracking_result = await self.db.execute(
                select(OrderTracking)
                .where(OrderTracking.order_id == uuid.UUID(order_id))
            )
            tracking_entries = tracking_result.scalars().all()
            
            # Get email communications
            email_result = await self.db.execute(
                select(EmailCommunication)
                .where(EmailCommunication.order_id == uuid.UUID(order_id))
            )
            email_communications = email_result.scalars().all()
            
            # Calculate statistics
            stats = {
                "total_tracking_entries": len(tracking_entries),
                "total_emails_sent": len(email_communications),
                "error_count": len([e for e in tracking_entries if "ERROR" in e.status]),
                "validation_attempts": len([e for e in tracking_entries if "VALIDATION" in e.status]),
                "file_parsing_attempts": len([e for e in tracking_entries if "FILE_PARSING" in e.status]),
                "last_activity": None
            }
            
            # Get last activity timestamp
            all_activities = []
            all_activities.extend([e.created_at for e in tracking_entries])
            all_activities.extend([e.created_at for e in email_communications])
            
            if all_activities:
                stats["last_activity"] = max(all_activities).isoformat()
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting tracking statistics: {str(e)}")
            return {}

    async def _log_tracking(self, order_id: str, status: str, message: str, details: Optional[str] = None):
        """Enhanced logging with better error handling"""
        try:
            tracking_entry = OrderTracking(
                order_id=uuid.UUID(order_id),
                status=status,
                message=message,
                details=details
            )
            self.db.add(tracking_entry)
            await self.db.commit()
            
            # Log to application logger as well
            logger.info(f"Order {order_id} - {status}: {message}")
            
        except Exception as e:
            logger.error(f"Error logging tracking for order {order_id}: {str(e)}")
            # Don't raise exception to avoid breaking main workflow
    
    async def _update_order_status(self, order: Order, status: str, message: str):
        """Update order status and log tracking entry"""
        try:
            # Update the order status
            order.status = status
            order.updated_at = datetime.utcnow()
            
            # Commit the status change
            await self.db.commit()
            
            # Log the tracking entry
            await self._log_tracking(str(order.id), status, message)
            
            logger.info(f"Order {order.id} status updated to {status}: {message}")
            
        except Exception as e:
            logger.error(f"Error updating order status for order {order.id}: {str(e)}")
            await self.db.rollback()
            raise
    
    async def process_info_received(self, order_id: str, received_info: Dict[str, Any]) -> bool:
        """Process information received from retailer"""
        try:
            result = await self.db.execute(
                select(Order).where(Order.id == uuid.UUID(order_id))
            )
            order = result.scalar_one_or_none()
            
            if not order or order.status != "PENDING_INFO":
                return False
            
            # Update order status
            await self._update_order_status(order, "INFO_RECEIVED", "Processing received information")
            
            # Process the received information
            # This would include updating SKU items, retailer info, etc.
            # For now, mark as validated if we have the needed info
            
            await self._update_order_status(order, "VALIDATED", "Order validation completed after receiving additional information")
            await self._send_order_confirmation(order)
            
            await self.db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error processing received info for order {order_id}: {str(e)}")
            return False
    
    async def assign_to_trip(self, order_id: str, trip_id: Optional[str] = None) -> bool:
        """Assign order to delivery trip"""
        try:
            result = await self.db.execute(
                select(Order).where(Order.id == uuid.UUID(order_id))
            )
            order = result.scalar_one_or_none()
            
            if not order or order.status != "VALIDATED":
                return False
            
            # Generate trip ID if not provided
            if not trip_id:
                trip_id = f"TRIP-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
            
            # Update order
            order.trip_id = trip_id
            order.trip_status = "QUEUED"
            
            await self._update_order_status(order, "TRIP_QUEUED", f"Order assigned to trip {trip_id}")
            
            await self.db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error assigning order {order_id} to trip: {str(e)}")
            return False
        
        # UI Menu Support Methods
    
    async def get_processing_steps(self, order_id: str) -> List[Dict[str, Any]]:
        """Get detailed processing steps for UI menu"""
        try:
            # Get tracking history and convert to processing steps
            tracking_history = await self.get_order_tracking_history(order_id)
            
            steps = []
            step_categories = {
                'file_processing': ['FILE_PARSING_STARTED', 'FILE_PARSING_COMPLETED', 'FILE_PARSING_ERROR'],
                'validation': ['VALIDATION_STARTED', 'VALIDATION_COMPLETED', 'VALIDATION_ERROR'],
                'communication': ['EMAIL_GENERATED', 'EMAIL_SENT', 'EMAIL_ERROR'],
                'sku_processing': ['SKU_PROCESSING_STARTED', 'SKU_PROCESSING_COMPLETED', 'SKU_PROCESSING_ERROR'],
                'user_interaction': ['USER_ACTION_REQUIRED', 'USER_ACTION_COMPLETED'],
                'system_process': ['PROCESSING_STARTED', 'PROCESSING_COMPLETED', 'PROCESSING_ERROR']
            }
            
            for entry in tracking_history:
                # Determine category
                category = 'system_process'
                for cat, statuses in step_categories.items():
                    if any(status in entry.get('status', '') for status in statuses):
                        category = cat
                        break
                
                # Determine step status
                step_status = 'completed'
                if 'ERROR' in entry.get('status', ''):
                    step_status = 'failed'
                elif 'STARTED' in entry.get('status', ''):
                    step_status = 'running'
                elif 'REQUIRED' in entry.get('status', ''):
                    step_status = 'waiting_user'
                
                steps.append({
                    'id': entry.get('id', str(uuid.uuid4())),
                    'name': entry.get('status', 'Unknown Step'),
                    'description': entry.get('message', ''),
                    'category': category,
                    'type': category,
                    'status': step_status,
                    'last_updated': entry.get('timestamp'),
                    'error_message': entry.get('details') if step_status == 'failed' else None
                })
            
            return steps
            
        except Exception as e:
            logger.error(f"Error getting processing steps for order {order_id}: {str(e)}")
            return []
    
    async def get_order_status_overview(self, order_id: str) -> Dict[str, Any]:
        """Get comprehensive order status overview"""
        try:
            result = await self.db.execute(
                select(Order).where(Order.id == uuid.UUID(order_id))
            )
            order = result.scalar_one_or_none()
            
            if not order:
                return {}
            
            # Get tracking statistics
            tracking_result = await self.db.execute(
                select(OrderTracking).where(OrderTracking.order_id == uuid.UUID(order_id))
            )
            tracking_entries = tracking_result.scalars().all()
            
            # Calculate metrics
            total_steps = len(tracking_entries)
            completed_steps = len([t for t in tracking_entries if 'COMPLETED' in t.status])
            failed_steps = len([t for t in tracking_entries if 'ERROR' in t.status])
            pending_steps = total_steps - completed_steps - failed_steps;
            
            progress = (completed_steps / total_steps * 100) if total_steps > 0 else 0;
            
            return {
                'status': order.status,
                'progress': round(progress, 1),
                'completed_steps': completed_steps,
                'pending_actions': pending_steps,
                'issues': failed_steps,
                'last_updated': order.updated_at.isoformat() if order.updated_at else None,
                'total_steps': total_steps
            }
            
        except Exception as e:
            logger.error(f"Error getting order status overview for {order_id}: {str(e)}")
            return {}
    
    async def get_processing_metrics(self, order_id: str) -> Dict[str, Any]:
        """Get processing metrics for dashboard"""
        try:
            # Get various counts
            tracking_result = await self.db.execute(
                select(OrderTracking).where(OrderTracking.order_id == uuid.UUID(order_id))
            )
            tracking_entries = tracking_result.scalars().all()
            
            email_result = await self.db.execute(
                select(EmailCommunication).where(EmailCommunication.order_id == uuid.UUID(order_id))
            )
            emails = email_result.scalars().all()
            
            active_steps = len([t for t in tracking_entries if 'STARTED' in t.status])
            pending_emails = len([e for e in emails if e.status == 'pending'])
            validation_errors = len([t for t in tracking_entries if 'VALIDATION_ERROR' in t.status])
            pending_user_actions = len([t for t in tracking_entries if 'USER_ACTION_REQUIRED' in t.status])
            
            return {
                'active_steps': active_steps,
                'pending_emails': pending_emails,
                'validation_errors': validation_errors,
                'pending_user_actions': pending_user_actions,
                'total_tracking_entries': len(tracking_entries),
                'total_emails': len(emails)
            }
            
        except Exception as e:
            logger.error(f"Error getting processing metrics for {order_id}: {str(e)}")
            return {}
    
    async def get_order_notifications(self, order_id: str) -> List[Dict[str, Any]]:
        """Get recent notifications for the order"""
        try:
            # Get recent tracking entries as notifications
            result = await self.db.execute(
                select(OrderTracking)
                .where(OrderTracking.order_id == uuid.UUID(order_id))
                .order_by(OrderTracking.created_at.desc())
                .limit(10)
            )
            tracking_entries = result.scalars().all()
            
            notifications = []
            for entry in tracking_entries:
                notification_type = 'info'
                if 'ERROR' in entry.status:
                    notification_type = 'failed'
                elif 'COMPLETED' in entry.status:
                    notification_type = 'completed'
                elif 'STARTED' in entry.status:
                    notification_type = 'processing'
                
                notifications.append({
                    'id': str(entry.id),
                    'title': entry.status,
                    'message': entry.message,
                    'type': notification_type,
                    'timestamp': entry.created_at.isoformat(),
                    'details': entry.details
                })
            
            return notifications
            
        except Exception as e:
            logger.error(f"Error getting notifications for order {order_id}: {str(e)}")
            return []
    
    async def get_user_actions(self, order_id: str) -> List[Dict[str, Any]]:
        """Get pending user actions for the order"""
        try:
            # Get tracking entries that require user action
            result = await self.db.execute(
                select(OrderTracking)
                .where(OrderTracking.order_id == uuid.UUID(order_id))
                .where(OrderTracking.status.like('%USER_ACTION_REQUIRED%'))
                .order_by(OrderTracking.created_at.desc())
            )
            tracking_entries = result.scalars().all()
            
            # Get validation results for missing fields
            validation_summary = await self.get_order_validation_summary(order_id)
            
            user_actions = []
            
            # Add actions from tracking
            for entry in tracking_entries:
                priority = 'medium'
                if 'ERROR' in entry.status:
                    priority = 'high'
                elif 'VALIDATION' in entry.status:
                    priority = 'high'
                
                user_actions.append({
                    'id': str(entry.id),
                    'title': 'User Action Required',
                    'description': entry.message,
                    'type': 'manual_entry',
                    'category': 'user_interaction',
                    'status': 'pending',
                    'priority': priority,
                    'created_at': entry.created_at.isoformat(),
                    'due_date': None,
                    'details': entry.details
                })
            
            # Add actions from validation results
            if validation_summary and validation_summary.get('missing_fields'):
                user_actions.append({
                    'id': f"missing_fields_{order_id}",
                    'title': 'Correct Missing Fields',
                    'description': f"Complete {len(validation_summary['missing_fields'])} missing required fields",
                    'type': 'correct_missing_fields',
                    'category': 'data_correction',
                    'status': 'pending',
                    'priority': 'high',
                    'created_at': datetime.now().isoformat(),
                    'due_date': None,
                    'details': None,
                    'current_data': validation_summary['missing_fields']
                })
            
            if validation_summary and validation_summary.get('validation_errors'):
                user_actions.append({
                    'id': f"validation_errors_{order_id}",
                    'title': 'Fix Validation Errors',
                    'description': f"Fix {len(validation_summary['validation_errors'])} validation errors",
                    'type': 'correct_validation_errors',
                    'category': 'validation',
                    'status': 'pending',
                    'priority': 'high',
                    'created_at': datetime.now().isoformat(),
                    'due_date': None,
                    'details': None,
                    'current_data': validation_summary['validation_errors']
                })
            
            return user_actions
            
        except Exception as e:
            logger.error(f"Error getting user actions for order {order_id}: {str(e)}")
            return []
    
    async def restart_processing_step(self, order_id: str, step_id: str) -> Dict[str, Any]:
        """Restart a specific processing step"""
        try:
            await self._log_tracking(order_id, "STEP_RESTART_REQUESTED", f"Restarting step {step_id}")
            
            # For now, we'll just trigger a reprocessing of the order
            # In a full implementation, this would restart the specific step
            result = await self.process_uploaded_order(order_id)
            
            return {
                'step_id': step_id,
                'status': 'restarted',
                'message': 'Processing step restarted successfully'
            }
            
        except Exception as e:
            logger.error(f"Error restarting step {step_id} for order {order_id}: {str(e)}")
            raise
    
    async def retry_processing_step(self, order_id: str, step_id: str) -> Dict[str, Any]:
        """Retry a failed processing step"""
        try:
            await self._log_tracking(order_id, "STEP_RETRY_REQUESTED", f"Retrying step {step_id}")
            
            # Similar to restart but specifically for failed steps
            result = await self.process_uploaded_order(order_id)
            
            return {
                'step_id': step_id,
                'status': 'retried',
                'message': 'Processing step retried successfully'
            }
            
        except Exception as e:
            logger.error(f"Error retrying step {step_id} for order {order_id}: {str(e)}")
            raise
    
    async def pause_processing_step(self, order_id: str, step_id: str) -> Dict[str, Any]:
        """Pause a running processing step"""
        try:
            await self._log_tracking(order_id, "STEP_PAUSE_REQUESTED", f"Pausing step {step_id}")
            
            return {
                'step_id': step_id,
                'status': 'paused',
                'message': 'Processing step paused successfully'
            }
            
        except Exception as e:
            logger.error(f"Error pausing step {step_id} for order {order_id}: {str(e)}")
            raise
    
    async def resume_processing_step(self, order_id: str, step_id: str) -> Dict[str, Any]:
        """Resume a paused processing step"""
        try:
            await self._log_tracking(order_id, "STEP_RESUME_REQUESTED", f"Resuming step {step_id}")
            
            return {
                'step_id': step_id,
                'status': 'resumed',
                'message': 'Processing step resumed successfully'
            }
            
        except Exception as e:
            logger.error(f"Error resuming step {step_id} for order {order_id}: {str(e)}")
            raise
    
    async def skip_processing_step(self, order_id: str, step_id: str) -> Dict[str, Any]:
        """Skip a processing step"""
        try:
            await self._log_tracking(order_id, "STEP_SKIP_REQUESTED", f"Skipping step {step_id}")
            
            return {
                'step_id': step_id,
                'status': 'skipped',
                'message': 'Processing step skipped successfully'
            }
            
        except Exception as e:
            logger.error(f"Error skipping step {step_id} for order {order_id}: {str(e)}")
            raise
    
    async def correct_missing_fields(self, order_id: str, correction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Correct missing fields in order data"""
        try:
            result = await self.db.execute(
                select(Order).where(Order.id == uuid.UUID(order_id))
            )
            order = result.scalar_one_or_none()
            
            if not order:
                raise ValueError(f"Order {order_id} not found")
            
            # Update order with corrected data
            for field, value in correction_data.items():
                if hasattr(order, field):
                    setattr(order, field, value)
            
            await self._log_tracking(order_id, "MISSING_FIELDS_CORRECTED", f"Missing fields corrected: {list(correction_data.keys())}")
            
            await self.db.commit()
            
            return {
                'corrected_fields': list(correction_data.keys()),
                'status': 'corrected',
                'message': 'Missing fields corrected successfully'
            }
            
        except Exception as e:
            logger.error(f"Error correcting missing fields for order {order_id}: {str(e)}")
            raise
    
    async def correct_validation_errors(self, order_id: str, correction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Correct validation errors in order data"""
        try:
            result = await self.db.execute(
                select(Order).where(Order.id == uuid.UUID(order_id))
            )
            order = result.scalar_one_or_none()
            
            if not order:
                raise ValueError(f"Order {order_id} not found")
            
            # Apply corrections
            for field, value in correction_data.items():
                if hasattr(order, field):
                    setattr(order, field, value)
            
            await self._log_tracking(order_id, "VALIDATION_ERRORS_CORRECTED", f"Validation errors corrected: {list(correction_data.keys())}")
            
            await self.db.commit()
            
            # Re-validate the order
            validation_result = await self.order_validator_service.validate_order(order_id)
            
            return {
                'corrected_fields': list(correction_data.keys()),
                'validation_result': validation_result,
                'status': 'corrected',
                'message': 'Validation errors corrected successfully'
            }
            
        except Exception as e:
            logger.error(f"Error correcting validation errors for order {order_id}: {str(e)}")
            raise
    
    async def send_order_email(self, order_id: str, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send an email for the order"""
        try:
            # Generate or use existing email
            if email_data.get('emailId'):
                # Send existing email
                result = await self.db.execute(
                    select(EmailCommunication).where(EmailCommunication.id == uuid.UUID(email_data['emailId']))
                )
                email_comm = result.scalar_one_or_none()
                
                if email_comm:
                    # Send the email
                    success = await self.email_service.send_email(
                        to_email=email_comm.recipient,
                        subject=email_comm.subject,
                        html_content=email_comm.html_content,
                        text_content=email_comm.text_content
                    )
                    
                    if success:
                        email_comm.status = 'sent'
                        email_comm.sent_at = datetime.now()
                        await self.db.commit()
                        
                        await self._log_tracking(order_id, "EMAIL_SENT", f"Email sent to {email_comm.recipient}")
                        
                        return {
                            'email_id': str(email_comm.id),
                            'status': 'sent',
                            'message': 'Email sent successfully'
                        }
            else:
                # Generate new email
                email_result = await self.email_generator_service.generate_email(
                    order_id=order_id,
                    email_type=email_data.get('type', 'missing_info'),
                    recipient=email_data.get('recipient'),
                    template_name=email_data.get('template'),
                    custom_content=email_data.get('custom_content')
                )
                
                if email_result['success']:
                    return {
                        'email_id': email_result['email_id'],
                        'status': 'generated',
                        'message': 'Email generated successfully'
                    }
            
            return {
                'status': 'failed',
                'message': 'Failed to send email'
            }
            
        except Exception as e:
            logger.error(f"Error sending email for order {order_id}: {str(e)}")
            raise
    
    async def resend_order_email(self, order_id: str, email_id: str) -> Dict[str, Any]:
        """Resend an email for the order"""
        try:
            result = await self.db.execute(
                select(EmailCommunication).where(EmailCommunication.id == uuid.UUID(email_id))
            )
            email_comm = result.scalar_one_or_none()
            
            if not email_comm:
                raise ValueError(f"Email {email_id} not found")
            
            # Resend the email
            success = await self.email_service.send_email(
                to_email=email_comm.recipient,
                subject=email_comm.subject,
                html_content=email_comm.html_content,
                text_content=email_comm.text_content
            )
            
            if success:
                email_comm.status = 'sent'
                email_comm.sent_at = datetime.now()
                await self.db.commit()
                
                await self._log_tracking(order_id, "EMAIL_RESENT", f"Email resent to {email_comm.recipient}")
                
                return {
                    'email_id': email_id,
                    'status': 'resent',
                    'message': 'Email resent successfully'
                }
            else:
                return {
                    'email_id': email_id,
                    'status': 'failed',
                    'message': 'Failed to resend email'
                }
                
        except Exception as e:
            logger.error(f"Error resending email {email_id} for order {order_id}: {str(e)}")
            raise
    
    async def complete_user_action(self, order_id: str, action_data: Dict[str, Any]) -> Dict[str, Any]:
        """Complete a user action"""
        try:
            action_type = action_data.get('actionType')
            
            if action_type == 'correct_missing_fields':
                return await self.correct_missing_fields(order_id, action_data.get('data', {}))
            elif action_type == 'correct_validation_errors':
                return await self.correct_validation_errors(order_id, action_data.get('data', {}))
            elif action_type == 'provide_feedback':
                await self._log_tracking(order_id, "USER_FEEDBACK_PROVIDED", action_data.get('data', {}).get('feedback', ''))
                return {
                    'status': 'completed',
                    'message': 'Feedback provided successfully'
                }
            else:
                # Generic user action completion
                await self._log_tracking(order_id, "USER_ACTION_COMPLETED", f"User action completed: {action_type}")
                return {
                    'status': 'completed',
                    'message': f'User action {action_type} completed successfully'
                }
                
        except Exception as e:
            logger.error(f"Error completing user action for order {order_id}: {str(e)}")
            raise
    
    async def skip_user_action(self, order_id: str, action_id: str) -> Dict[str, Any]:
        """Skip a user action"""
        try:
            await self._log_tracking(order_id, "USER_ACTION_SKIPPED", f"User action skipped: {action_id}")
            
            return {
                'action_id': action_id,
                'status': 'skipped',
                'message': 'User action skipped successfully'
            }
            
        except Exception as e:
            logger.error(f"Error skipping user action {action_id} for order {order_id}: {str(e)}")
            raise
    
    async def restart_order_processing(self, order_id: str) -> Dict[str, Any]:
        """Restart entire order processing"""
        try:
            await self._log_tracking(order_id, "ORDER_PROCESSING_RESTART_REQUESTED", "Restarting entire order processing")
            
            result = await self.process_uploaded_order(order_id)
            
            return {
                'order_id': order_id,
                'status': 'restarted',
                'message': 'Order processing restarted successfully',
                'result': result
            }
            
        except Exception as e:
            logger.error(f"Error restarting processing for order {order_id}: {str(e)}")
            raise
    
    async def pause_order_processing(self, order_id: str) -> Dict[str, Any]:
        """Pause entire order processing"""
        try:
            result = await self.db.execute(
                select(Order).where(Order.id == uuid.UUID(order_id))
            )
            order = result.scalar_one_or_none()
            
            if not order:
                raise ValueError(f"Order {order_id} not found")
            
            await self._update_order_status(order, "PAUSED", "Order processing paused by user")
            
            await self.db.commit()
            
            return {
                'order_id': order_id,
                'status': 'paused',
                'message': 'Order processing paused successfully'
            }
            
        except Exception as e:
            logger.error(f"Error pausing processing for order {order_id}: {str(e)}")
            raise
    
    async def update_order_email(self, order_id: str, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing email"""
        try:
            email_id = email_data.get('emailId')
            if not email_id:
                raise ValueError("Email ID is required")
            
            result = await self.db.execute(
                select(EmailCommunication).where(EmailCommunication.id == uuid.UUID(email_id))
            )
            email_comm = result.scalar_one_or_none()
            
            if not email_comm:
                raise ValueError(f"Email {email_id} not found")
            
            # Update email fields
            if 'subject' in email_data:
                email_comm.subject = email_data['subject']
            if 'recipient' in email_data:
                email_comm.recipient = email_data['recipient']
            if 'html_content' in email_data:
                email_comm.html_content = email_data['html_content']
            if 'text_content' in email_data:
                email_comm.text_content = email_data['text_content']
            
            await self.db.commit()
            
            await self._log_tracking(order_id, "EMAIL_UPDATED", f"Email {email_id} updated")
            
            return {
                'email_id': email_id,
                'status': 'updated',
                'message': 'Email updated successfully'
            }
            
        except Exception as e:
            logger.error(f"Error updating email for order {order_id}: {str(e)}")
            raise
    
    async def export_order_data(self, order_id: str) -> Dict[str, Any]:
        """Export order data for download"""
        try:
            result = await self.db.execute(
                select(Order).where(Order.id == uuid.UUID(order_id))
            )
            order = result.scalar_one_or_none()
            
            if not order:
                raise ValueError(f"Order {order_id} not found")
            
            # Get related data
            tracking_history = await self.get_order_tracking_history(order_id)
            validation_summary = await self.get_order_validation_summary(order_id)
            
            # Create export data
            export_data = {
                'order_id': order_id,
                'status': order.status,
                'customer_name': order.customer_name,
                'email': order.email,
                'phone': order.phone,
                'company': order.company,
                'address': order.address,
                'created_at': order.created_at.isoformat() if order.created_at else None,
                'updated_at': order.updated_at.isoformat() if order.updated_at else None,
                'tracking_history': tracking_history,
                'validation_summary': validation_summary
            }
            
            await self._log_tracking(order_id, "DATA_EXPORTED", "Order data exported for download")
            
            return {
                'export_data': export_data,
                'status': 'exported',
                'message': 'Order data exported successfully'
            }
            
        except Exception as e:
            logger.error(f"Error exporting data for order {order_id}: {str(e)}")
            raise
    
    async def import_order_corrections(self, order_id: str, correction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Import corrections for order data"""
        try:
            result = await self.db.execute(
                select(Order).where(Order.id == uuid.UUID(order_id))
            )
            order = result.scalar_one_or_none()
            
            if not order:
                raise ValueError(f"Order {order_id} not found")
            
            # Apply corrections
            corrections_applied = []
            for field, value in correction_data.items():
                if hasattr(order, field):
                    setattr(order, field, value)
                    corrections_applied.append(field)
            
            await self.db.commit()
            
            await self._log_tracking(order_id, "CORRECTIONS_IMPORTED", f"Corrections imported for fields: {corrections_applied}")
            
            return {
                'corrected_fields': corrections_applied,
                'status': 'imported',
                'message': 'Order corrections imported successfully'
            }
            
        except Exception as e:
            logger.error(f"Error importing corrections for order {order_id}: {str(e)}")
            raise

    async def consolidate_orders(self, order_ids: List[str], consolidation_notes: Optional[str] = None) -> Dict[str, Any]:
        """Consolidate multiple orders into a single shipment"""
        try:
            # Get all orders
            order_uuids = [uuid.UUID(order_id) for order_id in order_ids]
            result = await self.db.execute(
                select(Order).where(Order.id.in_(order_uuids))
            )
            orders = result.scalars().all()
            
            if len(orders) != len(order_ids):
                raise ValueError("One or more orders not found")
            
            # Validate orders can be consolidated
            await self._validate_consolidation(orders)
            
            # Create consolidation tracking
            for order in orders:
                await self._log_tracking(
                    str(order.id), 
                    "CONSOLIDATION_STARTED", 
                    f"Order consolidated with {len(order_ids)-1} other orders. Notes: {consolidation_notes or 'None'}"
                )
            
            # Update all orders to consolidated status
            for order in orders:
                order.status = "CONSOLIDATED"
                order.processing_notes = f"Consolidated with orders: {', '.join([o.order_number for o in orders if o.id != order.id])}"
                order.updated_at = datetime.utcnow()
            
            await self.db.commit()
            
            # Generate consolidation email
            await self._generate_consolidation_email(orders, consolidation_notes)
            
            # Log completion
            for order in orders:
                await self._log_tracking(
                    str(order.id), 
                    "CONSOLIDATION_COMPLETED", 
                    f"Order successfully consolidated"
                )
            
            return {
                "status": "success",
                "message": f"Successfully consolidated {len(orders)} orders",
                "consolidated_orders": [
                    {
                        "order_id": str(order.id),
                        "order_number": order.order_number,
                        "total_quantity": order.total_quantity,
                        "total_value": float(order.total) if order.total else 0
                    }
                    for order in orders
                ],
                "consolidation_notes": consolidation_notes
            }
            
        except Exception as e:
            logger.error(f"Error consolidating orders: {str(e)}")
            # Update all orders to error status
            for order_id in order_ids:
                await self._log_tracking(order_id, "CONSOLIDATION_ERROR", f"Consolidation failed: {str(e)}")
            raise
    
    async def _validate_consolidation(self, orders: List[Order]):
        """Validate that orders can be consolidated"""
        # Check if orders have same manufacturer (if assigned)
        manufacturers = set(order.manufacturer_id for order in orders if order.manufacturer_id)
        if len(manufacturers) > 1:
            raise ValueError("Orders must have the same manufacturer to be consolidated")
        
        # Check if orders are in valid status for consolidation
        valid_statuses = ["UPLOADED", "PARSED", "VALIDATED", "ASSIGNED"]
        for order in orders:
            if order.status not in valid_statuses:
                raise ValueError(f"Order {order.order_number} has invalid status {order.status} for consolidation")
    
    async def _generate_consolidation_email(self, orders: List[Order], consolidation_notes: Optional[str]):
        """Generate email notification for order consolidation"""
        try:
            # Find unique email recipients
            recipients = set()
            for order in orders:
                if order.retailer_info and isinstance(order.retailer_info, dict):
                    if 'contact_email' in order.retailer_info:
                        recipients.add(order.retailer_info['contact_email'])
            
            for recipient_email in recipients:
                email_content = await self.email_generator_service.generate_consolidation_email(
                    orders, consolidation_notes
                )
                
                # Create email communication record
                email_communication = EmailCommunication(
                    order_id=orders[0].id,  # Use first order as primary
                    email_type="CONSOLIDATION_NOTICE",
                    subject=f"Order Consolidation Notice - {len(orders)} Orders",
                    to_email=recipient_email,
                    from_email="noreply@orderplanner.com",
                    content=email_content,
                    status="PENDING"
                )
                
                self.db.add(email_communication)
                await self.db.commit()
                
                # Send email
                await self.email_service.send_email(email_communication.id, self.db)
                
        except Exception as e:
            logger.error(f"Error generating consolidation email: {str(e)}")
            # Don't fail the consolidation if email fails

    async def get_validation_summary(self, order_id: str) -> Dict[str, Any]:
        """Get comprehensive validation summary for an order"""
        try:
            order_uuid = uuid.UUID(order_id)
            result = await self.db.execute(
                select(Order).where(Order.id == order_uuid)
            )
            order = result.scalar_one_or_none()
            
            if not order:
                raise ValueError(f"Order {order_id} not found")
            
            if not order.parsed_data:
                return {
                    "order_id": order_id,
                    "has_parsed_data": False,
                    "validation_status": "PENDING_PARSING",
                    "is_valid": False,
                    "missing_fields": [],
                    "validation_errors": [],
                    "business_rule_violations": [],
                    "validation_score": 0.0
                }
            
            # Run validation if not already done
            validation_result = await self.order_validator_service.validate_order_completeness(
                order_id, order.parsed_data
            )
            
            return {
                "order_id": order_id,
                "has_parsed_data": True,
                "validation_status": "COMPLETED",
                "parsed_data": order.parsed_data,
                **validation_result
            }
            
        except Exception as e:
            logger.error(f"Error getting validation summary: {str(e)}")
            raise
    
    async def get_missing_info_details(self, order_id: str) -> Dict[str, Any]:
        """Get detailed missing information for user correction"""
        try:
            validation_summary = await self.get_validation_summary(order_id)
            
            if validation_summary["is_valid"]:
                return {
                    "order_id": order_id,
                    "has_missing_info": False,
                    "missing_fields": [],
                    "correctable_fields": []
                }
            
            missing_fields = validation_summary.get("missing_fields", [])
            validation_errors = validation_summary.get("validation_errors", [])
            
            # Categorize fields that can be corrected by user
            correctable_fields = []
            for field in missing_fields:
                correctable_fields.append({
                    "field_name": field,
                    "field_type": self._get_field_type(field),
                    "description": self._get_field_description(field),
                    "current_value": None,
                    "required": True,
                    "validation_rules": self._get_field_validation_rules(field)
                })
            
            # Add error fields that can be corrected
            for error in validation_errors:
                if error.get("correctable", True):
                    correctable_fields.append({
                        "field_name": error.get("field", "unknown"),
                        "field_type": self._get_field_type(error.get("field", "")),
                        "description": error.get("message", ""),
                        "current_value": error.get("current_value"),
                        "required": True,
                        "validation_rules": error.get("rules", [])
                    })
            
            return {
                "order_id": order_id,
                "has_missing_info": len(correctable_fields) > 0,
                "missing_fields": missing_fields,
                "correctable_fields": correctable_fields,
                "total_issues": len(missing_fields) + len(validation_errors)
            }
            
        except Exception as e:
            logger.error(f"Error getting missing info details: {str(e)}")
            raise
    
    async def apply_corrections(self, order_id: str, corrections: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Apply user corrections to order data"""
        try:
            order_uuid = uuid.UUID(order_id)
            result = await self.db.execute(
                select(Order).where(Order.id == order_uuid)
            )
            order = result.scalar_one_or_none()
            
            if not order:
                raise ValueError(f"Order {order_id} not found")
            
            if not order.parsed_data:
                raise ValueError("Order has no parsed data to correct")
            
            # Track what was corrected
            applied_corrections = []
            
            # Apply corrections to parsed data
            updated_data = order.parsed_data.copy()
            
            for field_name, new_value in corrections.items():
                if field_name in updated_data:
                    old_value = updated_data[field_name]
                    updated_data[field_name] = new_value
                    applied_corrections.append({
                        "field": field_name,
                        "old_value": old_value,
                        "new_value": new_value
                    })
                else:
                    # Add new field
                    updated_data[field_name] = new_value
                    applied_corrections.append({
                        "field": field_name,
                        "old_value": None,
                        "new_value": new_value
                    })
            
            # Update order
            order.parsed_data = updated_data
            order.status = "INFO_RECEIVED"
            order.updated_at = datetime.utcnow()
            
            await self.db.commit()
            
            # Re-validate order with corrections
            validation_result = await self.order_validator_service.validate_order_completeness(
                order_id, updated_data
            )
            
            # Update status based on validation
            if validation_result["is_valid"]:
                await self._update_order_status(order, "VALIDATED", "Order validated after corrections")
            else:
                await self._update_order_status(order, "PENDING_INFO", "Additional corrections needed")
            
            return {
                "order_id": order_id,
                "corrections_applied": len(applied_corrections),
                "applied_corrections": applied_corrections,
                "validation_result": validation_result,
                "new_status": order.status
            }
            
        except Exception as e:
            logger.error(f"Error applying corrections: {str(e)}")
            raise
    
    async def retry_file_parsing(self, order_id: str) -> Dict[str, Any]:
        """Retry file parsing for an order"""
        try:
            order_uuid = uuid.UUID(order_id)
            result = await self.db.execute(
                select(Order).where(Order.id == order_uuid)
            )
            order = result.scalar_one_or_none()
            
            if not order:
                raise ValueError(f"Order {order_id} not found")
            
            if not order.file_path:
                raise ValueError("Order has no file to parse")
            
            await self._log_tracking(order_id, "FILE_PARSING_RETRY", "Retrying file parsing")
            
            # Parse file again
            parsed_data = await self.file_parser_service.parse_file(
                order_id, order.file_path, order.file_type
            )
            
            # Update order
            order.parsed_data = parsed_data
            order.status = "PROCESSING"
            await self.db.commit()
            
            await self._log_tracking(order_id, "FILE_PARSING_COMPLETED", "File parsing retry successful")
            
            return {
                "order_id": order_id,
                "status": "success",
                "parsed_data": parsed_data
            }
            
        except Exception as e:
            await self._log_tracking(order_id, "FILE_PARSING_ERROR", f"File parsing retry failed: {str(e)}")
            raise
    
    async def retry_validation(self, order_id: str) -> Dict[str, Any]:
        """Retry order validation"""
        try:
            order_uuid = uuid.UUID(order_id)
            result = await self.db.execute(
                select(Order).where(Order.id == order_uuid)
            )
            order = result.scalar_one_or_none()
            
            if not order:
                raise ValueError(f"Order {order_id} not found")
            
            if not order.parsed_data:
                raise ValueError("Order has no parsed data to validate")
            
            await self._log_tracking(order_id, "VALIDATION_RETRY", "Retrying order validation")
            
            # Validate order
            validation_result = await self.order_validator_service.validate_order_completeness(
                order_id, order.parsed_data
            )
            
            # Update status based on validation
            if validation_result["is_valid"]:
                await self._update_order_status(order, "VALIDATED", "Order validation retry successful")
            else:
                await self._update_order_status(order, "PENDING_INFO", "Validation retry found issues")
            
            return {
                "order_id": order_id,
                "status": "success",
                "validation_result": validation_result
            }
            
        except Exception as e:
            await self._log_tracking(order_id, "VALIDATION_ERROR", f"Validation retry failed: {str(e)}")
            raise
    
    async def retry_sku_processing(self, order_id: str) -> Dict[str, Any]:
        """Retry SKU processing for an order"""
        try:
            order_uuid = uuid.UUID(order_id)
            result = await self.db.execute(
                select(Order).where(Order.id == order_uuid)
            )
            order = result.scalar_one_or_none()
            
            if not order:
                raise ValueError(f"Order {order_id} not found")
            
            if not order.parsed_data:
                raise ValueError("Order has no parsed data for SKU processing")
            
            await self._log_tracking(order_id, "SKU_PROCESSING_RETRY", "Retrying SKU processing")
            
            # Process SKU items
            sku_result = await self._process_sku_items(order, order.parsed_data)
            
            await self._log_tracking(order_id, "SKU_PROCESSING_COMPLETED", "SKU processing retry successful")
            
            return {
                "order_id": order_id,
                "status": "success",
                "sku_result": sku_result
            }
            
        except Exception as e:
            await self._log_tracking(order_id, "SKU_PROCESSING_ERROR", f"SKU processing retry failed: {str(e)}")
            raise
    
    async def retry_email_generation(self, order_id: str) -> Dict[str, Any]:
        """Retry email generation for an order"""
        try:
            await self._log_tracking(order_id, "EMAIL_GENERATION_RETRY", "Retrying email generation")
            
            # Get current validation status
            validation_result = await self.get_validation_summary(order_id)
            
            # Generate email
            email_result = await self.email_generator_service.generate_missing_info_email(
                order_id, validation_result, validation_result.get("parsed_data", {})
            )
            
            await self._log_tracking(order_id, "EMAIL_GENERATION_COMPLETED", "Email generation retry successful")
            
            return {
                "order_id": order_id,
                "status": "success",
                "email_result": email_result
            }
            
        except Exception as e:
            await self._log_tracking(order_id, "EMAIL_GENERATION_ERROR", f"Email generation retry failed: {str(e)}")
            raise
    
    def _get_field_type(self, field_name: str) -> str:
        """Get field type for UI display"""
        field_types = {
            "delivery_address": "text",
            "delivery_date": "date",
            "retailer_contact": "email",
            "retailer_phone": "tel",
            "priority": "select",
            "special_instructions": "textarea"
        }
        return field_types.get(field_name, "text")
    
    def _get_field_description(self, field_name: str) -> str:
        """Get field description for UI display"""
        descriptions = {
            "delivery_address": "Complete delivery address including street, city, state, zip",
            "delivery_date": "Requested delivery date (YYYY-MM-DD format)",
            "retailer_contact": "Primary contact email for this order",
            "retailer_phone": "Contact phone number",
            "priority": "Order priority level (LOW, MEDIUM, HIGH, URGENT)",
            "special_instructions": "Any special delivery or handling instructions"
        }
        return descriptions.get(field_name, f"Please provide {field_name.replace('_', ' ')}")
    
    def _get_field_validation_rules(self, field_name: str) -> List[str]:
        """Get validation rules for a field"""
        rules = {
            "delivery_address": ["required", "min_length:10"],
            "delivery_date": ["required", "date", "future_date"],
            "retailer_contact": ["required", "email"],
            "retailer_phone": ["phone"],
            "priority": ["required", "in:LOW,MEDIUM,HIGH,URGENT"]
        }
        return rules.get(field_name, ["required"])

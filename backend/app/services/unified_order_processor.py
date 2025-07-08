"""
Unified Order Processor
Consolidates all order processing functionality into a single, reusable service.
"""

import logging
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.base_service import BaseOrderService
from app.services.file_parser_service import FileParserService
from app.services.sku_service import SKUService
from app.services.email_service import EmailService
from app.services.email_generator_service import EmailGeneratorService
from app.models.order import Order
from app.models.tracking import EmailCommunication

logger = logging.getLogger(__name__)


class UnifiedOrderProcessor(BaseOrderService):
    """
    Unified order processor that consolidates all order processing functionality.
    Eliminates code duplication and provides a single interface for order processing.
    """
    
    def __init__(self, db: AsyncSession):
        super().__init__(db)
        self.file_parser = FileParserService(db)
        self.sku_service = SKUService(db)
        self.email_service = EmailService()
        self.email_generator = EmailGeneratorService(db)
        
        # Define required fields once
        self.required_fields = {
            "order_level": [
                "order_number",
                "retailer_info", 
                "delivery_date",
                "priority"
            ],
            "item_level": [
                "sku_code",
                "quantity", 
                "price"
            ],
            "retailer_level": [
                "retailer_name",
                "delivery_address",
                "contact_info"
            ]
        }
    
    # ============== MAIN PROCESSING WORKFLOW ==============
    
    async def process_order_complete(self, order_id: str) -> Dict[str, Any]:
        """Complete order processing workflow - single entry point"""
        try:
            await self.log_tracking(order_id, "UNIFIED_PROCESSING_STARTED", "Starting unified order processing")
            
            # Get order
            order = await self.get_order(order_id)
            if not order:
                return self.create_error_result(f"Order {order_id} not found")
            
            # Step 1: Parse file if needed
            parse_result = await self.process_file_parsing(order_id)
            if not parse_result["success"]:
                return parse_result
            
            # Step 2: Validate data and get missing fields
            validation_result = await self.process_validation(order_id)
            
            # Step 3: Handle missing information with unified email step
            email_result = None
            if not validation_result["is_valid"]:
                email_result = await self.process_email_workflow(order_id, validation_result)
            
            # Step 4: Process SKUs if validation passed
            sku_result = None
            if validation_result["is_valid"]:
                sku_result = await self.process_sku_items(order_id)
            
            # Step 5: Calculate logistics if SKUs processed
            logistics_result = None
            if sku_result and sku_result["success"]:
                logistics_result = await self.process_logistics(order_id)
            
            # Step 6: Update final status
            final_status = self._determine_final_status(validation_result, sku_result, logistics_result)
            await self.update_order_status(order, final_status, "Unified processing completed")
            
            # Compile comprehensive result
            result = self.create_success_result({
                "order_id": order_id,
                "final_status": final_status,
                "parse_result": parse_result,
                "validation_result": validation_result,
                "email_result": email_result,
                "sku_result": sku_result,
                "logistics_result": logistics_result,
                "processing_summary": self._create_processing_summary(
                    validation_result, sku_result, logistics_result
                )
            })
            
            await self.log_tracking(order_id, "UNIFIED_PROCESSING_COMPLETED", 
                                  f"Processing completed with status: {final_status}")
            
            return result
            
        except Exception as e:
            error_msg = f"Unified processing failed: {str(e)}"
            logger.error(error_msg)
            await self.log_tracking(order_id, "UNIFIED_PROCESSING_ERROR", error_msg)
            return self.create_error_result(error_msg)
    
    # ============== INDIVIDUAL PROCESSING STEPS ==============
    
    async def process_file_parsing(self, order_id: str) -> Dict[str, Any]:
        """Process file parsing with comprehensive error handling"""
        try:
            await self.log_tracking(order_id, "FILE_PARSING_STARTED", "Starting file parsing")
            
            order = await self.get_order(order_id)
            if not order:
                return self.create_error_result("Order not found")
            
            if order.parsed_data:
                await self.log_tracking(order_id, "FILE_PARSING_SKIPPED", "File already parsed")
                return self.create_success_result({
                    "already_parsed": True,
                    "parsed_data": order.parsed_data
                })
            
            if not order.file_path:
                return self.create_error_result("No file path available for parsing")
            
            # Parse the file
            parsed_data = await self.file_parser.parse_file(order_id, order.file_path, order.file_type)
            
            # Update order with parsed data
            order.parsed_data = parsed_data
            await self.db.commit()
            
            await self.log_tracking(order_id, "FILE_PARSING_COMPLETED", 
                                  f"File parsed successfully. Found {len(parsed_data.get('order_items', []))} items")
            
            return self.create_success_result({
                "parsed_data": parsed_data,
                "items_count": len(parsed_data.get('order_items', [])),
                "file_type": order.file_type
            })
            
        except Exception as e:
            error_msg = f"File parsing failed: {str(e)}"
            await self.log_tracking(order_id, "FILE_PARSING_ERROR", error_msg)
            return self.create_error_result(error_msg)
    
    async def process_validation(self, order_id: str) -> Dict[str, Any]:
        """Process order validation with unified missing field detection"""
        try:
            await self.log_tracking(order_id, "VALIDATION_STARTED", "Starting order validation")
            
            order = await self.get_order(order_id)
            if not order or not order.parsed_data:
                return self.create_error_result("Order or parsed data not found")
            
            # Extract missing fields
            missing_fields = self.extract_missing_fields(order.parsed_data, self.required_fields)
            
            # Perform data quality checks
            quality_issues = await self._check_data_quality(order.parsed_data)
            
            # Perform business rule validation
            business_violations = await self._check_business_rules(order.parsed_data)
            
            # Calculate validation score
            validation_score = self.calculate_data_quality_score(order.parsed_data)
            
            # Determine if valid
            is_valid = (
                len(missing_fields) == 0 and
                len(quality_issues) == 0 and
                len(business_violations) == 0 and
                validation_score >= 0.8
            )
            
            validation_result = {
                "is_valid": is_valid,
                "missing_fields": missing_fields,
                "quality_issues": quality_issues,
                "business_violations": business_violations,
                "validation_score": validation_score,
                "field_metadata": {field: self.get_field_metadata(field) for field in missing_fields}
            }
            
            status = "VALIDATION_COMPLETED" if is_valid else "VALIDATION_FAILED"
            message = f"Validation {'passed' if is_valid else 'failed'}. Score: {validation_score:.2f}"
            
            await self.log_tracking(order_id, status, message, validation_result)
            
            return self.create_success_result(validation_result)
            
        except Exception as e:
            error_msg = f"Validation failed: {str(e)}"
            await self.log_tracking(order_id, "VALIDATION_ERROR", error_msg)
            return self.create_error_result(error_msg)
    
    async def process_email_workflow(self, order_id: str, validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """Unified email processing - generate AND send in one step"""
        try:
            await self.log_tracking(order_id, "EMAIL_WORKFLOW_STARTED", "Starting unified email workflow")
            
            order = await self.get_order(order_id)
            if not order:
                return self.create_error_result("Order not found")
            
            # Get recipient email
            recipient_email = self._extract_recipient_email(order)
            if not recipient_email:
                return self.create_error_result("No recipient email available")
            
            # Generate email content
            email_content = await self._generate_unified_email_content(order_id, validation_result, order.parsed_data)
            
            # Create email communication record
            email_comm = EmailCommunication(
                order_id=order.id,
                email_type="MISSING_INFO_REQUEST",
                recipient=recipient_email,
                sender="noreply@orderplanner.com",
                subject=email_content["subject"],
                html_content=email_content["html_content"],
                text_content=email_content["text_content"],
                status="PENDING"
            )
            
            self.db.add(email_comm)
            await self.db.commit()
            
            # Send email immediately
            send_success = await self.email_service.send_email(
                to_email=recipient_email,
                subject=email_content["subject"],
                html_content=email_content["html_content"],
                text_content=email_content["text_content"]
            )
            
            if send_success:
                email_comm.status = "SENT"
                email_comm.sent_at = datetime.utcnow()
                await self.db.commit()
                
                await self.log_tracking(order_id, "EMAIL_SENT_SUCCESS", 
                                      f"Email sent successfully to {recipient_email}")
                
                return self.create_success_result({
                    "email_sent": True,
                    "recipient": recipient_email,
                    "email_id": str(email_comm.id),
                    "missing_fields_count": len(validation_result.get("missing_fields", [])),
                    "subject": email_content["subject"]
                })
            else:
                email_comm.status = "FAILED"
                await self.db.commit()
                
                await self.log_tracking(order_id, "EMAIL_SEND_FAILED", 
                                      f"Failed to send email to {recipient_email}")
                
                return self.create_error_result("Email generation succeeded but sending failed", {
                    "email_id": str(email_comm.id),
                    "recipient": recipient_email
                })
            
        except Exception as e:
            error_msg = f"Email workflow failed: {str(e)}"
            await self.log_tracking(order_id, "EMAIL_WORKFLOW_ERROR", error_msg)
            return self.create_error_result(error_msg)
    
    async def process_sku_items(self, order_id: str) -> Dict[str, Any]:
        """Process SKU items with validation and totals calculation"""
        try:
            await self.log_tracking(order_id, "SKU_PROCESSING_STARTED", "Starting SKU processing")
            
            order = await self.get_order(order_id)
            if not order or not order.parsed_data:
                return self.create_error_result("Order or parsed data not found")
            
            items = order.parsed_data.get("order_items", [])
            if not items:
                return self.create_error_result("No items found in parsed data")
            
            # Process items
            processed_items = []
            total_quantity = 0
            total_weight = 0.0
            total_volume = 0.0
            total_value = 0.0
            
            for i, item in enumerate(items):
                try:
                    quantity = float(item.get("quantity", 0))
                    price = float(item.get("price", 0))
                    weight = float(item.get("weight_kg", 1.0))  # Default 1kg
                    volume = float(item.get("volume_m3", 0.001))  # Default 1L
                    
                    item_total = quantity * price
                    
                    total_quantity += quantity
                    total_weight += weight * quantity
                    total_volume += volume * quantity
                    total_value += item_total
                    
                    processed_items.append({
                        "sku_code": item.get("sku_code"),
                        "product_name": item.get("product_name", "Unknown Product"),
                        "quantity": quantity,
                        "price": price,
                        "weight_kg": weight,
                        "volume_m3": volume,
                        "line_total": item_total,
                        "processed": True
                    })
                    
                except (ValueError, TypeError) as e:
                    logger.warning(f"Error processing item {i}: {str(e)}")
                    continue
            
            # Update order totals
            order.total_sku_count = len(processed_items)
            order.total_quantity = int(total_quantity)
            order.total_weight_kg = total_weight
            order.total_volume_m3 = total_volume
            order.subtotal = total_value
            await self.db.commit()
            
            await self.log_tracking(order_id, "SKU_PROCESSING_COMPLETED", 
                                  f"Processed {len(processed_items)} SKU items")
            
            return self.create_success_result({
                "processed_items": processed_items,
                "totals": {
                    "sku_count": len(processed_items),
                    "total_quantity": total_quantity,
                    "total_weight_kg": total_weight,
                    "total_volume_m3": total_volume,
                    "total_value": total_value
                }
            })
            
        except Exception as e:
            error_msg = f"SKU processing failed: {str(e)}"
            await self.log_tracking(order_id, "SKU_PROCESSING_ERROR", error_msg)
            return self.create_error_result(error_msg)
    
    async def process_logistics(self, order_id: str, shipping_method: str = "STANDARD") -> Dict[str, Any]:
        """Process logistics calculations"""
        try:
            await self.log_tracking(order_id, "LOGISTICS_CALCULATION_STARTED", "Starting logistics calculation")
            
            order = await self.get_order(order_id)
            if not order:
                return self.create_error_result("Order not found")
            
            # Calculate shipping costs
            base_cost = 50.0
            weight_factor = float(order.total_weight_kg or 0) * 2.0
            volume_factor = float(order.total_volume_m3 or 0) * 100.0
            
            shipping_cost = base_cost + weight_factor + volume_factor
            
            # Apply shipping method multipliers
            if shipping_method == "EXPRESS":
                shipping_cost *= 1.5
                estimated_days = 1
            elif shipping_method == "ECONOMY":
                shipping_cost *= 0.8
                estimated_days = 7
            else:  # STANDARD
                estimated_days = 3
            
            # Calculate tax and total
            tax_rate = 0.1
            tax_amount = shipping_cost * tax_rate
            total_cost = (order.subtotal or 0) + shipping_cost + tax_amount
            
            # Update order
            order.tax = tax_amount
            order.total = total_cost
            await self.db.commit()
            
            logistics_data = {
                "shipping_cost": round(shipping_cost, 2),
                "tax": round(tax_amount, 2),
                "total_cost": round(total_cost, 2),
                "shipping_method": shipping_method,
                "estimated_delivery_days": estimated_days,
                "weight_kg": float(order.total_weight_kg or 0),
                "volume_m3": float(order.total_volume_m3 or 0)
            }
            
            await self.log_tracking(order_id, "LOGISTICS_CALCULATION_COMPLETED", 
                                  f"Logistics calculated. Total: ${total_cost:.2f}")
            
            return self.create_success_result(logistics_data)
            
        except Exception as e:
            error_msg = f"Logistics calculation failed: {str(e)}"
            await self.log_tracking(order_id, "LOGISTICS_CALCULATION_ERROR", error_msg)
            return self.create_error_result(error_msg)
    
    # ============== INDIVIDUAL OPERATIONS ==============
    
    async def apply_corrections(self, order_id: str, corrections: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Apply user corrections to order data"""
        try:
            await self.log_tracking(order_id, "CORRECTIONS_STARTED", f"Applying corrections from user {user_id}")
            
            order = await self.get_order(order_id)
            if not order or not order.parsed_data:
                return self.create_error_result("Order or parsed data not found")
            
            # Apply corrections
            updated_data = order.parsed_data.copy()
            applied_corrections = []
            
            for field_name, new_value in corrections.items():
                old_value = updated_data.get(field_name)
                updated_data[field_name] = new_value
                applied_corrections.append({
                    "field": field_name,
                    "old_value": old_value,
                    "new_value": new_value
                })
            
            # Update order
            order.parsed_data = updated_data
            order.status = "INFO_RECEIVED"
            await self.db.commit()
            
            # Re-validate
            validation_result = await self.process_validation(order_id)
            
            await self.log_tracking(order_id, "CORRECTIONS_APPLIED", 
                                  f"Applied {len(applied_corrections)} corrections")
            
            return self.create_success_result({
                "corrections_applied": len(applied_corrections),
                "applied_corrections": applied_corrections,
                "validation_result": validation_result,
                "order_status": order.status
            })
            
        except Exception as e:
            error_msg = f"Corrections failed: {str(e)}"
            await self.log_tracking(order_id, "CORRECTIONS_ERROR", error_msg)
            return self.create_error_result(error_msg)
    
    async def get_order_summary(self, order_id: str) -> Dict[str, Any]:
        """Get comprehensive order summary"""
        try:
            order = await self.get_order(order_id)
            if not order:
                return self.create_error_result("Order not found")
            
            summary = {
                "order_id": order_id,
                "order_number": order.order_number,
                "status": order.status,
                "customer_info": {
                    "name": order.customer_name,
                    "contact": order.customer_contact,
                    "address": order.delivery_address
                },
                "retailer_info": order.retailer_info or {},
                "file_info": {
                    "file_path": order.file_path,
                    "file_type": order.file_type,
                    "uploaded_at": order.created_at.isoformat() if order.created_at else None
                },
                "processing_info": {
                    "parsed_data_available": bool(order.parsed_data),
                    "validation_status": order.validation_status,
                    "processing_notes": order.processing_notes,
                    "priority": self.get_processing_priority(order)
                },
                "totals": {
                    "sku_count": order.total_sku_count or 0,
                    "quantity": order.total_quantity or 0,
                    "weight_kg": float(order.total_weight_kg or 0),
                    "volume_m3": float(order.total_volume_m3 or 0),
                    "subtotal": float(order.subtotal or 0),
                    "tax": float(order.tax or 0),
                    "total": float(order.total or 0)
                },
                "timeline": {
                    "created_at": order.created_at.isoformat() if order.created_at else None,
                    "updated_at": order.updated_at.isoformat() if order.updated_at else None,
                    "delivery_date": order.delivery_date.isoformat() if order.delivery_date else None
                }
            }
            
            return self.create_success_result(summary)
            
        except Exception as e:
            return self.create_error_result(f"Failed to get order summary: {str(e)}")
    
    # ============== RETRY OPERATIONS ==============
    
    async def retry_processing_step(self, order_id: str, step_name: str) -> Dict[str, Any]:
        """Retry a specific processing step"""
        try:
            await self.log_tracking(order_id, f"RETRY_{step_name.upper()}_STARTED", 
                                  f"Retrying {step_name} step")
            
            step_mapping = {
                "parse": self.process_file_parsing,
                "validate": self.process_validation,
                "sku_processing": self.process_sku_items,
                "logistics": self.process_logistics
            }
            
            if step_name not in step_mapping:
                return self.create_error_result(f"Unknown step: {step_name}")
            
            # Execute step with retry mechanism
            step_func = step_mapping[step_name]
            result = await self.retry_with_backoff(lambda: step_func(order_id))
            
            if result["success"]:
                await self.log_tracking(order_id, f"RETRY_{step_name.upper()}_SUCCESS", 
                                      f"Retry of {step_name} successful")
            
            return result
            
        except Exception as e:
            error_msg = f"Retry of {step_name} failed: {str(e)}"
            await self.log_tracking(order_id, f"RETRY_{step_name.upper()}_FAILED", error_msg)
            return self.create_error_result(error_msg)
    
    # ============== HELPER METHODS ==============
    
    async def _check_data_quality(self, data: Dict[str, Any]) -> List[str]:
        """Check data quality issues"""
        issues = []
        
        # Check for duplicates
        items = data.get("order_items", [])
        sku_codes = [item.get("sku_code") for item in items if item.get("sku_code")]
        duplicates = [sku for sku in set(sku_codes) if sku_codes.count(sku) > 1]
        
        if duplicates:
            issues.append(f"Duplicate SKU codes found: {', '.join(duplicates)}")
        
        # Check for inconsistent data
        for i, item in enumerate(items):
            if item.get("quantity") and not self.is_valid_quantity(item["quantity"]):
                issues.append(f"Invalid quantity in item {i+1}: {item.get('quantity')}")
            
            if item.get("price") and not self.is_valid_price(item["price"]):
                issues.append(f"Invalid price in item {i+1}: {item.get('price')}")
        
        return issues
    
    async def _check_business_rules(self, data: Dict[str, Any]) -> List[str]:
        """Check business rule violations"""
        violations = []
        
        items = data.get("order_items", [])
        
        # Check minimum order value
        total_value = sum(
            float(item.get("price", 0)) * float(item.get("quantity", 0))
            for item in items
            if self.is_valid_price(item.get("price")) and self.is_valid_quantity(item.get("quantity"))
        )
        
        if total_value < 100:
            violations.append(f"Order value ${total_value:.2f} below minimum $100")
        elif total_value > 100000:
            violations.append(f"Order value ${total_value:.2f} exceeds maximum $100,000")
        
        # Check minimum quantities
        for i, item in enumerate(items):
            quantity = float(item.get("quantity", 0))
            if 0 < quantity < 1:
                violations.append(f"Item {i+1} quantity {quantity} below minimum of 1")
        
        return violations
    
    def _extract_recipient_email(self, order: Order) -> Optional[str]:
        """Extract recipient email from order"""
        if order.retailer_info:
            email = order.retailer_info.get("email") or order.retailer_info.get("contact_email")
            if email and self.is_valid_email(email):
                return email
        
        if order.customer_contact and self.is_valid_email(order.customer_contact):
            return order.customer_contact
        
        return None
    
    async def _generate_unified_email_content(self, order_id: str, validation_result: Dict[str, Any], 
                                            parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate unified email content for missing information"""
        missing_fields = validation_result.get("missing_fields", [])
        quality_issues = validation_result.get("quality_issues", [])
        business_violations = validation_result.get("business_violations", [])
        
        subject = f"Order {order_id[:8]} - Additional Information Required"
        
        # Generate text content
        text_content = f"""
Dear Customer,

We have received your order {order_id[:8]} and need additional information to process it.

Missing Information:
{chr(10).join(f"• {field.replace('_', ' ').title()}" for field in missing_fields)}

"""
        
        if quality_issues:
            text_content += f"""
Data Quality Issues:
{chr(10).join(f"• {issue}" for issue in quality_issues)}

"""
        
        if business_violations:
            text_content += f"""
Business Rule Issues:
{chr(10).join(f"• {violation}" for violation in business_violations)}

"""
        
        text_content += """
Please provide the missing information so we can process your order promptly.

Best regards,
Order Processing Team
"""
        
        # Generate HTML content
        html_content = f"""
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f8f9fa; padding: 20px; border-radius: 5px; }}
        .content {{ margin: 20px 0; }}
        .issue-list {{ background-color: #fff3cd; padding: 15px; border-radius: 5px; margin: 10px 0; }}
        .footer {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="header">
        <h2>Order Information Required</h2>
        <p>Order ID: {order_id[:8]}</p>
    </div>
    
    <div class="content">
        <p>We have received your order and need additional information to process it.</p>
        
        <div class="issue-list">
            <h3>Missing Information:</h3>
            <ul>
                {"".join(f"<li>{field.replace('_', ' ').title()}</li>" for field in missing_fields)}
            </ul>
        </div>
"""
        
        if quality_issues:
            html_content += f"""
        <div class="issue-list">
            <h3>Data Quality Issues:</h3>
            <ul>
                {"".join(f"<li>{issue}</li>" for issue in quality_issues)}
            </ul>
        </div>
"""
        
        if business_violations:
            html_content += f"""
        <div class="issue-list">
            <h3>Business Rule Issues:</h3>
            <ul>
                {"".join(f"<li>{violation}</li>" for violation in business_violations)}
            </ul>
        </div>
"""
        
        html_content += """
    </div>
    
    <div class="footer">
        <p>Please provide the missing information so we can process your order promptly.</p>
        <p>Best regards,<br>Order Processing Team</p>
    </div>
</body>
</html>
"""
        
        return {
            "subject": subject,
            "text_content": text_content,
            "html_content": html_content
        }
    
    def _determine_final_status(self, validation_result: Dict[str, Any], 
                              sku_result: Optional[Dict[str, Any]], 
                              logistics_result: Optional[Dict[str, Any]]) -> str:
        """Determine final order status"""
        if not validation_result["is_valid"]:
            if validation_result.get("missing_fields"):
                return "MISSING_INFO"
            elif validation_result.get("quality_issues"):
                return "DATA_QUALITY_ISSUES"
            elif validation_result.get("business_violations"):
                return "BUSINESS_RULE_VIOLATIONS"
            else:
                return "VALIDATION_FAILED"
        
        if sku_result and not sku_result["success"]:
            return "SKU_PROCESSING_FAILED"
        
        if logistics_result and not logistics_result["success"]:
            return "LOGISTICS_CALCULATION_FAILED"
        
        if validation_result["is_valid"] and sku_result and logistics_result:
            return "PROCESSED"
        
        return "VALIDATED"
    
    def _create_processing_summary(self, validation_result: Dict[str, Any], 
                                 sku_result: Optional[Dict[str, Any]], 
                                 logistics_result: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Create processing summary"""
        return {
            "validation_score": validation_result.get("validation_score", 0.0),
            "missing_fields_count": len(validation_result.get("missing_fields", [])),
            "quality_issues_count": len(validation_result.get("quality_issues", [])),
            "business_violations_count": len(validation_result.get("business_violations", [])),
            "sku_items_processed": sku_result.get("totals", {}).get("sku_count", 0) if sku_result else 0,
            "logistics_calculated": bool(logistics_result and logistics_result["success"]),
            "total_value": logistics_result.get("total_cost", 0.0) if logistics_result else 0.0
        }

from typing import Dict, List, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.order import Order
from app.models.tracking import OrderTracking, EmailCommunication
from app.models.user import User
from jinja2 import Environment, FileSystemLoader, Template
import logging
import uuid
from datetime import datetime
import os
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

logger = logging.getLogger(__name__)

class EmailGeneratorService:
    """Enhanced service for generating draft emails for missing information"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        
        # Initialize Jinja2 environment for email templates
        template_dir = os.path.join(os.path.dirname(__file__), '..', 'templates', 'emails')
        self.jinja_env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=True
        )
        
        # Email templates
        self.templates = {
            'missing_info': self._get_missing_info_template(),
            'validation_failed': self._get_validation_failed_template(),
            'order_incomplete': self._get_order_incomplete_template(),
            'catalog_mismatch': self._get_catalog_mismatch_template(),
            'data_quality_issues': self._get_data_quality_template()
        }
    
    async def generate_missing_info_email(
        self, 
        order_id: str, 
        validation_result: Dict[str, Any],
        order_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate draft email for missing information"""
        try:
            # Log email generation start
            await self._log_tracking(order_id, "EMAIL_GENERATION_STARTED", 
                                   "Starting email generation for missing information")
            
            # Get order details
            order = await self._get_order_details(order_id)
            if not order:
                raise ValueError(f"Order {order_id} not found")
            
            # Determine email type based on validation result
            email_type = self._determine_email_type(validation_result)
            
            # Generate email content
            email_content = await self._generate_email_content(
                email_type, order, validation_result, order_data
            )
            
            # Create email record
            email_record = await self._create_email_record(
                order_id, email_type, email_content
            )
            
            # Log email generation completion
            await self._log_tracking(order_id, "EMAIL_GENERATION_COMPLETED", 
                                   f"Generated {email_type} email with ID: {email_record['id']}")
            
            return {
                "email_id": email_record["id"],
                "email_type": email_type,
                "content": email_content,
                "generated_at": datetime.utcnow().isoformat(),
                "order_id": order_id
            }
            
        except Exception as e:
            error_msg = f"Email generation error: {str(e)}"
            logger.error(error_msg)
            await self._log_tracking(order_id, "EMAIL_GENERATION_ERROR", error_msg)
            raise
    
    async def generate_html_email(
        self, 
        template_name: str, 
        context: Dict[str, Any]
    ) -> str:
        """Generate HTML email content from template"""
        try:
            if template_name in self.templates:
                template = self.templates[template_name]
            else:
                # Try to load from file system
                template = self.jinja_env.get_template(f"{template_name}.html")
            
            return template.render(**context)
            
        except Exception as e:
            logger.error(f"Error generating HTML email: {str(e)}")
            return self._get_fallback_email_content(context)
    
    async def prepare_email_with_attachments(
        self, 
        email_content: Dict[str, Any],
        attachments: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Prepare email with attachments for reference documents"""
        try:
            msg = MIMEMultipart()
            msg['Subject'] = email_content['subject']
            msg['From'] = email_content['from']
            msg['To'] = email_content['to']
            
            # Add HTML body
            html_body = MIMEText(email_content['html_body'], 'html')
            msg.attach(html_body)
            
            # Add text body as fallback
            if 'text_body' in email_content:
                text_body = MIMEText(email_content['text_body'], 'plain')
                msg.attach(text_body)
            
            # Add attachments
            if attachments:
                for attachment in attachments:
                    await self._add_attachment(msg, attachment)
            
            return {
                "message": msg,
                "raw_content": msg.as_string(),
                "attachment_count": len(attachments) if attachments else 0
            }
            
        except Exception as e:
            logger.error(f"Error preparing email with attachments: {str(e)}")
            raise
    
    def _determine_email_type(self, validation_result: Dict[str, Any]) -> str:
        """Determine appropriate email type based on validation result"""
        if validation_result.get("missing_fields"):
            return "missing_info"
        elif validation_result.get("business_rule_violations"):
            return "validation_failed"
        elif validation_result.get("catalog_validation", {}).get("invalid_products"):
            return "catalog_mismatch"
        elif validation_result.get("data_quality_issues"):
            return "data_quality_issues"
        else:
            return "order_incomplete"
    
    async def _generate_email_content(
        self, 
        email_type: str, 
        order: Dict[str, Any], 
        validation_result: Dict[str, Any],
        order_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate email content based on type"""
        
        context = {
            "order": order,
            "validation_result": validation_result,
            "order_data": order_data,
            "generated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "support_email": "support@orderplanner.com",
            "company_name": "Order Planner System"
        }
        
        # Generate HTML content
        html_content = await self.generate_html_email(email_type, context)
        
        # Generate subject based on email type
        subject = self._generate_subject(email_type, order, validation_result)
        
        # Generate text content as fallback
        text_content = self._generate_text_content(email_type, context)
        
        # Determine recipient: prefer retailer's contact_email, then user's email, then fallback
        recipient_email = None
        # Try retailer_info dict
        if order.get("retailer_info") and isinstance(order["retailer_info"], dict):
            recipient_email = order["retailer_info"].get("contact_email")
        # Try direct contact_email (should not exist, but for safety)
        if not recipient_email:
            recipient_email = order.get("contact_email")
        # Try user email
        if not recipient_email and order.get("user") and isinstance(order["user"], dict):
            recipient_email = order["user"].get("email")
        # Fallback
        if not recipient_email:
            recipient_email = "customer@example.com"

        return {
            "subject": subject,
            "html_body": html_content,
            "text_body": text_content,
            "recipient": recipient_email,
            "sender": "noreply@orderplanner.com",
            "email_type": email_type,
            "priority": self._get_email_priority(validation_result)
        }
    
    def _generate_subject(self, email_type: str, order: Dict[str, Any], validation_result: Dict[str, Any]) -> str:
        """Generate email subject based on type"""
        order_number = order.get("order_number", "Unknown")
        
        subjects = {
            "missing_info": f"Missing Information Required for Order {order_number}",
            "validation_failed": f"Order Validation Issues - Order {order_number}",
            "order_incomplete": f"Incomplete Order Data - Order {order_number}",
            "catalog_mismatch": f"Product Catalog Mismatch - Order {order_number}",
            "data_quality_issues": f"Data Quality Issues - Order {order_number}"
        }
        
        return subjects.get(email_type, f"Order Processing Issue - Order {order_number}")
    
    def _generate_text_content(self, email_type: str, context: Dict[str, Any]) -> str:
        """Generate plain text email content"""
        order = context["order"]
        validation_result = context["validation_result"]
        
        text_content = f"""
Dear Customer,

We are writing regarding your order {order.get('order_number', 'Unknown')}.

"""
        
        if email_type == "missing_info":
            missing_fields = validation_result.get("missing_fields", [])
            text_content += f"""
We have identified the following missing information that is required to process your order:

"""
            for field in missing_fields:
                text_content += f"• {field}\n"
            
            text_content += f"""
Please provide the missing information at your earliest convenience to avoid delays in processing your order.
"""
        
        elif email_type == "validation_failed":
            violations = validation_result.get("business_rule_violations", [])
            text_content += f"""
We have identified the following validation issues with your order:

"""
            for violation in violations:
                text_content += f"• {violation}\n"
        
        elif email_type == "catalog_mismatch":
            invalid_products = validation_result.get("catalog_validation", {}).get("invalid_products", [])
            text_content += f"""
We have identified the following products that do not match our catalog:

"""
            for product in invalid_products:
                text_content += f"• SKU: {product.get('sku_code', 'Unknown')}\n"
        
        text_content += f"""

If you have any questions, please contact our support team at {context['support_email']}.

Best regards,
{context['company_name']} Team

---
This is an automated message. Please do not reply to this email.
Generated on: {context['generated_at']}
"""
        
        return text_content
    
    def _get_email_priority(self, validation_result: Dict[str, Any]) -> str:
        """Determine email priority based on validation result"""
        if validation_result.get("validation_score", 1.0) < 0.3:
            return "high"
        elif validation_result.get("validation_score", 1.0) < 0.7:
            return "medium"
        else:
            return "low"
    
    async def _add_attachment(self, msg: MIMEMultipart, attachment: Dict[str, Any]):
        """Add attachment to email message"""
        try:
            file_path = attachment.get("file_path")
            filename = attachment.get("filename", os.path.basename(file_path))
            
            with open(file_path, "rb") as attachment_file:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment_file.read())
            
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {filename}'
            )
            
            msg.attach(part)
            
        except Exception as e:
            logger.error(f"Error adding attachment: {str(e)}")
    
    async def _get_order_details(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Get order details from database"""
        try:
            result = await self.db.execute(
                select(Order).where(Order.id == uuid.UUID(order_id))
            )
            order = result.scalar_one_or_none()
            
            if order:
                return {
                    "id": str(order.id),
                    "order_number": order.order_number,
                    "retailer_id": order.retailer_id,
                    "status": order.status,
                    "contact_email": getattr(order, 'contact_email', None),
                    "created_at": order.created_at.isoformat() if order.created_at else None
                }
            return None
            
        except Exception as e:
            logger.error(f"Error getting order details: {str(e)}")
            return None
    
    async def _create_email_record(
        self, 
        order_id: str, 
        email_type: str, 
        email_content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create email communication record"""
        try:
            email_record = EmailCommunication(
                order_id=uuid.UUID(order_id),
                email_type=email_type,
                recipient=email_content["recipient"],
                sender=email_content["sender"],
                subject=email_content["subject"],
                body=email_content["html_body"]
            )
            
            self.db.add(email_record)
            await self.db.commit()
            
            return {
                "id": str(email_record.id),
                "created_at": email_record.created_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error creating email record: {str(e)}")
            raise
    
    def _get_fallback_email_content(self, context: Dict[str, Any]) -> str:
        """Get fallback email content when template fails"""
        return f"""
        <html>
        <body>
            <h2>Order Processing Issue</h2>
            <p>Dear Customer,</p>
            <p>We have identified issues with your order that require attention.</p>
            <p>Please contact our support team for assistance.</p>
            <p>Best regards,<br>Order Planner Team</p>
        </body>
        </html>
        """
    
    def _get_missing_info_template(self) -> Template:
        """Get missing information email template"""
        template_str = """
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
                .header { background-color: #f8f9fa; padding: 20px; border-radius: 5px; }
                .content { padding: 20px 0; }
                .missing-fields { background-color: #fff3cd; padding: 15px; border-radius: 5px; margin: 10px 0; }
                .footer { background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 20px; }
                .urgent { color: #dc3545; font-weight: bold; }
            </style>
        </head>
        <body>
            <div class="header">
                <h2>Missing Information Required</h2>
                <p>Order Number: <strong>{{ order.order_number }}</strong></p>
                <p>Date: {{ generated_at }}</p>
            </div>
            
            <div class="content">
                <p>Dear Customer,</p>
                
                <p>We are processing your order but have identified missing information that is required to complete the process.</p>
                
                <div class="missing-fields">
                    <h3>Missing Information:</h3>
                    <ul>
                    {% for field in validation_result.missing_fields %}
                        <li>{{ field }}</li>
                    {% endfor %}
                    </ul>
                </div>
                
                {% if validation_result.validation_score < 0.5 %}
                <p class="urgent">This order requires immediate attention due to multiple missing fields.</p>
                {% endif %}
                
                <p>Please provide the missing information at your earliest convenience to avoid delays in processing your order.</p>
                
                <p>You can reply to this email or contact our support team at {{ support_email }}.</p>
            </div>
            
            <div class="footer">
                <p>Best regards,<br>{{ company_name }} Team</p>
                <p><small>This is an automated message. Order ID: {{ order.id }}</small></p>
            </div>
        </body>
        </html>
        """
        return Template(template_str)
    
    def _get_validation_failed_template(self) -> Template:
        """Get validation failed email template"""
        template_str = """
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
                .header { background-color: #f8f9fa; padding: 20px; border-radius: 5px; }
                .content { padding: 20px 0; }
                .violations { background-color: #f8d7da; padding: 15px; border-radius: 5px; margin: 10px 0; }
                .footer { background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 20px; }
            </style>
        </head>
        <body>
            <div class="header">
                <h2>Order Validation Issues</h2>
                <p>Order Number: <strong>{{ order.order_number }}</strong></p>
                <p>Date: {{ generated_at }}</p>
            </div>
            
            <div class="content">
                <p>Dear Customer,</p>
                
                <p>We have identified validation issues with your order that need to be resolved.</p>
                
                <div class="violations">
                    <h3>Validation Issues:</h3>
                    <ul>
                    {% for violation in validation_result.business_rule_violations %}
                        <li>{{ violation }}</li>
                    {% endfor %}
                    </ul>
                </div>
                
                <p>Please review and correct these issues, then resubmit your order.</p>
                
                <p>If you need assistance, please contact our support team at {{ support_email }}.</p>
            </div>
            
            <div class="footer">
                <p>Best regards,<br>{{ company_name }} Team</p>
                <p><small>This is an automated message. Order ID: {{ order.id }}</small></p>
            </div>
        </body>
        </html>
        """
        return Template(template_str)
    
    def _get_order_incomplete_template(self) -> Template:
        """Get order incomplete email template"""
        template_str = """
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
                .header { background-color: #f8f9fa; padding: 20px; border-radius: 5px; }
                .content { padding: 20px 0; }
                .info { background-color: #d1ecf1; padding: 15px; border-radius: 5px; margin: 10px 0; }
                .footer { background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 20px; }
            </style>
        </head>
        <body>
            <div class="header">
                <h2>Incomplete Order Data</h2>
                <p>Order Number: <strong>{{ order.order_number }}</strong></p>
                <p>Date: {{ generated_at }}</p>
            </div>
            
            <div class="content">
                <p>Dear Customer,</p>
                
                <p>Your order has been received but contains incomplete data that prevents processing.</p>
                
                <div class="info">
                    <h3>Order Status:</h3>
                    <p>Validation Score: {{ "%.1f"|format(validation_result.validation_score * 100) }}%</p>
                    <p>Issues Found: {{ validation_result.validation_errors|length }}</p>
                </div>
                
                <p>Please review your order and provide the missing information to complete processing.</p>
                
                <p>Contact our support team at {{ support_email }} for assistance.</p>
            </div>
            
            <div class="footer">
                <p>Best regards,<br>{{ company_name }} Team</p>
                <p><small>This is an automated message. Order ID: {{ order.id }}</small></p>
            </div>
        </body>
        </html>
        """
        return Template(template_str)
    
    def _get_catalog_mismatch_template(self) -> Template:
        """Get catalog mismatch email template"""
        template_str = """
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
                .header { background-color: #f8f9fa; padding: 20px; border-radius: 5px; }
                .content { padding: 20px 0; }
                .products { background-color: #fff3cd; padding: 15px; border-radius: 5px; margin: 10px 0; }
                .footer { background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 20px; }
            </style>
        </head>
        <body>
            <div class="header">
                <h2>Product Catalog Mismatch</h2>
                <p>Order Number: <strong>{{ order.order_number }}</strong></p>
                <p>Date: {{ generated_at }}</p>
            </div>
            
            <div class="content">
                <p>Dear Customer,</p>
                
                <p>We have identified products in your order that do not match our current catalog.</p>
                
                <div class="products">
                    <h3>Unknown Products:</h3>
                    <ul>
                    {% for product in validation_result.catalog_validation.invalid_products %}
                        <li>SKU: {{ product.sku_code }}</li>
                    {% endfor %}
                    </ul>
                </div>
                
                <p>Please verify the product codes and resubmit your order with correct SKU codes.</p>
                
                <p>Contact our support team at {{ support_email }} for assistance with product codes.</p>
            </div>
            
            <div class="footer">
                <p>Best regards,<br>{{ company_name }} Team</p>
                <p><small>This is an automated message. Order ID: {{ order.id }}</small></p>
            </div>
        </body>
        </html>
        """
        return Template(template_str)
    
    def _get_data_quality_template(self) -> Template:
        """Get data quality issues email template"""
        template_str = """
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
                .header { background-color: #f8f9fa; padding: 20px; border-radius: 5px; }
                .content { padding: 20px 0; }
                .issues { background-color: #f8d7da; padding: 15px; border-radius: 5px; margin: 10px 0; }
                .footer { background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 20px; }
            </style>
        </head>
        <body>
            <div class="header">
                <h2>Data Quality Issues</h2>
                <p>Order Number: <strong>{{ order.order_number }}</strong></p>
                <p>Date: {{ generated_at }}</p>
            </div>
            
            <div class="content">
                <p>Dear Customer,</p>
                
                <p>We have identified data quality issues in your order that need to be resolved.</p>
                
                <div class="issues">
                    <h3>Data Quality Issues:</h3>
                    <ul>
                    {% for issue in validation_result.data_quality_issues %}
                        <li>{{ issue }}</li>
                    {% endfor %}
                    </ul>
                </div>
                
                <p>Please review and correct these issues, then resubmit your order.</p>
                
                <p>Contact our support team at {{ support_email }} for assistance.</p>
            </div>
            
            <div class="footer">
                <p>Best regards,<br>{{ company_name }} Team</p>
                <p><small>This is an automated message. Order ID: {{ order.id }}</small></p>
            </div>
        </body>
        </html>
        """
        return Template(template_str)
    
    async def _log_tracking(self, order_id: str, status: str, message: str, details: Optional[str] = None):
        """Log tracking information"""
        try:
            tracking_entry = OrderTracking(
                order_id=uuid.UUID(order_id),
                status=status,
                message=message,
                details=details
            )
            self.db.add(tracking_entry)
            await self.db.commit()
        except Exception as e:
            logger.error(f"Error logging tracking: {str(e)}")
    
    async def get_email_templates(self) -> List[Dict[str, Any]]:
        """Get available email templates for UI"""
        try:
            templates = [
                {
                    'id': 'missing_info',
                    'name': 'Missing Information',
                    'description': 'Email template for requesting missing order information',
                    'category': 'data_collection',
                    'fields': ['missing_fields', 'order_details', 'customer_info']
                },
                {
                    'id': 'validation_failed',
                    'name': 'Validation Failed',
                    'description': 'Email template for validation failures',
                    'category': 'validation',
                    'fields': ['validation_errors', 'order_details', 'correction_instructions']
                },
                {
                    'id': 'catalog_mismatch',
                    'name': 'Catalog Mismatch',
                    'description': 'Email template for product catalog mismatches',
                    'category': 'catalog',
                    'fields': ['mismatched_items', 'suggested_alternatives', 'order_details']
                },
                {
                    'id': 'data_quality_issues',
                    'name': 'Data Quality Issues',
                    'description': 'Email template for data quality problems',
                    'category': 'quality',
                    'fields': ['quality_issues', 'correction_guidance', 'order_details']
                },
                {
                    'id': 'order_confirmation',
                    'name': 'Order Confirmation',
                    'description': 'Email template for order confirmation',
                    'category': 'confirmation',
                    'fields': ['order_summary', 'customer_details', 'next_steps']
                }
            ]
            
            return templates
            
        except Exception as e:
            logger.error(f"Error getting email templates: {str(e)}")
            return []
    
    async def generate_consolidation_email(
        self, 
        orders: List[Order], 
        consolidation_notes: Optional[str] = None
    ) -> str:
        """Generate consolidation email content"""
        try:
            total_orders = len(orders)
            total_quantity = sum(order.total_quantity or 0 for order in orders)
            total_value = sum(float(order.total) if order.total else 0 for order in orders)
            
            # Get order details
            order_details = []
            for order in orders:
                order_details.append({
                    'order_number': order.order_number,
                    'quantity': order.total_quantity or 0,
                    'value': float(order.total) if order.total else 0,
                    'status': order.status,
                    'created_date': order.created_at.strftime('%Y-%m-%d') if order.created_at else 'N/A'
                })
            
            # Get manufacturer information
            manufacturer_name = "Not assigned"
            if orders[0].manufacturer_id:
                # In a real implementation, you'd fetch the manufacturer details
                manufacturer_name = f"Manufacturer ID: {orders[0].manufacturer_id}"
            
            email_content = f"""
Subject: Order Consolidation Notice - {total_orders} Orders Combined

Dear Customer,

We are pleased to inform you that your orders have been successfully consolidated for efficient processing and delivery.

CONSOLIDATION DETAILS:
-------------------
Total Orders Consolidated: {total_orders}
Total Items: {total_quantity}
Total Value: ${total_value:.2f}
Consolidation Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Assigned Manufacturer: {manufacturer_name}

INCLUDED ORDERS:
---------------
"""
            
            for i, order_detail in enumerate(order_details, 1):
                email_content += f"""
{i}. Order Number: {order_detail['order_number']}
   Quantity: {order_detail['quantity']} items
   Value: ${order_detail['value']:.2f}
   Status: {order_detail['status']}
   Order Date: {order_detail['created_date']}
"""
            
            if consolidation_notes:
                email_content += f"""
CONSOLIDATION NOTES:
------------------
{consolidation_notes}
"""
            
            email_content += """
BENEFITS OF CONSOLIDATION:
------------------------
✓ Reduced shipping costs
✓ Faster processing time
✓ Simplified tracking
✓ Environmental efficiency

NEXT STEPS:
----------
1. Your consolidated order will be processed by our assigned manufacturer
2. You will receive a single shipment tracking number
3. Delivery will be coordinated for all items together
4. A consolidated invoice will be generated

If you have any questions about this consolidation, please contact our customer service team.

Thank you for your business!

Best regards,
Order Management Team
"""
            
            return email_content
            
        except Exception as e:
            logger.error(f"Error generating consolidation email: {str(e)}")
            return f"Error generating consolidation email: {str(e)}"

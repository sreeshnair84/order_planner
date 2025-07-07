import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from jinja2 import Environment, FileSystemLoader
from typing import List, Optional, Dict, Any
import logging
import os
from app.utils.config import settings

logger = logging.getLogger(__name__)

class EmailService:
    """Service class for sending emails"""
    
    def __init__(self):
        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT
        self.username = settings.SMTP_USERNAME
        self.password = settings.SMTP_PASSWORD
        
        # Initialize Jinja2 environment for email templates
        template_dir = os.path.join(os.path.dirname(__file__), '..', 'templates', 'emails')
        self.jinja_env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=True
        )
    
    async def send_missing_info_email(
        self,
        recipient: str,
        order_number: str,
        missing_fields: List[str],
        order_data: Dict[str, Any]
    ) -> bool:
        """Send email requesting missing order information"""
        try:
            template = self.jinja_env.get_template('missing_info.html')
            
            html_content = template.render(
                order_number=order_number,
                missing_fields=missing_fields,
                order_data=order_data
            )
            
            subject = f"Missing Information Required for Order {order_number}"
            
            return await self._send_email(
                recipient=recipient,
                subject=subject,
                html_content=html_content
            )
            
        except Exception as e:
            logger.error(f"Error sending missing info email: {str(e)}")
            return False
    
    async def send_order_confirmation_email(
        self,
        recipient: str,
        order_number: str,
        order_data: Dict[str, Any]
    ) -> bool:
        """Send order confirmation email"""
        try:
            template = self.jinja_env.get_template('order_confirmation.html')
            
            html_content = template.render(
                order_number=order_number,
                order_data=order_data
            )
            
            subject = f"Order Confirmation - {order_number}"
            
            return await self._send_email(
                recipient=recipient,
                subject=subject,
                html_content=html_content
            )
            
        except Exception as e:
            logger.error(f"Error sending order confirmation email: {str(e)}")
            return False
    
    async def send_status_update_email(
        self,
        recipient: str,
        order_number: str,
        new_status: str,
        message: Optional[str] = None
    ) -> bool:
        """Send order status update email"""
        try:
            template = self.jinja_env.get_template('status_update.html')
            
            html_content = template.render(
                order_number=order_number,
                new_status=new_status,
                message=message
            )
            
            subject = f"Order Status Update - {order_number}"
            
            return await self._send_email(
                recipient=recipient,
                subject=subject,
                html_content=html_content
            )
            
        except Exception as e:
            logger.error(f"Error sending status update email: {str(e)}")
            return False
    
    async def send_error_notification_email(
        self,
        recipient: str,
        order_number: str,
        error_message: str
    ) -> bool:
        """Send error notification email"""
        try:
            template = self.jinja_env.get_template('error_notification.html')
            
            html_content = template.render(
                order_number=order_number,
                error_message=error_message
            )
            
            subject = f"Order Processing Error - {order_number}"
            
            return await self._send_email(
                recipient=recipient,
                subject=subject,
                html_content=html_content
            )
            
        except Exception as e:
            logger.error(f"Error sending error notification email: {str(e)}")
            return False
    
    async def send_trip_notification_email(
        self,
        recipient: str,
        order_number: str,
        trip_data: Dict[str, Any]
    ) -> bool:
        """Send trip assignment notification email"""
        try:
            template = self.jinja_env.get_template('trip_notification.html')
            
            html_content = template.render(
                order_number=order_number,
                trip_data=trip_data
            )
            
            subject = f"Trip Assigned for Order {order_number}"
            
            return await self._send_email(
                recipient=recipient,
                subject=subject,
                html_content=html_content
            )
            
        except Exception as e:
            logger.error(f"Error sending trip notification email: {str(e)}")
            return False
    
    async def send_delivery_notification_email(
        self,
        recipient: str,
        order_number: str,
        delivery_data: Dict[str, Any]
    ) -> bool:
        """Send delivery notification email"""
        try:
            template = self.jinja_env.get_template('delivery_notification.html')
            
            html_content = template.render(
                order_number=order_number,
                delivery_data=delivery_data
            )
            
            subject = f"Your Order is Out for Delivery - {order_number}"
            
            return await self._send_email(
                recipient=recipient,
                subject=subject,
                html_content=html_content
            )
            
        except Exception as e:
            logger.error(f"Error sending delivery notification email: {str(e)}")
            return False
    
    async def send_sku_validation_email(
        self,
        recipient: str,
        order_number: str,
        sku_validation_data: Dict[str, Any]
    ) -> bool:
        """Send SKU validation request email"""
        try:
            template = self.jinja_env.get_template('sku_validation.html')
            
            html_content = template.render(
                order_number=order_number,
                sku_validation_data=sku_validation_data
            )
            
            subject = f"SKU Validation Required for Order {order_number}"
            
            return await self._send_email(
                recipient=recipient,
                subject=subject,
                html_content=html_content
            )
            
        except Exception as e:
            logger.error(f"Error sending SKU validation email: {str(e)}")
            return False
    
    async def _send_email(
        self,
        recipient: str,
        subject: str,
        html_content: str,
        attachments: Optional[List[str]] = None
    ) -> bool:
        """Send email using SMTP"""
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.username
            message["To"] = recipient
            
            # Add HTML content
            html_part = MIMEText(html_content, "html")
            message.attach(html_part)
            
            # Add attachments if provided
            if attachments:
                for file_path in attachments:
                    if os.path.exists(file_path):
                        with open(file_path, "rb") as attachment:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(attachment.read())
                            encoders.encode_base64(part)
                            part.add_header(
                                'Content-Disposition',
                                f'attachment; filename= {os.path.basename(file_path)}'
                            )
                            message.attach(part)
            
            # Send email
            await aiosmtplib.send(
                message,
                hostname=self.smtp_server,
                port=self.smtp_port,
                start_tls=True,
                username=self.username,
                password=self.password
            )
            
            logger.info(f"Email sent successfully to {recipient}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email to {recipient}: {str(e)}")
            return False
    
    def generate_missing_info_template(self, missing_fields: List[str]) -> str:
        """Generate a template for missing information email"""
        template = """
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .header { background-color: #f8f9fa; padding: 20px; border-radius: 5px; }
                .content { margin: 20px 0; }
                .missing-fields { background-color: #fff3cd; padding: 15px; border-radius: 5px; }
                .field-list { list-style-type: none; padding: 0; }
                .field-list li { padding: 5px; margin: 5px 0; background-color: #fff; border-radius: 3px; }
            </style>
        </head>
        <body>
            <div class="header">
                <h2>Missing Information Required for Order {{ order_number }}</h2>
            </div>
            
            <div class="content">
                <p>Dear Customer,</p>
                
                <p>We have received your order file, but we need some additional information to process it completely.</p>
                
                <div class="missing-fields">
                    <h3>Missing Information:</h3>
                    <ul class="field-list">
                    {% for field in missing_fields %}
                        <li>{{ field }}</li>
                    {% endfor %}
                    </ul>
                </div>
                
                <p>Please reply to this email with the missing information, and we will continue processing your order.</p>
                
                <p>Best regards,<br>
                Order Management Team</p>
            </div>
        </body>
        </html>
        """
        return template

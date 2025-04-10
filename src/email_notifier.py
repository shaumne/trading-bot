import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import logging
from config import (
    EMAIL_HOST,
    EMAIL_PORT,
    EMAIL_USERNAME,
    EMAIL_PASSWORD,
    EMAIL_RECIPIENT,
    EMAIL_USE_TLS
)

logger = logging.getLogger(__name__)

def send_order_notification(order_details):
    """
    Send email notification with order details
    
    Args:
        order_details (dict): Dictionary containing order information
    """
    try:
        # Create message container
        msg = MIMEMultipart()
        msg['From'] = EMAIL_USERNAME
        msg['To'] = EMAIL_RECIPIENT
        msg['Subject'] = f"New Trading Order - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        # Create email body
        body = f"""
        New Order Details:
        
        Symbol: {order_details.get('symbol', 'N/A')}
        Side: {order_details.get('side', 'N/A')}
        Type: {order_details.get('type', 'N/A')}
        Quantity: {order_details.get('quantity', 'N/A')}
        Price: {order_details.get('price', 'N/A')}
        Status: {order_details.get('status', 'N/A')}
        Order ID: {order_details.get('orderId', 'N/A')}
        Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        
        Trading Bot Notification
        """

        msg.attach(MIMEText(body, 'plain'))

        # Create server
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        if EMAIL_USE_TLS:
            server.starttls()
        
        # Login to server
        server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
        
        # Send email
        text = msg.as_string()
        server.sendmail(EMAIL_USERNAME, EMAIL_RECIPIENT, text)
        server.quit()
        
        logger.info(f"Order notification email sent successfully to {EMAIL_RECIPIENT}")
        
    except Exception as e:
        logger.error(f"Failed to send order notification email: {str(e)}") 
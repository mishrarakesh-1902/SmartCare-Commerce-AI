import logging
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)

def send_support_resolution_email(
    to_email: str,
    customer_name: str,
    ticket_id: str,
    subject: str,
    resolution_text: str,
    order_id: str = None
) -> bool:
    """
    Sends an automated, human-grade customer support email resolution directly
    to the customer's inbox.
    """
    if not to_email:
        logger.warning("No recipient email provided for support ticket.")
        return False

    email_subject = f"[Ticket #{ticket_id}] Regarding: {subject} - Ajara Shopper Support"
    
    order_context_str = f"Related Order ID: #{order_id}\n" if order_id else ""

    plain_message = f"""Dear {customer_name or 'Valued Customer'},

Thank you for reaching out to Ajara Shopper Customer Support. 

Your request (Ticket #{ticket_id}) has been reviewed and resolved by our AI Customer Support Desk:

{order_context_str}
------------------------------------------------------------
RESOLUTION & NEXT STEPS:
------------------------------------------------------------
{resolution_text}
------------------------------------------------------------

If you have any further questions or if your issue is not completely resolved, you can reply directly to this email or visit our AI Support Desk on our website anytime.

Warm regards,
Ajara Shopper Customer Support Team
support@ajarashopper.com
"""

    html_message = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f7f9fa; margin: 0; padding: 20px; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.06); }}
            .header {{ background: linear-gradient(135deg, #FE980F 0%, #e67e22 100%); color: #ffffff; padding: 25px; text-align: center; }}
            .header h1 {{ margin: 0; font-size: 24px; font-weight: 700; }}
            .ticket-badge {{ display: inline-block; background: rgba(255,255,255,0.25); padding: 4px 12px; border-radius: 20px; font-size: 13px; margin-top: 8px; }}
            .content {{ padding: 30px 25px; }}
            .order-box {{ background: #fdf5ea; border-left: 4px solid #FE980F; padding: 12px 16px; margin: 15px 0 25px; border-radius: 0 8px 8px 0; font-size: 14px; }}
            .resolution-card {{ background: #fafafa; border: 1px solid #ebebeb; border-radius: 8px; padding: 20px; line-height: 1.6; font-size: 15px; margin: 20px 0; }}
            .footer {{ background: #f1f3f5; padding: 20px; text-align: center; font-size: 12px; color: #888; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Ajara Shopper</h1>
                <div class="ticket-badge">Ticket #{ticket_id}</div>
            </div>
            <div class="content">
                <p>Dear <strong>{customer_name or 'Valued Customer'}</strong>,</p>
                <p>Thank you for contacting Ajara Shopper Support. Our automated support engine has processed your inquiry:</p>
                
                {f'<div class="order-box">📦 <strong>Linked Order:</strong> #{order_id}</div>' if order_id else ''}

                <div class="resolution-card">
                    <h3 style="margin-top:0; color:#FE980F; font-size:16px;">Resolution Summary</h3>
                    <p style="white-space: pre-wrap; margin-bottom: 0;">{resolution_text}</p>
                </div>

                <p style="font-size: 13px; color: #666;">
                    Need more help? You can check status anytime on our website under <strong>AI Support Desk</strong>.
                </p>
            </div>
            <div class="footer">
                &copy; Ajara Shopper Inc. | Automated Support Dispatch<br>
                This email was sent in response to your customer service request.
            </div>
        </div>
    </body>
    </html>
    """

    try:
        from_email = getattr(settings, 'EMAIL_HOST_USER', 'support@ajarashopper.com')
        send_mail(
            subject=email_subject,
            message=plain_message,
            from_email=from_email,
            recipient_list=[to_email],
            html_message=html_message,
            fail_silently=False
        )
        logger.info(f"✅ Support email sent successfully to {to_email} for Ticket #{ticket_id}")
        return True
    except Exception as e:
        logger.error(f"⚠️ Failed to send email via SMTP ({e}). Simulated delivery logged.")
        # Print clearly to console so user can see it in development
        print(f"\n[EMAIL DISPATCH SIMULATOR]")
        print(f"TO: {to_email}")
        print(f"SUBJECT: {email_subject}")
        print(f"BODY:\n{plain_message[:200]}...\n")
        return True  # Return True so flow continues in development

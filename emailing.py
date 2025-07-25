# emailing.py
import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

def send_email(image_path):
    # Configure email
    msg = EmailMessage()
    msg["Subject"] = "Security Alert: Motion Detected"
    msg["From"] = os.getenv("MAIL_USER")
    msg["To"] = os.getenv("RECEIVER_EMAIL")
    msg.set_content("Motion detected in your surveillance area. Review the attached image.")
    
    # Attach image
    with open(image_path, "rb") as f:
        img_data = f.read()
        msg.add_attachment(
            img_data, 
            maintype="image", 
            subtype="png",  # Explicit subtype for better compatibility
            filename=os.path.basename(image_path)
        )
    
    # Send email
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(os.getenv("MAIL_USER"), os.getenv("MAIL_PASS"))
            server.send_message(msg)
        print("Email sent successfully")
    except Exception as e:
        print(f"Email failed: {str(e)}")
    finally:
        # Cleanup image after sending
        try:
            os.remove(image_path)
        except OSError:
            pass
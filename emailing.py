from dotenv import load_dotenv
import os
import smtplib, ssl
import imghdr
from email.message import EmailMessage

load_dotenv()  # Loads variables from .env

username = os.getenv("MAIL_USER")
password = os.getenv("MAIL_PASS")
receiver = os.getenv("RECEIVER_EMAIL")


def send_email(image_path):
    email_message = EmailMessage()
    email_message["Subject"] = "New motion detected"
    email_message.set_content("Hey, there is a new motion detected in your home. Check it out.")
    
    with open(image_path, "rb") as file:
        content = file.read()
        
    email_message.add_attachment(content, maintype="image", subtype=imghdr.what(None, h=content))
    
    gmail = smtplib.SMTP("smtp.gmail.com", 587)
    gmail.ehlo()
    gmail.starttls()
    gmail.login(username, password)
    gmail.sendmail(username, receiver, email_message.as_string())
    gmail.quit()
    
    # or, if you want to use SSL
    # context = ssl.create_default_context()
    # with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as smtp:
    #     smtp.login(username, password)
    #     smtp.sendmail(username, receiver, email_message.as_string())
        
if __name__ == "__main__":
    send_email(image_path="images/1.png")
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import os
from ..config import settings

class EmailService:
    def __init__(self):
        self.smtp_server = getattr(settings, 'SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = getattr(settings, 'SMTP_PORT', 587)
        self.smtp_username = getattr(settings, 'SMTP_USERNAME', '')
        self.smtp_password = getattr(settings, 'SMTP_PASSWORD', '')
        self.from_email = getattr(settings, 'FROM_EMAIL', self.smtp_username)
    
    def send_temp_password_email(self, to_email: str, temp_password: str, user_name: str) -> bool:
        """Send temporary password email to new employee"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Subject'] = "Welcome to Smart Forum HRMS - Your Temporary Password"
            
            body = f"""
            Dear {user_name},
            
            Welcome to Smart Forum HRMS! Your account has been created successfully.
            
            Your login credentials:
            Email: {to_email}
            Temporary Password: {temp_password}
            
            Please log in to the system and change your password immediately for security purposes.
            
            Login URL: http://localhost:3000/login
            
            If you have any questions, please contact your HR department.
            
            Best regards,
            Smart Forum HRMS Team
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email (mock for development)
            if not self.smtp_username:
                print(f"[EMAIL MOCK] To: {to_email}")
                print(f"[EMAIL MOCK] Subject: Welcome to Smart Forum HRMS")
                print(f"[EMAIL MOCK] Temp Password: {temp_password}")
                return True
            
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            text = msg.as_string()
            server.sendmail(self.from_email, to_email, text)
            server.quit()
            
            return True
        except Exception as e:
            print(f"Failed to send email: {str(e)}")
            return False

email_service = EmailService()
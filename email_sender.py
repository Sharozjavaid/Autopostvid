import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import os
import ssl

class EmailSender:
    def __init__(self):
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 465
        self.sender_email = os.getenv("EMAIL_USER")
        self.password = os.getenv("EMAIL_PASSWORD")
        
        # Default recipient to sender if not specified
        self.default_recipient = os.getenv("RECIPIENT_EMAIL") or self.sender_email

    def send_video(self, video_path: str, recipient: str = None, subject: str = None, body: str = None, caption: str = None):
        """Send an email with the generated video attachment and optional TikTok caption"""
        
        if not self.sender_email or not self.password:
            print("❌ Error: EMAIL_USER or EMAIL_PASSWORD not set in .env")
            return False

        if not recipient:
            recipient = self.default_recipient

        msg = MIMEMultipart()
        msg['From'] = self.sender_email
        msg['To'] = recipient
        msg['Subject'] = subject or "Your Generated Philosophy Video is Ready 🎥"

        body_text = body or "Here is your fresh philosophy video! Enjoy.\n\nAutomated by your Agent."
        
        # Add TikTok caption section if provided
        if caption:
            body_text += "\n\n" + "=" * 50
            body_text += "\n📱 TIKTOK CAPTION (Copy & Paste):\n"
            body_text += "=" * 50
            body_text += f"\n\n{caption}\n"
            body_text += "\n" + "=" * 50
        
        msg.attach(MIMEText(body_text, 'plain'))

        # Attach Video
        if video_path and os.path.exists(video_path):
            try:
                with open(video_path, "rb") as f:
                    # Read the file
                    video_data = f.read()
                    name = os.path.basename(video_path)
                    
                    # Create attachment
                    part = MIMEApplication(video_data, Name=name)
                    part['Content-Disposition'] = f'attachment; filename="{name}"'
                    msg.attach(part)
                    print(f"📎 Attached video: {name} ({len(video_data)/1024/1024:.1f} MB)")
            except Exception as e:
                print(f"❌ Error attaching video: {e}")
                return False
        else:
            print(f"⚠️ Video path not found: {video_path}")
            # Send anyway? Maybe just to notify failure? 
            # For now, let's fail if we can't attach the video as that's the whole point.
            return False

        # Send Email
        try:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, context=context) as server:
                server.login(self.sender_email, self.password)
                server.sendmail(self.sender_email, recipient, msg.as_string())
            
            print(f"✅ Email sent successfully to {recipient}!")
            return True
        except Exception as e:
            print(f"❌ Failed to send email: {e}")
            return False

if __name__ == "__main__":
    # Test the sender
    from dotenv import load_dotenv
    load_dotenv()
    
    sender = EmailSender()
    if sender.sender_email:
        print(f"Testing email creds for: {sender.sender_email}")
        # Create a dummy file for testing if real one doesn't exist
        dummy_path = "test_video.txt"
        with open(dummy_path, "w") as f:
            f.write("This is a dummy video file.")
            
        sender.send_video(dummy_path, subject="Test Email from Agent", body="If you see this, the email automation is working!")
        
        # cleanup
        if os.path.exists(dummy_path):
            os.remove(dummy_path)
    else:
        print("Please set EMAIL_USER and EMAIL_PASSWORD in .env to test.")

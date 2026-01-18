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

    def send_slideshow(
        self, 
        image_paths: list, 
        recipient: str = None, 
        subject: str = None, 
        body: str = None, 
        caption: str = None,
        hashtags: list = None
    ):
        """Send an email with slideshow images as attachments for manual Instagram posting.
        
        Args:
            image_paths: List of image file paths to attach
            recipient: Email recipient (defaults to RECIPIENT_EMAIL or sender)
            subject: Email subject
            body: Email body text
            caption: Suggested Instagram caption
            hashtags: List of hashtags to include
        """
        
        if not self.sender_email or not self.password:
            print("❌ Error: EMAIL_USER or EMAIL_PASSWORD not set in .env")
            return False

        if not recipient:
            recipient = self.default_recipient

        if not image_paths:
            print("❌ Error: No images provided")
            return False

        msg = MIMEMultipart()
        msg['From'] = self.sender_email
        msg['To'] = recipient
        msg['Subject'] = subject or f"📸 Instagram Slideshow Ready ({len(image_paths)} slides)"

        # Build the email body
        body_text = body or "Your Instagram slideshow is ready! Find the images attached below.\n\n"
        body_text += f"📊 Total slides: {len(image_paths)}\n"
        
        # Add suggested caption
        if caption:
            body_text += "\n" + "=" * 50
            body_text += "\n📝 SUGGESTED CAPTION (Copy & Paste):\n"
            body_text += "=" * 50
            body_text += f"\n\n{caption}\n"
        
        # Add hashtags
        if hashtags:
            hashtag_str = " ".join(f"#{tag}" for tag in hashtags)
            body_text += "\n" + "=" * 50
            body_text += "\n🏷️ HASHTAGS:\n"
            body_text += "=" * 50
            body_text += f"\n\n{hashtag_str}\n"
        
        body_text += "\n" + "=" * 50
        body_text += "\n\n📱 HOW TO POST:\n"
        body_text += "1. Save all attached images to your phone\n"
        body_text += "2. Open Instagram and tap + to create a post\n"
        body_text += "3. Select all images (tap the 'multiple' icon)\n"
        body_text += "4. Add music, filters, and edit caption as desired\n"
        body_text += "5. Post when ready!\n"
        body_text += "\n" + "=" * 50
        
        msg.attach(MIMEText(body_text, 'plain'))

        # Attach all images
        attached_count = 0
        for i, image_path in enumerate(image_paths, 1):
            if image_path and os.path.exists(image_path):
                try:
                    with open(image_path, "rb") as f:
                        image_data = f.read()
                        name = os.path.basename(image_path)
                        
                        # Create attachment
                        part = MIMEApplication(image_data, Name=name)
                        part['Content-Disposition'] = f'attachment; filename="slide_{i:02d}_{name}"'
                        msg.attach(part)
                        attached_count += 1
                        print(f"📎 Attached slide {i}: {name} ({len(image_data)/1024:.1f} KB)")
                except Exception as e:
                    print(f"⚠️ Error attaching {image_path}: {e}")
            else:
                print(f"⚠️ Image not found: {image_path}")

        if attached_count == 0:
            print("❌ No images could be attached")
            return False

        # Send Email
        try:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, context=context) as server:
                server.login(self.sender_email, self.password)
                server.sendmail(self.sender_email, recipient, msg.as_string())
            
            print(f"✅ Slideshow email sent to {recipient} with {attached_count} images!")
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

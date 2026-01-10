import requests
import os
import urllib.parse

class TikTokUploader:
    def __init__(self):
        self._load_env()
        self.client_key = os.getenv("TIKTOK_CLIENT_KEY")
        self.client_secret = os.getenv("TIKTOK_CLIENT_SECRET")
        # Ensure this matches your Redirect URI in TikTok Developer Portal
        self.redirect_uri = os.getenv("TIKTOK_REDIRECT_URI", "http://localhost:8501") 
        
        self.auth_base_url = "https://www.tiktok.com/v2/auth/authorize/"
        self.token_url = "https://open.tiktokapis.com/v2/oauth/token/"
        self.init_upload_url = "https://open.tiktokapis.com/v2/post/publish/video/init/"
        
        print(f"DEBUG: TIKTOK_CLIENT_KEY loaded: '{self.client_key}'")
        secret_preview = f"{self.client_secret[:3]}...{self.client_secret[-3:]}" if self.client_secret else "None"
        print(f"DEBUG: TIKTOK_CLIENT_SECRET loaded: '{secret_preview}'")

    def _load_env(self):
        """Manually load .env file to ensure variables are set even if process didn't restart."""
        try:
            if os.path.exists(".env"):
                print("DEBUG: Loading .env manually")
                with open(".env", "r") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#"): continue
                        try:
                            key, value = line.split("=", 1)
                            os.environ[key.strip()] = value.strip()
                        except ValueError:
                            pass
        except Exception as e:
            print(f"DEBUG: Error loading .env: {e}")
            
        except Exception as e:
            print(f"DEBUG: Error loading .env: {e}")
        
    def generate_pkce_pair(self):
        """Generates a code_verifier and code_challenge for PKCE."""
        import secrets
        import hashlib
        import base64
        
        # 1. Generate code_verifier (random string)
        code_verifier = secrets.token_urlsafe(32)
        
        # 2. Generate code_challenge (SHA256 hash of verifier, then base64url encoded)
        m = hashlib.sha256()
        m.update(code_verifier.encode('ascii'))
        d = m.digest()
        # base64.urlsafe_b64encode returns bytes, we need string without padding '='
        code_challenge = base64.urlsafe_b64encode(d).decode('ascii').rstrip('=')
        
        return code_verifier, code_challenge

    def get_auth_url(self, code_challenge):
        """Generates the URL for the user to authorize the app."""
        csrf_state = "custom_state_string" # In production, randomize this
        
        params = {
            "client_key": self.client_key,
            "scope": "user.info.basic,video.publish,video.upload",
            "response_type": "code",
            "redirect_uri": self.redirect_uri,
            "state": csrf_state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256"
        }
        
        auth_url = f"{self.auth_base_url}?{urllib.parse.urlencode(params)}"
        return auth_url

    def get_access_token(self, code, code_verifier):
        """Exchanges authorization code for an access token."""
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Cache-Control": "no-cache"
        }
        
        data = {
            "client_key": self.client_key,
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": self.redirect_uri,
            "code_verifier": code_verifier
        }
        
        response = requests.post(self.token_url, headers=headers, data=data)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get token: {response.text}")

    def upload_video(self, access_token, file_path, title, privacy_level="SELF_ONLY"):
        """
        Uploads a video to TikTok.
        
        Args:
            access_token (str): The valid access token.
            file_path (str): Local path to the video file.
            title (str): Caption/Title for the video.
            privacy_level (str): 'PUBLIC', 'FRIENDS', or 'SELF_ONLY' (default).
            
        Returns:
            dict: The result containing publish_id.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Video file not found: {file_path}")
            
        file_size = os.path.getsize(file_path)
        
        # 1. Initialize Upload
        init_headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; charset=UTF-8"
        }
        
        # Note: TikTok Sandbox often requires SELF_ONLY (Private) or MUTUAL_FOLLOW_FRIENDS. 
        # PUBLIC might be restricted depending on app status.
        init_data = {
            "post_info": {
                "title": title,
                "privacy_level": privacy_level,
                "disable_duet": False,
                "disable_comment": True,
                "disable_stitch": False,
                "video_cover_timestamp_ms": 1000
            },
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": file_size,
                "chunk_size": file_size, # Uploading in one chunk for simplicity
                "total_chunk_count": 1
            }
        }
        
        print("Initializing upload...")
        init_response = requests.post(self.init_upload_url, headers=init_headers, json=init_data)
        
        if init_response.status_code != 200:
            raise Exception(f"Failed to initialize upload: {init_response.text}")
            
        init_json = init_response.json()
        
        # Check for error in body
        if "error" in init_json and init_json["error"]["code"] != "ok":
             raise Exception(f"API Error during init: {init_json['error']}")

        upload_url = init_json["data"]["upload_url"]
        publish_id = init_json["data"]["publish_id"]
        
        # 2. Upload Video Content (PUT)
        print(f"Uploading file ({file_size} bytes) to {upload_url[:50]}...")
        
        with open(file_path, 'rb') as f:
            video_data = f.read()
            
        upload_headers = {
            "Content-Type": "video/mp4",
            "Content-Range": f"bytes 0-{file_size-1}/{file_size}"
        }
        
        upload_response = requests.put(upload_url, headers=upload_headers, data=video_data)
        
        if upload_response.status_code not in [200, 201]: # Verify successful upload codes
             raise Exception(f"Failed to upload video data: {upload_response.text}")
             
        return {"status": "success", "publish_id": publish_id}

"""
Google Cloud Storage service for persistent file storage.

PRODUCTION ONLY: All generated content (images, slideshows, scripts) is uploaded 
to GCS and served via public URLs. This ensures content persists and is accessible
from anywhere.

LOCAL DEVELOPMENT: Uses local filesystem storage (no GCS uploads).

Bucket: gs://philosophy-content-storage
Public URL: https://storage.googleapis.com/philosophy-content-storage/...
"""

import os
import uuid
from pathlib import Path
from typing import Optional
from datetime import datetime

# Import environment detection
from ..config import IS_PRODUCTION

# Try to import google-cloud-storage, gracefully degrade if not available
try:
    from google.cloud import storage
    GCS_AVAILABLE = True
except ImportError:
    GCS_AVAILABLE = False
    if IS_PRODUCTION:
        print("⚠️ google-cloud-storage not installed. Using local storage only.")


# Configuration
GCS_BUCKET_NAME = "philosophy-content-storage"
GCS_PUBLIC_URL = f"https://storage.googleapis.com/{GCS_BUCKET_NAME}"

# Possible locations for credentials file (production paths)
CREDENTIALS_PATHS = [
    Path("/home/runner/philosophy_video_generator/gcs-credentials.json"),  # GCP VM
    Path(__file__).parent.parent.parent.parent / "gcs-credentials.json",  # Project root
    Path("/app/gcs-credentials.json"),  # Docker
]


def _find_credentials() -> Optional[str]:
    """Find the GCS credentials file."""
    # First check environment variable
    env_creds = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if env_creds and Path(env_creds).exists():
        return env_creds
    
    # Then check known paths
    for path in CREDENTIALS_PATHS:
        if path.exists():
            return str(path)
    
    return None


class CloudStorageService:
    """
    Service for uploading and managing files in Google Cloud Storage.
    
    PRODUCTION: Uploads to GCS, returns public URLs
    LOCAL DEV: No-op, returns None (local paths used instead)
    """
    
    def __init__(self):
        self.bucket_name = GCS_BUCKET_NAME
        self.public_url_base = GCS_PUBLIC_URL
        self.client = None
        self.bucket = None
        self._enabled = IS_PRODUCTION  # Only enable in production
        
        if not self._enabled:
            print("💻 Local development mode - Cloud Storage DISABLED (using local files)")
            return
        
        if GCS_AVAILABLE:
            try:
                # Find and set credentials
                creds_path = _find_credentials()
                if creds_path:
                    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = creds_path
                    print(f"📁 Using GCS credentials: {creds_path}")
                else:
                    print("⚠️ No GCS credentials found - storage disabled")
                    self._enabled = False
                    return
                
                # Initialize client
                self.client = storage.Client()
                self.bucket = self.client.bucket(self.bucket_name)
                print(f"✅ Cloud Storage connected: {self.bucket_name}")
            except Exception as e:
                print(f"⚠️ Cloud Storage init error: {e}")
                print("   Falling back to local storage.")
                self._enabled = False
        else:
            print("⚠️ google-cloud-storage not installed")
            self._enabled = False
    
    @property
    def is_available(self) -> bool:
        """Check if GCS is available and configured."""
        return self._enabled and self.client is not None and self.bucket is not None
    
    def upload_file(
        self,
        local_path: str,
        destination_folder: str = "images",
        custom_filename: Optional[str] = None
    ) -> Optional[str]:
        """
        Upload a file to GCS and return the public URL.
        
        Args:
            local_path: Path to the local file
            destination_folder: Folder in the bucket (images, slideshows, scripts, etc.)
            custom_filename: Optional custom filename (defaults to original + uuid suffix)
        
        Returns:
            Public URL of the uploaded file, or None if upload fails
        """
        if not self.is_available:
            print(f"⚠️ GCS not available, keeping local path: {local_path}")
            return None
        
        local_path = Path(local_path)
        if not local_path.exists():
            print(f"❌ File not found: {local_path}")
            return None
        
        try:
            # Generate unique filename to avoid collisions
            if custom_filename:
                filename = custom_filename
            else:
                # Add UUID suffix to prevent overwrites
                suffix = uuid.uuid4().hex[:8]
                filename = f"{local_path.stem}_{suffix}{local_path.suffix}"
            
            # Create blob path
            blob_path = f"{destination_folder}/{filename}"
            blob = self.bucket.blob(blob_path)
            
            # Set content type based on extension
            content_type = self._get_content_type(local_path.suffix)
            blob.content_type = content_type
            
            # Upload file
            blob.upload_from_filename(str(local_path))
            
            # Get public URL
            public_url = f"{self.public_url_base}/{blob_path}"
            
            print(f"✅ Uploaded to GCS: {public_url}")
            return public_url
            
        except Exception as e:
            print(f"❌ GCS upload error: {e}")
            return None
    
    def upload_bytes(
        self,
        data: bytes,
        filename: str,
        destination_folder: str = "images",
        content_type: str = "image/png"
    ) -> Optional[str]:
        """
        Upload bytes directly to GCS.
        
        Args:
            data: File content as bytes
            filename: Filename to use
            destination_folder: Folder in the bucket
            content_type: MIME type of the content
        
        Returns:
            Public URL of the uploaded file, or None if upload fails
        """
        if not self.is_available:
            print(f"⚠️ GCS not available, cannot upload bytes")
            return None
        
        try:
            # Add UUID suffix to prevent overwrites
            suffix = uuid.uuid4().hex[:8]
            name_parts = filename.rsplit('.', 1)
            if len(name_parts) == 2:
                unique_filename = f"{name_parts[0]}_{suffix}.{name_parts[1]}"
            else:
                unique_filename = f"{filename}_{suffix}"
            
            # Create blob path
            blob_path = f"{destination_folder}/{unique_filename}"
            blob = self.bucket.blob(blob_path)
            blob.content_type = content_type
            
            # Upload bytes
            blob.upload_from_string(data, content_type=content_type)
            
            # Get public URL
            public_url = f"{self.public_url_base}/{blob_path}"
            
            print(f"✅ Uploaded bytes to GCS: {public_url}")
            return public_url
            
        except Exception as e:
            print(f"❌ GCS upload bytes error: {e}")
            return None
    
    def delete_file(self, gcs_url: str) -> bool:
        """
        Delete a file from GCS by its public URL.
        
        Args:
            gcs_url: The public URL of the file
        
        Returns:
            True if deleted, False otherwise
        """
        if not self.is_available:
            return False
        
        try:
            # Extract blob path from URL
            blob_path = gcs_url.replace(f"{self.public_url_base}/", "")
            blob = self.bucket.blob(blob_path)
            blob.delete()
            print(f"🗑️ Deleted from GCS: {blob_path}")
            return True
        except Exception as e:
            print(f"❌ GCS delete error: {e}")
            return False
    
    def list_files(self, prefix: str = "") -> list[str]:
        """
        List files in the bucket with optional prefix filter.
        
        Args:
            prefix: Filter by path prefix (e.g., "images/", "slideshows/project_123")
        
        Returns:
            List of public URLs
        """
        if not self.is_available:
            return []
        
        try:
            blobs = self.bucket.list_blobs(prefix=prefix)
            return [f"{self.public_url_base}/{blob.name}" for blob in blobs]
        except Exception as e:
            print(f"❌ GCS list error: {e}")
            return []
    
    def get_storage_stats(self) -> dict:
        """Get storage statistics for the bucket."""
        if not self.is_available:
            return {"available": False, "error": "GCS not configured"}
        
        try:
            blobs = list(self.bucket.list_blobs())
            total_size = sum(blob.size or 0 for blob in blobs)
            
            # Group by folder
            folders = {}
            for blob in blobs:
                folder = blob.name.split('/')[0] if '/' in blob.name else 'root'
                if folder not in folders:
                    folders[folder] = {"count": 0, "size": 0}
                folders[folder]["count"] += 1
                folders[folder]["size"] += blob.size or 0
            
            return {
                "available": True,
                "bucket": self.bucket_name,
                "total_files": len(blobs),
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "folders": folders,
                "public_url": self.public_url_base
            }
        except Exception as e:
            return {"available": False, "error": str(e)}
    
    def _get_content_type(self, extension: str) -> str:
        """Get MIME type from file extension."""
        content_types = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".webp": "image/webp",
            ".mp4": "video/mp4",
            ".mp3": "audio/mpeg",
            ".wav": "audio/wav",
            ".json": "application/json",
            ".txt": "text/plain",
        }
        return content_types.get(extension.lower(), "application/octet-stream")


# Singleton instance
_storage_service: Optional[CloudStorageService] = None


def get_storage_service() -> CloudStorageService:
    """Get the singleton storage service instance."""
    global _storage_service
    if _storage_service is None:
        _storage_service = CloudStorageService()
    return _storage_service


def upload_video_to_gcs(local_path: str, delete_local: bool = False) -> Optional[str]:
    """
    Upload a video file to GCS and optionally delete the local copy.
    
    Args:
        local_path: Path to the local video file
        delete_local: If True, delete the local file after successful upload
    
    Returns:
        Public URL of the uploaded video, or None if upload fails
    """
    storage = get_storage_service()
    
    if not storage.is_available:
        print(f"⚠️ GCS not available, keeping video locally: {local_path}")
        return None
    
    # Upload to videos/ folder
    public_url = storage.upload_file(local_path, destination_folder="videos")
    
    if public_url and delete_local:
        try:
            import os
            os.remove(local_path)
            print(f"🗑️ Deleted local video after upload: {local_path}")
        except Exception as e:
            print(f"⚠️ Could not delete local file: {e}")
    
    return public_url

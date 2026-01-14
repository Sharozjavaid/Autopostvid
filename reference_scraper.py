"""
Reference Scraper - Downloads TikToks and extracts frames for agent context

This tool allows you to:
1. Download TikTok videos/slideshows from URLs
2. Extract individual frames (slides)
3. Store metadata for agent lookup
4. Feed visual examples to the AI agent
"""

import os
import json
import subprocess
import re
from datetime import datetime
from pathlib import Path
import hashlib

# Use absolute paths based on this file's location
_SCRIPT_DIR = Path(__file__).parent.resolve()
REFERENCES_DIR = _SCRIPT_DIR / "references" / "examples"
REFERENCES_INDEX = _SCRIPT_DIR / "references" / "index.json"


def get_reference_id(url: str) -> str:
    """Generate a short ID from the URL"""
    # Extract video ID from TikTok URL
    match = re.search(r'/(video|photo)/(\d+)', url)
    if match:
        return f"ref_{match.group(2)[-8:]}"
    # Fallback to hash
    return f"ref_{hashlib.md5(url.encode()).hexdigest()[:8]}"


def download_tiktok(url: str, output_dir: Path) -> dict:
    """Download a TikTok video and return metadata"""

    output_template = str(output_dir / "video.%(ext)s")

    # First, get metadata without downloading
    meta_cmd = [
        "yt-dlp",
        "--dump-json",
        "--no-download",
        url
    ]

    print(f"Fetching metadata for {url}...")
    result = subprocess.run(meta_cmd, capture_output=True, text=True)

    metadata = {}
    if result.returncode == 0:
        try:
            metadata = json.loads(result.stdout)
        except json.JSONDecodeError:
            print("Warning: Could not parse metadata")

    # Now download the video
    download_cmd = [
        "yt-dlp",
        "-o", output_template,
        "--no-playlist",
        url
    ]

    print(f"Downloading video...")
    result = subprocess.run(download_cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"Error downloading: {result.stderr}")
        return None

    # Find the downloaded file
    video_file = None
    for f in output_dir.iterdir():
        if f.name.startswith("video."):
            video_file = f
            break

    return {
        "video_file": str(video_file) if video_file else None,
        "title": metadata.get("title", ""),
        "description": metadata.get("description", ""),
        "uploader": metadata.get("uploader", ""),
        "view_count": metadata.get("view_count", 0),
        "like_count": metadata.get("like_count", 0),
        "comment_count": metadata.get("comment_count", 0),
        "duration": metadata.get("duration", 0),
        "upload_date": metadata.get("upload_date", ""),
    }


def extract_frames(video_path: str, output_dir: Path, fps: float = 0.5) -> list:
    """
    Extract frames from video.

    For slideshows: fps=0.5 (1 frame every 2 seconds) works well
    For regular videos: fps=1 (1 frame per second)
    """

    frames_dir = output_dir / "frames"
    frames_dir.mkdir(exist_ok=True)

    # Extract frames using ffmpeg
    output_pattern = str(frames_dir / "slide_%03d.jpg")

    cmd = [
        "ffmpeg",
        "-i", video_path,
        "-vf", f"fps={fps}",
        "-q:v", "2",  # High quality JPEG
        output_pattern,
        "-y"  # Overwrite
    ]

    print(f"Extracting frames at {fps} fps...")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"Error extracting frames: {result.stderr}")
        return []

    # List extracted frames
    frames = sorted([str(f) for f in frames_dir.iterdir() if f.suffix == ".jpg"])
    print(f"Extracted {len(frames)} frames")

    return frames


def add_reference(
    url: str,
    format_type: str = "unknown",
    tags: list = None,
    notes: str = "",
    fps: float = 0.5
) -> dict:
    """
    Add a TikTok reference to the library.

    Args:
        url: TikTok URL
        format_type: "slideshow", "narrated_video", "mentor_slideshow", etc.
        tags: List of tags for searching
        notes: Why this example is good
        fps: Frame extraction rate

    Returns:
        Reference metadata dict
    """

    ref_id = get_reference_id(url)
    ref_dir = REFERENCES_DIR / ref_id
    ref_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*50}")
    print(f"Adding reference: {ref_id}")
    print(f"{'='*50}\n")

    # Download the video
    download_result = download_tiktok(url, ref_dir)

    if not download_result or not download_result.get("video_file"):
        print("Failed to download video")
        return None

    # Extract frames
    frames = extract_frames(download_result["video_file"], ref_dir, fps=fps)

    # Build reference metadata
    reference = {
        "id": ref_id,
        "url": url,
        "format_type": format_type,
        "tags": tags or [],
        "notes": notes,
        "added_date": datetime.now().isoformat(),

        # From TikTok metadata
        "title": download_result.get("title", ""),
        "description": download_result.get("description", ""),
        "uploader": download_result.get("uploader", ""),
        "view_count": download_result.get("view_count", 0),
        "like_count": download_result.get("like_count", 0),
        "duration": download_result.get("duration", 0),

        # Local files
        "video_path": download_result.get("video_file"),
        "frames": frames,
        "frame_count": len(frames),
    }

    # Save reference metadata
    ref_metadata_path = ref_dir / "metadata.json"
    with open(ref_metadata_path, "w") as f:
        json.dump(reference, f, indent=2)

    # Update index
    update_index(reference)

    print(f"\n{'='*50}")
    print(f"Reference added successfully!")
    print(f"  ID: {ref_id}")
    print(f"  Frames: {len(frames)}")
    print(f"  Path: {ref_dir}")
    print(f"{'='*50}\n")

    return reference


def update_index(reference: dict):
    """Update the global references index"""

    index = []
    if REFERENCES_INDEX.exists():
        with open(REFERENCES_INDEX) as f:
            index = json.load(f)

    # Remove existing entry with same ID
    index = [r for r in index if r.get("id") != reference["id"]]

    # Add new entry (summary only, not full paths)
    index.append({
        "id": reference["id"],
        "url": reference["url"],
        "format_type": reference["format_type"],
        "tags": reference["tags"],
        "notes": reference["notes"],
        "title": reference["title"],
        "uploader": reference["uploader"],
        "view_count": reference["view_count"],
        "like_count": reference["like_count"],
        "frame_count": reference["frame_count"],
        "added_date": reference["added_date"],
    })

    REFERENCES_INDEX.parent.mkdir(parents=True, exist_ok=True)
    with open(REFERENCES_INDEX, "w") as f:
        json.dump(index, f, indent=2)


def get_reference(ref_id: str) -> dict:
    """Get a reference by ID with full metadata"""

    ref_dir = REFERENCES_DIR / ref_id
    metadata_path = ref_dir / "metadata.json"

    if not metadata_path.exists():
        return None

    with open(metadata_path) as f:
        return json.load(f)


def list_references(format_type: str = None, tags: list = None) -> list:
    """List all references, optionally filtered"""

    if not REFERENCES_INDEX.exists():
        return []

    with open(REFERENCES_INDEX) as f:
        index = json.load(f)

    if format_type:
        index = [r for r in index if r.get("format_type") == format_type]

    if tags:
        index = [r for r in index if any(t in r.get("tags", []) for t in tags)]

    return index


def get_reference_for_agent(ref_id: str) -> dict:
    """
    Get reference formatted for the agent to see.
    Returns metadata + paths to frame images that can be loaded.
    """

    ref = get_reference(ref_id)
    if not ref:
        return None

    return {
        "id": ref["id"],
        "format_type": ref["format_type"],
        "title": ref["title"],
        "description": ref["description"],
        "view_count": ref["view_count"],
        "like_count": ref["like_count"],
        "notes": ref["notes"],
        "tags": ref["tags"],
        "frames": ref["frames"],  # Agent will load these images
        "frame_count": ref["frame_count"],
    }


def add_manual_reference(
    title: str,
    format_type: str = "slideshow",
    tags: list = None,
    notes: str = "",
    url: str = "",
    uploader: str = "",
    view_count: int = 0,
    like_count: int = 0,
) -> dict:
    """
    Create a manual reference entry (for screenshots/uploads).
    Returns the reference with an ID and directory ready for frame uploads.
    """

    # Generate ID from title or timestamp
    ref_id = f"ref_{hashlib.md5(f'{title}{datetime.now().isoformat()}'.encode()).hexdigest()[:8]}"
    ref_dir = REFERENCES_DIR / ref_id
    ref_dir.mkdir(parents=True, exist_ok=True)

    # Create frames directory
    frames_dir = ref_dir / "frames"
    frames_dir.mkdir(exist_ok=True)

    reference = {
        "id": ref_id,
        "url": url,
        "format_type": format_type,
        "tags": tags or [],
        "notes": notes,
        "added_date": datetime.now().isoformat(),
        "title": title,
        "description": "",
        "uploader": uploader,
        "view_count": view_count,
        "like_count": like_count,
        "duration": 0,
        "video_path": None,
        "frames": [],
        "frame_count": 0,
        "is_manual": True,
    }

    # Save reference metadata
    ref_metadata_path = ref_dir / "metadata.json"
    with open(ref_metadata_path, "w") as f:
        json.dump(reference, f, indent=2)

    # Update index
    update_index(reference)

    return reference


def add_frame_to_reference(ref_id: str, frame_data: bytes, frame_name: str = None) -> dict:
    """
    Add a frame/screenshot to an existing reference.

    Args:
        ref_id: Reference ID
        frame_data: Raw image bytes
        frame_name: Optional custom filename

    Returns:
        Updated reference metadata
    """

    ref_dir = REFERENCES_DIR / ref_id
    frames_dir = ref_dir / "frames"
    metadata_path = ref_dir / "metadata.json"

    if not metadata_path.exists():
        return None

    # Load existing metadata
    with open(metadata_path) as f:
        reference = json.load(f)

    # Determine frame filename
    existing_frames = list(frames_dir.glob("*.jpg")) + list(frames_dir.glob("*.png"))
    frame_num = len(existing_frames) + 1

    if frame_name:
        filename = frame_name if "." in frame_name else f"{frame_name}.jpg"
    else:
        filename = f"slide_{frame_num:03d}.jpg"

    frame_path = frames_dir / filename

    # Save the frame
    with open(frame_path, "wb") as f:
        f.write(frame_data)

    # Update reference metadata
    reference["frames"].append(str(frame_path))
    reference["frame_count"] = len(reference["frames"])

    with open(metadata_path, "w") as f:
        json.dump(reference, f, indent=2)

    # Update index
    update_index(reference)

    return reference


def delete_reference(ref_id: str) -> bool:
    """Delete a reference and all its files."""

    ref_dir = REFERENCES_DIR / ref_id

    if not ref_dir.exists():
        return False

    # Remove from index first
    if REFERENCES_INDEX.exists():
        with open(REFERENCES_INDEX) as f:
            index = json.load(f)
        index = [r for r in index if r.get("id") != ref_id]
        with open(REFERENCES_INDEX, "w") as f:
            json.dump(index, f, indent=2)

    # Delete directory and contents
    import shutil
    shutil.rmtree(ref_dir)

    return True


def update_reference_metadata(ref_id: str, updates: dict) -> dict:
    """Update metadata fields for a reference."""

    ref_dir = REFERENCES_DIR / ref_id
    metadata_path = ref_dir / "metadata.json"

    if not metadata_path.exists():
        return None

    with open(metadata_path) as f:
        reference = json.load(f)

    # Update allowed fields
    allowed_fields = ["title", "format_type", "tags", "notes", "url", "uploader", "view_count", "like_count"]
    for field in allowed_fields:
        if field in updates:
            reference[field] = updates[field]

    with open(metadata_path, "w") as f:
        json.dump(reference, f, indent=2)

    update_index(reference)

    return reference


# CLI interface
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python reference_scraper.py add <url> [format_type] [tags] [notes]")
        print("  python reference_scraper.py add-manual <title> [format_type] [tags] [notes]")
        print("  python reference_scraper.py list [format_type]")
        print("  python reference_scraper.py get <ref_id>")
        print("  python reference_scraper.py delete <ref_id>")
        sys.exit(1)

    command = sys.argv[1]

    if command == "add":
        url = sys.argv[2]
        format_type = sys.argv[3] if len(sys.argv) > 3 else "unknown"
        tags = sys.argv[4].split(",") if len(sys.argv) > 4 else []
        notes = sys.argv[5] if len(sys.argv) > 5 else ""

        add_reference(url, format_type, tags, notes)

    elif command == "add-manual":
        title = sys.argv[2]
        format_type = sys.argv[3] if len(sys.argv) > 3 else "slideshow"
        tags = sys.argv[4].split(",") if len(sys.argv) > 4 else []
        notes = sys.argv[5] if len(sys.argv) > 5 else ""

        ref = add_manual_reference(title, format_type, tags, notes)
        print(json.dumps(ref, indent=2))

    elif command == "list":
        format_type = sys.argv[2] if len(sys.argv) > 2 else None
        refs = list_references(format_type)
        print(json.dumps(refs, indent=2))

    elif command == "get":
        ref_id = sys.argv[2]
        ref = get_reference_for_agent(ref_id)
        print(json.dumps(ref, indent=2))

    elif command == "delete":
        ref_id = sys.argv[2]
        success = delete_reference(ref_id)
        print(f"Deleted: {success}")

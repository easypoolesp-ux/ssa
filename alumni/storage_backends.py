"""
alumni/storage_backends.py
Responsibility: Define named GCS storage backends for each media type.
                One backend per upload category = clear bucket organisation.

GCS Bucket layout:
    ssa-alumni-media/
    ├── events/banners/     ← event poster images (JPG, WebP, GIF)
    └── events/videos/      ← event highlight videos (MP4, WebM)

Bucket is set via GCS_BUCKET_NAME env var (default: ssa-alumni-media).
Files are stored with PUBLIC_URL = False; signed URLs are generated at read time.
"""

from django.conf import settings
from storages.backends.gcloud import GoogleCloudStorage


class EventBannerStorage(GoogleCloudStorage):
    """
    Storage backend for event banner images (JPG / WebP / GIF).
    Uploaded to: gs://<bucket>/events/banners/<filename>
    """

    location = "events/banners"
    file_overwrite = False   # keep originals if re-uploaded


class EventVideoStorage(GoogleCloudStorage):
    """
    Storage backend for event highlight videos (MP4 / WebM).
    Uploaded to: gs://<bucket>/events/videos/<filename>
    Max recommended size: 50 MB — larger assets should use a CDN directly.
    """

    location = "events/videos"
    file_overwrite = False

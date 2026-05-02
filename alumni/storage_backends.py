"""
alumni/storage_backends.py
Responsibility: Named GCS storage backends for each media category.

Both classes read GCS_BUCKET_NAME from Django settings so they always
target the correct bucket, whether running on Cloud Run or locally.

GCS Bucket layout:
    ssa-alumni-media/
    ├── events/banners/     ← event poster images (JPG, WebP, GIF)
    └── events/videos/      ← event highlight videos (MP4, WebM)
"""

from django.conf import settings
from storages.backends.gcloud import GoogleCloudStorage


class EventBannerStorage(GoogleCloudStorage):
    """
    Storage backend for event banner images (JPG / WebP / GIF).
    Uploaded to: gs://<bucket>/events/banners/<filename>
    """

    def __init__(self, **kwargs):
        bucket_name = getattr(settings, "GCS_BUCKET_NAME", "ssa-alumni-media")
        super().__init__(bucket_name=bucket_name, location="events/banners", file_overwrite=False, **kwargs)


class EventVideoStorage(GoogleCloudStorage):
    """
    Storage backend for event highlight videos (MP4 / WebM).
    Uploaded to: gs://<bucket>/events/videos/<filename>
    Max recommended size: 50 MB.
    """

    def __init__(self, **kwargs):
        bucket_name = getattr(settings, "GCS_BUCKET_NAME", "ssa-alumni-media")
        super().__init__(bucket_name=bucket_name, location="events/videos", file_overwrite=False, **kwargs)

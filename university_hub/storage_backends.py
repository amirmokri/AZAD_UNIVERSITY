"""
Custom storage backends for Arvan Cloud Object Storage.

This module provides separate storage backends for static and media files,
allowing them to be stored in different locations within the same bucket.
"""

from storages.backends.s3boto3 import S3Boto3Storage


class StaticStorage(S3Boto3Storage):
    """Storage backend for static files."""
    location = 'static'
    default_acl = 'public-read'
    file_overwrite = True


class MediaStorage(S3Boto3Storage):
    """Storage backend for media files (user uploads)."""
    location = 'media'
    default_acl = 'public-read'
    file_overwrite = False


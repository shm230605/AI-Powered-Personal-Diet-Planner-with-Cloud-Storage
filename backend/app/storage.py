import os
from pathlib import Path

try:
    import boto3
except ImportError:
    boto3 = None

LOCAL_ROOT = Path(os.getenv("LOCAL_STORAGE_PATH", "data/uploads"))


def _s3():
    if boto3 is None:
        raise RuntimeError("Install backend/requirements-cloud.txt to enable S3 storage")
    return boto3.client(
        "s3",
        endpoint_url=os.getenv("S3_ENDPOINT_URL") or None,
        region_name=os.getenv("S3_REGION", "auto"),
        aws_access_key_id=os.getenv("S3_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("S3_SECRET_ACCESS_KEY"),
    )


def put_object(key: str, content: bytes, content_type: str) -> None:
    bucket = os.getenv("S3_BUCKET")
    if bucket:
        _s3().put_object(Bucket=bucket, Key=key, Body=content, ContentType=content_type)
        return
    path = LOCAL_ROOT / key
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def get_object(key: str) -> bytes:
    bucket = os.getenv("S3_BUCKET")
    if bucket:
        return _s3().get_object(Bucket=bucket, Key=key)["Body"].read()
    return (LOCAL_ROOT / key).read_bytes()


def delete_object(key: str) -> None:
    bucket = os.getenv("S3_BUCKET")
    if bucket:
        _s3().delete_object(Bucket=bucket, Key=key)
        return
    (LOCAL_ROOT / key).unlink(missing_ok=True)
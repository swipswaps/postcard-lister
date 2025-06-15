import boto3
import os
from datetime import datetime
from botocore.exceptions import BotoCoreError, NoCredentialsError
import re

def sanitize_filename(filename):
    # Replace or remove unsafe characters
    return re.sub(r'[^\w\-.]', '_', filename)

def sanitize_path_part(name: str) -> str:
    return re.sub(r'[^\w\-.]', '_', name)

def upload_to_s3(file_path: str, bucket: str, folder_name: str, aws_access_key: str, aws_secret_key: str, region: str = "us-east-1", s3_base_url: str = "") -> str:
    try:
        session = boto3.session.Session(
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=region
        )
        s3 = session.client("s3")

        file_name = sanitize_filename(os.path.basename(file_path))
        today = datetime.today().strftime("%Y-%m-%d")

        safe_folder_name = sanitize_path_part(folder_name)
        s3_key = os.path.join("Postcards", today, safe_folder_name, file_name).replace("\\", "/")

        s3.upload_file(
            file_path,
            bucket,
            s3_key,
            ExtraArgs={
                "ContentType": "image/jpeg"
            }
        )

        # Use custom base URL if provided, otherwise use default S3 URL
        if s3_base_url:
            public_url = f"{s3_base_url.rstrip('/')}/{s3_key}"
        else:
            public_url = f"https://{bucket}.s3.{region}.amazonaws.com/{s3_key}"
        return public_url

    except (BotoCoreError, NoCredentialsError) as e:
        print(f"AWS Upload failed for {file_path}: {e}")
        return ""

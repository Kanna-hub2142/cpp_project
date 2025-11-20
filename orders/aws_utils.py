import json
import os
import boto3
from botocore.exceptions import ClientError
from django.conf import settings

s3_client = boto3.client("s3", region_name=settings.AWS_REGION_NAME)
sqs_client = boto3.client("sqs", region_name=settings.AWS_REGION_NAME)
secrets_client = boto3.client("secretsmanager", region_name=settings.AWS_REGION_NAME)


def upload_to_s3(file_obj, filename: str) -> str:
    """
    Upload a Django InMemoryUploadedFile/File object to S3 and
    return the public URL (assuming bucket is public or via CloudFront).
    """
    bucket = settings.AWS_S3_BUCKET_NAME

    try:
        s3_client.upload_fileobj(
            Fileobj=file_obj,
            Bucket=bucket,
            Key=filename,
            ExtraArgs={"ContentType": file_obj.content_type},
        )
    except ClientError as e:
        raise RuntimeError(f"Error uploading to S3: {e}") from e

    return f"https://{bucket}.s3.{settings.AWS_REGION_NAME}.amazonaws.com/{filename}"


def send_order_event_to_sqs(order) -> None:
    """
    Send an order event to SQS so that a Lambda can pick it up
    and send an email via SNS.
    """
    queue_url = settings.AWS_SQS_QUEUE_URL

    body = {
        "order_id": order.order_id,
        "status": order.status,
        "user_email": order.user.email,
        "product_name": order.product.name,
        "quantity": order.quantity,
        "estimated_delivery": order.estimated_delivery.isoformat(),
    }

    sqs_client.send_message(QueueUrl=queue_url, MessageBody=json.dumps(body))


def get_rds_secret(secret_name: str | None = None) -> dict:
    """
    Example usage of Secrets Manager for RDS details.
    """
    secret_name = secret_name or os.environ.get("RDS_SECRET_NAME")

    if not secret_name:
        raise RuntimeError("RDS_SECRET_NAME not configured")

    try:
        response = secrets_client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        raise RuntimeError(f"Unable to retrieve secret: {e}") from e

    secret_str = response.get("SecretString")
    return json.loads(secret_str)

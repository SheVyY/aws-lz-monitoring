import boto3
import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def copy_objects(event, context):
    try:
        destination_bucket = os.environ['DESTINATION_BUCKET']
        source_bucket = os.environ['SOURCE_BUCKET']
        source_prefix = os.environ['SOURCE_PREFIX']
        destination_prefix = os.environ['DESTINATION_PREFIX']

        s3_client = boto3.client('s3')

        response = s3_client.list_objects_v2(Bucket=source_bucket, Prefix=source_prefix)
        objects = response.get('Contents', [])

        for obj in objects:
            source_key = obj['Key']
            destination_key = source_key.replace(source_prefix, destination_prefix, 1)

            try:
                copy_source = {'Bucket': source_bucket, 'Key': source_key}
                s3_client.copy_object(CopySource=copy_source, Bucket=destination_bucket, Key=destination_key)
                logger.info(f"Successfully copied {source_bucket}/{source_key} to {destination_bucket}/{destination_key}")
            except Exception as e:
                logger.error(f"Failed to copy {source_bucket}/{source_key} to {destination_bucket}/{destination_key}: {e}")
        
        return {"message": "Copy operation completed successfully."}

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise e

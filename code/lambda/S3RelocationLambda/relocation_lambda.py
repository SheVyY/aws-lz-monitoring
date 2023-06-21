import os
import logging
import boto3

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def lambda_handler(event, context):
    # Get the S3 bucket name and directory prefix from environment variables
    bucket_name = os.environ.get('BUCKET_NAME')
    directory_prefix = os.environ.get('DIRECTORY_PREFIX')
    destination_directory_prefix = os.environ.get('DESTINATION_DIRECTORY_PREFIX')

    try:
        # Find the latest directory
        latest_directory = find_latest_directory(bucket_name, directory_prefix)

        if latest_directory:
            logger.info(f"Latest directory: {latest_directory}")
            directory_contents = list_directory_contents(bucket_name, latest_directory)
            if directory_contents:
                logger.info("Directory contents:")
                for file in directory_contents:
                    logger.info(file)
                    if file.endswith('.csv'):
                        new_file_name = f"{destination_directory_prefix}lz_aggregated.csv"
                        copy_file(bucket_name, file, new_file_name)
                        logger.info(f"File '{file}' copied and renamed to '{new_file_name}'")
                    elif file.endswith('.csv.metadata'):
                        new_file_name = f"{destination_directory_prefix}lz.aggregated.csv.metadata"
                        copy_file(bucket_name, file, new_file_name)
                        logger.info(f"File '{file}' copied and renamed to '{new_file_name}'")
                return {
                    'statusCode': 200,
                    'body': {
                        'latest_directory': latest_directory,
                        'directory_contents': directory_contents
                    }
                }
            else:
                logger.info("Directory is empty.")
                return {
                    'statusCode': 200,
                    'body': {
                        'latest_directory': latest_directory,
                        'directory_contents': []
                    }
                }
        else:
            logger.info("No directories found.")
            return {
                'statusCode': 404,
                'body': "No directories found."
            }
    except Exception as e:
        logger.exception("An error occurred:")
        return {
            'statusCode': 500,
            'body': str(e)
        }


def find_latest_directory(bucket_name, directory_prefix):
    # Create an S3 client
    s3 = boto3.client('s3')

    # List the objects in the bucket
    response = s3.list_objects_v2(Bucket=bucket_name, Delimiter='/')
    directories = [obj['Prefix'] for obj in response.get('CommonPrefixes', [])]

    # Filter the directories by the specified prefix
    filtered_directories = [directory for directory in directories if directory.startswith(directory_prefix)]

    # Sort the directories by their timestamps in descending order
    sorted_directories = sorted(filtered_directories, reverse=True)

    return sorted_directories[0] if sorted_directories else None


def list_directory_contents(bucket_name, directory_path):
    # Create an S3 client
    s3 = boto3.client('s3')

    # List the objects in the directory
    response = s3.list_objects_v2(Bucket=bucket_name, Prefix=directory_path)

    files = [obj['Key'] for obj in response.get('Contents', []) if not obj['Key'].endswith('/')]
    return files


def copy_file(bucket_name, old_file_name, new_file_name):
    # Create an S3 client
    s3 = boto3.client('s3')

    # Copy the file with the new name
    s3.copy_object(Bucket=bucket_name, CopySource=f"{bucket_name}/{old_file_name}", Key=new_file_name)

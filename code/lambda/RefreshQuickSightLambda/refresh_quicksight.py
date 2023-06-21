import os
import boto3
import time
import calendar
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def find_dataset_id(dataset_name, aws_account_id, quicksight_region):
    client = boto3.client('quicksight', region_name=quicksight_region)

    try:
        response = client.list_data_sets(AwsAccountId=aws_account_id)

        for dataset in response.get('DataSetSummaries', []):
            if dataset.get('Name') == dataset_name:
                return dataset.get('DataSetId')

        return None
    except Exception as e:
        logger.error(f"An error occurred while finding the dataset ID: {str(e)}")
        return None

def refresh_dataset(dataset_name, aws_account_id, quicksight_region):
    dataset_id = find_dataset_id(dataset_name, aws_account_id, quicksight_region)

    if dataset_id:
        client = boto3.client('quicksight', region_name=quicksight_region)

        try:
            ingestion_id = str(calendar.timegm(time.gmtime()))
            client.create_ingestion(DataSetId=dataset_id, IngestionId=ingestion_id, AwsAccountId=aws_account_id)
            logger.info(f"Dataset refresh triggered for dataset {dataset_name}. Ingestion ID: {ingestion_id}")

            while True:
                response = client.describe_ingestion(DataSetId=dataset_id, IngestionId=ingestion_id, AwsAccountId=aws_account_id)
                ingestion_status = response['Ingestion']['IngestionStatus']
                
                if ingestion_status in ('INITIALIZED', 'QUEUED', 'RUNNING'):
                    time.sleep(5)  # Adjust sleep time according to your dataset size
                elif ingestion_status == 'COMPLETED':
                    row_info = response['Ingestion'].get('RowInfo', {})
                    rows_ingested = row_info.get('RowsIngested', 'Unknown')
                    rows_dropped = row_info.get('RowsDropped', 'Unknown')
                    ingestion_time = row_info.get('IngestionTimeInSeconds', 'Unknown')
                    ingestion_size = row_info.get('IngestionSizeInBytes', 'Unknown')
                    logger.info(f"Refresh completed for dataset {dataset_name}. RowsIngested: {rows_ingested}, RowsDropped: {rows_dropped}, IngestionTimeInSeconds: {ingestion_time}, IngestionSizeInBytes: {ingestion_size}")
                    return {
                        'statusCode': 200,
                        'body': f"Refresh completed for dataset {dataset_name}. RowsIngested: {rows_ingested}, RowsDropped: {rows_dropped}, IngestionTimeInSeconds: {ingestion_time}, IngestionSizeInBytes: {ingestion_size}"
                    }
                else:
                    logger.error(f"Refresh failed for dataset {dataset_name}! - Status: {ingestion_status}")
                    return {
                        'statusCode': 500,
                        'body': f"Refresh failed for dataset {dataset_name}! - Status: {ingestion_status}"
                    }
        except Exception as e:
            logger.error(f"An error occurred while refreshing the dataset: {str(e)}")
            return {
                'statusCode': 500,
                'body': f"An error occurred while refreshing the dataset {dataset_name} - {str(e)}"
            }
    else:
        logger.error("Dataset not found.")
        return {
            'statusCode': 404,
            'body': "Dataset not found"
        }

def lambda_handler(event, context):
    dataset_name = os.environ['DATASET_NAME']
    aws_account_id = os.environ['AWS_ACCOUNT_ID']
    quicksight_region = os.environ['QUICKSIGHT_REGION']

    return refresh_dataset(dataset_name, aws_account_id, quicksight_region)

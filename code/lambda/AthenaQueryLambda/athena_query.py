import os
import boto3
import logging
import time
from datetime import datetime

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def wait_for_query_completion(athena_client, query_execution_id):
    """
    Helper function to wait for the completion of an Athena query execution.
    It continuously polls the status of the query until it reaches a terminal state.
    """
    while True:
        response = athena_client.get_query_execution(QueryExecutionId=query_execution_id)
        status = response["QueryExecution"]["Status"]["State"]
        
        if status in ["SUCCEEDED", "FAILED", "CANCELLED"]:
            break
        
        time.sleep(1)  # Wait for 1 second before polling again

def lambda_handler(event, context):
    # Set the Athena configuration
    database = "cid_cur"
    table = "cur"
    query = f'SELECT * FROM "{database}"."{table}";'  # Query to be executed
    output_bucket = os.environ["OUTPUT_BUCKET_NAME"]  # S3 bucket name for query results
    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    s3_output_key = f"landing_zone_{timestamp}"  # Key for the S3 output location
    s3_output = f"s3://{output_bucket}/{s3_output_key}"  # S3 output location for query results

    # Create an Athena client
    athena_client = boto3.client("athena")

    try:
        # Start the Athena query execution
        response = athena_client.start_query_execution(
            QueryString=query,
            QueryExecutionContext={"Database": database},
            ResultConfiguration={"OutputLocation": s3_output}
        )

        # Get the QueryExecutionId
        query_execution_id = response["QueryExecutionId"]

        # Wait for the query to complete
        wait_for_query_completion(athena_client, query_execution_id)

        # Check if the query execution succeeded
        query_status = athena_client.get_query_execution(QueryExecutionId=query_execution_id)
        status = query_status["QueryExecution"]["Status"]["State"]

        if status == "SUCCEEDED":
            logger.info(f"Query execution successful: {query_execution_id}")

            # Wait for file metadata to propagate in S3
            time.sleep(5)

            # Check if the file was uploaded successfully
            s3_client = boto3.client("s3")
            try:
                response = s3_client.list_objects_v2(Bucket=output_bucket, Prefix=s3_output_key)
                if "Contents" in response:
                    result_message = "Query results saved successfully"
                    logger.info(result_message)
                    return {
                        "statusCode": 200,
                        "body": result_message
                    }
                else:
                    error_message = "Query results file not found in S3"
                    logger.error(error_message)
                    return {
                        "statusCode": 500,
                        "body": error_message
                    }
            except Exception as e:
                error_message = f"Error occurred while checking if query results file was uploaded: {str(e)}"
                logger.error(error_message)
                return {
                    "statusCode": 500,
                    "body": error_message
                }
        else:
            error_message = query_status["QueryExecution"]["Status"]["StateChangeReason"]
            logger.error(f"Query execution failed or was cancelled: {error_message}")
            return {
                "statusCode": 500,
                "body": f"Query execution failed or was cancelled: {error_message}"
            }
    except Exception as e:
        error_message = "An error occurred while executing the Athena query"
        logger.exception(error_message)
        return {
            "statusCode": 500,
            "body": error_message
        }

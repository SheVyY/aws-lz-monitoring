import pandas as pd
import json
import boto3
import os
import numpy as np

def lambda_handler(event, context):
    # S3 bucket and file configurations
    s3_bucket = os.environ['S3_BUCKET']
    lz_mapping_key = os.environ['LZ_MAPPING_KEY']
    lz_aggregated_key = os.environ['LZ_AGGREGATED_KEY']
    output_key = os.environ['OUTPUT_KEY']

    # Check if the lz_name_mapping.json file exists and is readable
    try:
        s3_client = boto3.client('s3')
        response = s3_client.get_object(Bucket=s3_bucket, Key=lz_mapping_key)
        lz_name_mapping = json.load(response['Body'])
    except Exception as e:
        return {
            'statusCode': 500,
            'body': f'Error: Failed to load lz_name_mapping.json from S3 - {str(e)}'
        }

    # Function to set lz_name and account_name
    def set_lz_name_and_account_name(df):
        # Convert the source_account_id and line_item_usage_account_id columns to strings
        source_landing_zones = df['source_account_id'].astype(str)
        source_account_names = df['line_item_usage_account_id'].astype(str)

        # Initialize empty lz_names and account_names lists
        lz_names = [np.nan] * len(df)
        account_names = [np.nan] * len(df)

        # Check if the source_landing_zones and source_account_names are present in the DataFrame
        source_landing_zone_present = df['source_account_id'].isin(lz_name_mapping.keys())
        source_account_name_present = df['line_item_usage_account_id'].isin(
            [account for lz in lz_name_mapping.values() for account in lz['accounts'].keys()])
        missing_lzs = source_landing_zones[~source_landing_zone_present].unique()
        missing_accounts = source_account_names[~source_account_name_present].unique()

        # Print a warning if some source_account_id or source_account_name is missing in the JSON file
        if missing_lzs.any():
            print(f"Warning: {len(missing_lzs)} source_account_id(s) not found in the JSON file: {', '.join(missing_lzs)}")
        if missing_accounts.any():
            print(f"Warning: {len(missing_accounts)} source_account_name(s) not found in the JSON file: {', '.join(missing_accounts)}")

        # Look up the lz_names and account_names for the source_landing_zones and source_account_names
        account_mappings = {}
        for lz, accounts in lz_name_mapping.items():
            account_mappings.update({(lz, account): (accounts['lz_name'], account_name) for account, account_name in accounts['accounts'].items()})

        for i, (lz, account) in enumerate(zip(source_landing_zones, source_account_names)):
            if source_landing_zone_present[i] and source_account_name_present[i]:
                lz_names[i], account_names[i] = account_mappings.get((lz, account), (np.nan, np.nan))

        # Create a DataFrame containing the lz_name and account_name columns
        result = pd.DataFrame({'lz_name': lz_names, 'account_name': account_names})
        return result

    # Read the lz_aggregated.csv file directly from S3 into a DataFrame
    try:
        obj = s3_client.get_object(Bucket=s3_bucket, Key=lz_aggregated_key)
        df = pd.read_csv(obj['Body'], dtype=str)
    except Exception as e:
        return {
            'statusCode': 500,
            'body': f'Error: Failed to read lz_aggregated.csv - {str(e)}'
        }

    # Apply the set_lz_name_and_account_name function to the DataFrame
    df[['lz_name', 'account_name']] = set_lz_name_and_account_name(df)

    # Write the DataFrame to a CSV file locally
    try:
        output_csv_path = '/tmp/lz_aggregated_with_lz_name.csv'
        df.to_csv(output_csv_path, index=False)
    except Exception as e:
        return {
            'statusCode': 500,
            'body': f'Error: Failed to write lz_aggregated_with_lz_name.csv - {str(e)}'
        }

    # Upload the file to S3
    try:
        s3_client.upload_file(output_csv_path, s3_bucket, output_key)
    except Exception as e:
        return {
            'statusCode': 500,
            'body': f'Error: Failed to upload file to S3 - {str(e)}'
        }

    # Delete the local file
    os.remove(output_csv_path)

    return {
        'statusCode': 200,
        'body': 'Successfully processed the lz_aggregated.csv file',
        's3_bucket': s3_bucket,
        's3_key': output_key
    }

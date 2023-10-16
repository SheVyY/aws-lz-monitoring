# Quicksight Monitoring Solution for Multiple Landing Zones

This repository contains the AWS SAM templates and documentation for the **Multi Landing Zones Monitoring Automation** solution.

## Overview

The **Multi Landing Zones Monitoring Automation** solution simplifies and streamlines the monitoring of data from multiple Landing Zones. By leveraging **AWS Step Functions**, **AWS Lambdas**, and **AWS EventBridge**, this solution automates the entire monitoring workflow, from data retrieval to data visualization in Quicksight.

## Solution Design

The solution is built and deployed using the **AWS SAM framework**, which enables easy management and deployment of serverless applications. Here's an overview of the solution's design:

1. **Trigger:** The workflow is triggered via **EventBridge Cron**, which schedules the execution of the monitoring process at a specified time (e.g., 2 AM UTC).

2. **Step Functions Workflow:** The EventBridge triggers a **Step Functions** workflow that coordinates the execution of various resources and functions. The workflow ensures the seamless flow of data through each step of the monitoring process.

   ![Monitoring Solution](./img/monitoring_diagram.png)

## State Machine Overview

The core of the solution is the **Step Functions state machine**, which consists of several states and transitions that automate the monitoring process. Each state represents a specific task or action to be performed. The overall flow of the state machine is as follows:

<img src="./img/state_machine.png" alt="State Machine Flow" width="800" height="800">

0. **Triggering the State Machine:** The state machine is triggered via **EventBridge cron** at a specified time.

## Explanation of the State Machine

1. **Fetch Data from Landing Zones (Lambda):** This state triggers a Lambda function (`S3ReplicationLambda`) to fetch data from all Cost Reports in the Landing Zones. The Lambda function retries the execution in case of specific errors, ensuring data retrieval.

2. **Safety Wait:** This state introduces a brief pause of 5 seconds before proceeding to the next state. It allows time for the crawler to start properly.

3. **Start CID Crawler (Glue):** In this state, the state machine triggers the `CidCrawler` Glue crawler using the `startCrawler` AWS SDK action. The crawler is responsible for extracting metadata and schema information from the data.

4. **Get CID Crawler (Glue):** This state retrieves the status of the `CidCrawler` Glue crawler using the `getCrawler` AWS SDK action. It checks the state and last crawl status of the crawler to determine the next step.

5. **Athena Proceed:** This state represents a decision point where the state machine checks if the `CidCrawler` is in the "READY" state and if the last crawl status is "SUCCEEDED". Based on the conditions, it either transitions to the "Wait for Crawler to Finish" state or proceeds to the "Query the Data and Upload CSV" state.

6. **Query the Data and Upload CSV (Lambda):** This state invokes a Lambda function (`AthenaQueryCSV`) to perform a query on the data and generate a CSV file. The Lambda function retries the execution in case of specific errors, ensuring data transformation.

7. **Rename / Move S3 Data (Lambda):** In this state, a Lambda function (`MoveRenameLZ`) is invoked to rename or move the S3 data. The function operates on the payload received from the previous lambda, allowing for data organization.

8. **Map and Transform Landing Zones Data (Lambda):** This state invokes a Lambda function (`Transform_LZ`) to map and transform the Landing Zones' data. The function operates on the payload received from the previous lambda, enabling data preparation for visualization.

9. **Refresh QuickSight DataSet (Lambda):** This state invokes a Lambda function (`DataSetRefresh`) to refresh the QuickSight DataSet with the transformed data. The function operates on the payload received from the previous lambda, ensuring the latest data is available for visualization.

10. **Wait for Crawler to Finish:** This state introduces a wait of 10 seconds before retrying the "Get CID Crawler" state. It provides a delay to allow the crawler to finish its operation before checking its status again.

## Quicksight Dashboard

<img src="./img/quicksight_dashboard.png" alt="Quicksight Dashboard" width="800">

The **QuickSight dashboard** is the main interface for monitoring the data from multiple Landing Zones. The transformed data is visualized and displayed on the dashboard, providing insights into various metrics and trends.

The solution provides pre-configured QuickSight dashboards that are automatically updated with the latest data during the monitoring process. The dashboards can be customized to display different visualizations, charts, and tables based on the specific monitoring requirements.

Users can access the QuickSight dashboard through the QuickSight web interface or embed it into other applications using QuickSight embedding capabilities. They can interact with the dashboard to explore the data, apply filters, and drill down into specific details.

The QuickSight monitoring dashboard provides a comprehensive view of the data from multiple Landing Zones, allowing users to track and analyze key metrics, identify anomalies, and make data-driven decisions.

## Deployment

To deploy the Multi Landing Zones Monitoring Automation solution, use the provided AWS SAM template and deploy it as a CloudFormation stack.

1. Clone the repository containing the solution's AWS SAM templates and documentation.

2. Navigate to the root directory of the cloned repository.

3. Open a terminal or command prompt and navigate to the root directory of the cloned repository.

4. Build the SAM application by executing the following command:

```bash
sam build
```

5.  Deploy the SAM application using the following command:

```bash
sam deploy --guided
```

This command will guide you through the deployment process and prompt for the necessary parameters. Provide the required inputs, such as stack name, AWS Region, and any other parameters defined in the SAM template.

Note: The deployment will take several minutes to complete.

Once the deployment is successful, the Multi Landing Zones Monitoring Automation solution will be up and running in your AWS account.

Nested Stacks
-------------

The Multi Landing Zones Monitoring Automation solution utilizes nested stacks to manage and deploy the individual Lambda functions. Each Lambda function is deployed as a separate stack, which allows for modular development and easier management of resources.

The following nested stacks are included in the deployment:

#### S3ReplicationStack

This stack deploys the `S3ReplicationLambda`, which is responsible for fetching data from all Cost Reports in the Landing Zones. The Lambda function ensures data retrieval and retries the execution in case of specific errors.

#### S3RelocationStack

This stack deploys the `S3RelocationLambda`, which can be used to rename or move the S3 data. The Lambda function operates on the payload received from the previous Lambda, allowing for flexible data organization based on specific requirements.

#### S3TransformStack

This stack deploys the `S3TransformLambda`, which is responsible for mapping and transforming the Landing Zones' data. The Lambda function operates on the payload received from the previous Lambda, enabling data preparation for visualization.

#### AthenaQueryStack

This stack deploys the `AthenaQueryLambda`, which performs a query on the data fetched from the Landing Zones. The Lambda function generates a CSV file containing the query results, ensuring data transformation for further processing.

#### RefreshQuickSightStack

This stack deploys the `RefreshQuickSightLambda`, which is responsible for refreshing the QuickSight DataSet with the transformed data. The Lambda function operates on the payload received from the previous Lambda, ensuring the latest data is available for visualization in QuickSight.

Conclusion
----------

Once the Multi Landing Zones Monitoring Automation solution is successfully deployed, it will orchestrate the monitoring workflow for data retrieval, transformation, and visualization. The Step Functions state machine will coordinate the execution of different resources and Lambdas, ensuring a seamless flow of data through each step.

The solution provides a pre-configured QuickSight dashboard that is automatically updated with the latest data during the monitoring process. You can customize the dashboard to display different visualizations, charts, and tables based on your specific monitoring requirements.

By leveraging this solution, you can simplify and streamline the monitoring of data from multiple Landing Zones, enabling you to track key metrics, identify trends, and make data-driven decisions.

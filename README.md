# Landing Zones Monitoring Automation State Machine

This repository contains the AWS SAM templates and documentation for the Multi Landing Zones Monitoring Automation solution.

## Overview

The Landing Zones Monitoring Automation Monitoring solution is built using AWS Step Functions, AWS Lambdas and AWS EventBridge. It coordinates the execution of all resources and functions.

## How it works

1) The workflow is trigger via Eventbridge Cron every day at X UTC
2) The Eventbridge start the Step Function workflow that executes the whole automation

![Monitoring_solution](./img/monitoring_diagram.png)

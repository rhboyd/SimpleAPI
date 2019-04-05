# Simple API (WORK IN PROGRESS)

This is a CloudFormation Macro that simplifies creating API Gateway integrations

```bash
.
├── README.md                   <-- You are here
├── event.json                  <-- an event, probably in json format
├── lambda                      <-- Source code for a lambda function
│   ├── __init__.py             <-- Never really knew what this was for
│   ├── simple_api.py           <-- Lambda function code
│   ├── requirements.txt        <-- Requirements, probably in text format
├── template.yaml               <-- SAM Template
└── tests                       <-- Unit tests, lol
    └── unit
        ├── __init__.py
        └── test_handler.py
```

## Requirements

* AWS CLI already configured with Administrator permission
* [Python 3 installed](https://www.python.org/downloads/)
* [Docker installed](https://www.docker.com/community-edition)

## Setup process

idk, git pull?

### Local development

**Invoking function locally using a local sample payload**

```bash
sam build --use-container -b ./build/ -t ./template.yaml
sam local invoke -t ./build/template.yaml -e event.json SimpleAPIMacroFunction
```

## Packaging and deployment

This is used to deploy the macro to your AWS Account. You need to do this before you can transform 'real' CloudFormation templates.

```bash
sam build --use-container -b ./build/ -t template.yaml \
&& sam package --s3-bucket [your bucket name here] --template-file build/template.yaml --output-template-file build/packaged.yaml --profile workshop\
&& aws cloudformation deploy --template-file build/packaged.yaml --stack-name [your stack name here]  --capabilities CAPABILITY_NAMED_IAM --profile workshop
```

## Deploying Templates to be modified

```bash
# A DynamoDB PutItem example
aws cloudformation deploy --stack-name api-macro-dynamodb-test --template-file test_templates/dynamo_db_test.yaml --capabilities CAPABILITY_IAM --profile workshop
# A EC2 VPC Example
aws cloudformation deploy --stack-name api-vpc-test --template-file test_templates/vpc_test.yaml --capabilities CAPABILITY_IAM --profile workshopaws cloudformation deploy --stack-name api-vpc-test --template-file test_templates/vpc_test.yaml --capabilities CAPABILITY_IAM --profile workshop
```

## Fetch, tail, and filter Lambda function logs

To simplify troubleshooting, SAM CLI has a command called sam logs. sam logs lets you fetch logs generated by your Lambda function from the command line. In addition to printing the logs on the terminal, this command has several nifty features to help you quickly find the bug.

`NOTE`: This command works for all AWS Lambda functions; not just the ones you deploy using SAM.

```bash
sam logs -n HelloWorldFunction --stack-name sam-app --tail
```

You can find more information and examples about filtering Lambda function logs in the [SAM CLI Documentation](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-logging.html).

## Testing

Next, we install test dependencies and we run `pytest` against our `tests` folder to run our initial unit tests:

```bash
pip install pytest pytest-mock --user
python -m pytest tests/ -v
```

## Cleanup

In order to delete our Serverless Application recently deployed you can use the following AWS CLI Command:

```bash
aws cloudformation delete-stack --stack-name sam-app
```

## Bringing to the next level

Here are a few things you can try to get more acquainted with building serverless applications using SAM:

### Step-through debugging

* **[Enable step-through debugging docs for supported runtimes]((https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-using-debugging.html))**

Next, you can use AWS Serverless Application Repository to deploy ready to use Apps that go beyond hello world samples and learn how authors developed their applications: [AWS Serverless Application Repository main page](https://aws.amazon.com/serverless/serverlessrepo/)

# Appendix

## SAM and AWS CLI commands

All commands used throughout this document

```bash
# Generate event.json via generate-event command
sam local generate-event apigateway aws-proxy > event.json

# Invoke function locally with event.json as an input
sam local invoke HelloWorldFunction --event event.json

# Run API Gateway locally
sam local start-api

# Create S3 bucket
aws s3 mb s3://BUCKET_NAME

# Package Lambda function defined locally and upload to S3 as an artifact
sam package \
    --output-template-file packaged.yaml \
    --s3-bucket REPLACE_THIS_WITH_YOUR_S3_BUCKET_NAME

# Deploy SAM template as a CloudFormation stack
sam deploy \
    --template-file packaged.yaml \
    --stack-name sam-app \
    --capabilities CAPABILITY_IAM

# Describe Output section of CloudFormation stack previously created
aws cloudformation describe-stacks \
    --stack-name sam-app \
    --query 'Stacks[].Outputs[?OutputKey==`HelloWorldApi`]' \
    --output table

# Tail Lambda function Logs using Logical name defined in SAM Template
sam logs -n HelloWorldFunction --stack-name sam-app --tail
```


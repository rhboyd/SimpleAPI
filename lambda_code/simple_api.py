from collections import ChainMap
import os
from botocore.model import ServiceModel
from botocore.loaders import Loader
from botocore.serialize import create_serializer
from botocore.parsers import create_parser
from botocore.awsrequest import AWSRequest
from botocore import session

REGION = os.environ['AWS_REGION']


def get_endpoint(service_name):
    this_session = session.get_session()
    client = this_session.create_client(service_name, region_name=REGION)
    return client.meta.endpoint_url


def create_request():
    pass


def create_response():
    pass


def integration_template():
    return {
        "IntegrationHttpMethod": "",
        "IntegrationResponses": [
            {
                "StatusCode": 200,
                "ResponseTemplates": {
                    "application/json": ''
                },
            },
            {"StatusCode": 400, "SelectionPattern": "4[0-9]{2}"},
            {"StatusCode": 500, "SelectionPattern": "5[0-9]{2}"}
        ],
        "PassthroughBehavior": "WHEN_NO_MATCH",
        "RequestParameters": {},
        "RequestTemplates": {"application/json": ""},
        "Type": "AWS",
        "Uri": '!Sub \"arn:aws:apigateway:${AWS::Region}:dynamodb:action/Query\"'
    }


class InvalidTypeException(Exception):
    pass


def handle_method(fragment):
    if fragment["Type"] != "AWS::ApiGateway::Method":
        response_string = "Macro only supports \"AWS::ApiGateway::Method\", user supplied {}"
        raise InvalidTypeException(response_string.format(fragment["Type"]))

    service_name = fragment["Properties"]["Integration"].pop("Service").lower()
    action = fragment["Properties"]["Integration"].pop("Action")
    response_maps = fragment["Properties"]["Integration"].pop("ResponseMaps")
    try:
        fragment.pop("Fn::Transform")
    except:
        pass

    loader = Loader()
    service_description = loader.load_service_model(service_name=service_name, type_name='service-2')
    service_model = ServiceModel(service_description)
    protocol = service_model.protocol
    op_model = service_model.operation_model(action["Name"])

    request_parameters = action["Parameters"]
    params = dict(ChainMap(*request_parameters))
    print("params: {}".format(params))
    serializer = create_serializer(protocol)
    response_parser = create_parser(protocol)

    print(service_model.protocol)
    request = serializer.serialize_to_request(params, op_model)
    request_object = AWSRequest(
        method=request['method'],
        url=get_endpoint(service_model.service_name),
        data=request['body'],
        headers=request['headers'])

    X = request_object.prepare()

    print("Raw request: {}".format(request))
    print("Prepared request: {}".format(X))

    integration = fragment["Properties"]["Integration"]
    new_integration = integration_template()

    # Copy the existing values to the new template
    for entry in integration.keys():
        new_integration[entry] = integration[entry]

    # Add headers to cfn template
    if X.headers is not None and callable(getattr(X.headers, "keys", None)):
        for header in X.headers.keys():
            if header.lower() != 'Content-Length'.lower():
                new_integration["RequestParameters"].update({"integration.request.header.{}".format(header): "'{}'".format(X.headers[header])})

    # Add Query Strings to cfn template
    if 'query_string' in request and callable(getattr(request['query_string'], "keys", None)):
        for query in request['query_string'].keys():
            new_integration["RequestParameters"].update({"integration.request.querystring.{}".format(query): "'{}'".format(request['query_string'][query])})

    # Set the body
    new_integration["RequestTemplates"]["application/json"] = str(X.body, "utf-8") if X.body else ''
    new_integration["Uri"] = ":".join([
        "arn",
        "aws",
        "apigateway",
        REGION,
        service_model.endpoint_prefix,
        "path/" + request["url_path"]
    ])
    new_integration["IntegrationHttpMethod"] = X.method

    fragment["Properties"]["Integration"] = new_integration
    print(fragment)
    return fragment


def lambda_handler(event, _context):
    status = "success"
    fragment = event["fragment"]
    try:
        fragment = handle_method(fragment)
        print("transformed fragment: {}".format(fragment))
    except InvalidTypeException as e:
        print("Invalid type supplied: {}".format(e))
        status = "failure"

    return {
        "requestId": event["requestId"],
        "status": status,
        "fragment": fragment,
    }

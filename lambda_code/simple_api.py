from collections import ChainMap
import os
from botocore.model import ServiceModel
from botocore.loaders import Loader
from botocore.serialize import create_serializer

REGION = os.environ['AWS_REGION']

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
    op_model = service_model.operation_model(action["Name"])
    request_parameters = action["Parameters"]
    params = dict(ChainMap(*request_parameters))
    serializer = create_serializer(service_model.protocol)
    request = serializer.serialize_to_request(params, op_model)
    print("Request: {}".format(request))

    integration = fragment["Properties"]["Integration"]
    new_integration = integration_template()

    for entry in integration.keys():
        new_integration[entry] = integration[entry]

    for header in request['headers'].keys():
        new_integration["RequestParameters"].update({"integration.request.header.{}".format(header): "'{}'".format(request['headers'][header])})
    new_integration["RequestTemplates"]["application/json"] = request["body"].decode("utf-8")
    new_integration["Uri"] = ":".join([
        "arn",
        "aws",
        "apigateway",
        REGION,
        service_model.endpoint_prefix,
        "path/" + request["url_path"]
    ])
    new_integration["IntegrationHttpMethod"] = request["method"]

    fragment["Properties"]["Integration"] = new_integration
    print(fragment)
    return fragment


def lambda_handler(event, _context):
    # print("event: {}".format(event))
    status = "success"
    fragment = event["fragment"]
    try:
        fragment = handle_method(fragment)
    except InvalidTypeException as e:
        print("Invalid type supplied: {}".format(e))
        status = "failure"

    return {
        "requestId": event["requestId"],
        "status": status,
        "fragment": fragment,
    }

import json

import pytest

from lambda_code import simple_api


@pytest.fixture()
def apigw_event():
    """ Generates API GW Event"""

    return {
        "region": "us-east-1",
        "accountId": "053954707544",
        "fragment": {
            "Type": "AWS::ApiGateway::Resource",
            "Fn::Transform": [
                {
                    "Name": "SimpleAPI"
                }
            ],
            "Properties": {
                "ParentId": "SimpleResource",
                "PathPart": "{queryId}",
                "RestApiId": "RestAPI"
            }
        }
    }


def test_lambda_handler(apigw_event, mocker):

    ret = simple_api.lambda_handler(apigw_event, "")
    data = json.loads(ret["body"])

    assert ret["statusCode"] == 200
    assert "message" in ret["body"]
    assert data["message"] == "hello world"
    # assert "location" in data.dict_keys()

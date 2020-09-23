import json

from os import getenv
from slack import WebClient

SLACK_API_TOKEN = getenv("SLACK_API_TOKEN")
SLACK_CHANNEL = getenv("SLACK_CHANNEL")

if not (SLACK_API_TOKEN and
        SLACK_CHANNEL):
    raise EnvironmentError("Check your env variables. Some are missing")


client = WebClient(token=SLACK_API_TOKEN)


def dispatcher(event, context):
    payload = json.loads(event["body"])

    result = payload["deploymentResult"]
    msg_ts = payload["msgId"]

    if "success" == result:
        client.reactions_add(
            channel=SLACK_CHANNEL,
            timestamp=msg_ts,
            name="heavy_check_mark")
    elif "fail" == result:
        client.reactions_add(
            channel=SLACK_CHANNEL,
            timestamp=msg_ts,
            name="x")
    else:
        return {"statusCode": 400, "body": "fuckup"}

    return {"statusCode": 200, "body": ""}

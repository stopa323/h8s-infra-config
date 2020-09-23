import json
import requests

from os import getenv
from slack import WebClient
from typing import Optional
from urllib.parse import unquote

SLACK_API_TOKEN = getenv("SLACK_API_TOKEN")
SLACK_CHANNEL = getenv("SLACK_CHANNEL")
GITHUB_TOKEN = getenv("GITHUB_TOKEN")

if not (SLACK_API_TOKEN and
        SLACK_CHANNEL and
        GITHUB_TOKEN):
    raise EnvironmentError("Check your env variables. Some are missing")


client = WebClient(token=SLACK_API_TOKEN)


class SlackSubmission:
    """Parser for view submissions comming from Slack."""

    def __init__(self, payload: dict):
        self._p = payload
        self._v = SlackSubmission.Values(payload)

    @property
    def user(self):
        return self._p["user"]["username"]

    @property
    def values(self):
        return self._v

    def env_create_requested(self) -> bool:
        return "id-deploy-environment-modal" == self._p["view"]["callback_id"]

    def env_destroy_requested(self) -> bool:
        return "id-destroy-environment-modal" == self._p["view"]["callback_id"]

    class Values:

        def __init__(self, payload: dict):
            self._v = payload["view"]["state"]["values"]

        def _get_radio_button_value(self, rb_val):
            value = rb_val["selected_option"]["value"]
            return value

        @property
        def environment(self):
            rb_val = self._v["var-environment"]["aid-environment"]
            env = self._get_radio_button_value(rb_val)
            return env

        @property
        def horreum_image_tag(self):
            body = self._v["var-horreum-image-tag"]["aid-horreum-image-tag"]
            image_tag = body["value"]
            return image_tag


class GithubClient:

    HEADERS = {
        "accept": "application/vnd.github.v3+json",
        "Authorization": f"token {GITHUB_TOKEN}"
    }
    URL = "https://api.github.com"

    def __init__(self, submission: SlackSubmission):
        self._s = submission

    def create_deployment(self, msg_ts):
        url = f"{self.URL}/repos/stopa323/h8s-infra-config/deployments"
        payload = {
            "auto_merge": False,
            "environment": self._s.values.environment,
            "payload": {
                "env": {
                    "horreum-image-tag": self._s.values.horreum_image_tag,
                },
                "msg_ts": msg_ts
            },
            "ref": "bob-bot-dev",
            "required_contexts": [],
            "task": "deploy-environment"
        }

        response = requests.post(url, json=payload, headers=self.HEADERS)
        response.raise_for_status()

    def destroy_deployment(self, msg_ts):
        url = f"{self.URL}/repos/stopa323/h8s-infra-config/deployments"
        payload = {
            "auto_merge": False,
            "environment": self._s.values.environment,
            "payload": {
                "msg_ts": msg_ts
            },
            "ref": "bob-bot-dev",
            "required_contexts": [],
            "task": "destroy-environment"
        }

        response = requests.post(url, json=payload, headers=self.HEADERS)
        response.raise_for_status()


def print_env_create_requested(sub: SlackSubmission) -> str:
    """Prints message that confirms env-create deployment was created."""
    blocks = [
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f":construction: Creating environment "
                            f"`{sub.values.environment}` "
                            f"for @{sub.user}"
                }
            ]
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"*HORREUM SERVICE*\ndocker-image-tag: "
                            f"`{sub.values.horreum_image_tag}`"
                }
            ]
        }
    ]
    response = client.chat_postMessage(
        channel=SLACK_CHANNEL, blocks=blocks, link_names=1)
    return response.data["ts"]


def print_env_destroy_requested(sub: SlackSubmission) -> str:
    blocks = [
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f":recycle: Hammering down "
                            f"`{sub.values.environment}` environment for "
                            f"@{sub.user}"
                }
            ]
        }
    ]
    response = client.chat_postMessage(
        channel=SLACK_CHANNEL, blocks=blocks,link_names=1)
    return response.data["ts"]


def view_submissions_dispatcher(payload):
    if not ("view_submission" == payload.get("type")):
        return build_response(400, "Non-submission payload received on "
                                   "dispatcher endpoint")

    submission = SlackSubmission(payload)
    github = GithubClient(submission)

    if submission.env_create_requested():
        msg_ts = print_env_create_requested(submission)
        github.create_deployment(msg_ts)
    elif submission.env_destroy_requested():
        msg_ts = print_env_destroy_requested(submission)
        github.destroy_deployment(msg_ts)
    else:
        return build_response(400, "Unknown view submission")

    return build_response()


def dispatcher(event, context):
    try:
        body = event["body"]

        if event["isBase64Encoded"]:
            from base64 import b64decode
            body = b64decode(body).decode("utf-8")

        unquoted_body = unquote(body)
        str_payload = unquoted_body.split("payload=")[1]
        payload = json.loads(str_payload)
        return view_submissions_dispatcher(payload)
    except Exception as exc:
        print(exc)
        build_response(500, "Things break sometimes. Check out log files.")


def build_response(status_code: Optional[int] = 200,
                   message: Optional[str] = ""):
    if 200 == status_code:
        body = ""
    else:
        body = {"ok": False, "error": message}
    response = {"statusCode": status_code, "body": body}
    return response

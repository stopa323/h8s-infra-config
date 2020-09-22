from typing import Optional

from slack import WebClient
from os import getenv

SLACK_API_TOKEN = getenv("SLACK_API_TOKEN")
SLACK_CHANNEL = getenv("SLACK_CHANNEL")

if not (SLACK_API_TOKEN and
        SLACK_CHANNEL):
    raise EnvironmentError("Check your env variables. Some are missing")


client = WebClient(token=SLACK_API_TOKEN)


class SlackCommand:
    """Parser for view request messages coming from Slack."""

    def __init__(self, request):
        self._r = request

    @property
    def name(self):
        return self._r["text"]

    @property
    def trigger_id(self):
        return self._r["trigger_id"]

    @property
    def user_id(self):
        return self._r["user_id"]

    def is_deploy(self):
        return "deploy" == self.name

    def is_destroy(self):
        return "destroy" == self.name


def print_help(cmd: SlackCommand):
    """Prints usage message visible only to user that invoked command."""
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"Your command `{cmd.name}` is "
                        f"fucked - I can't build it :rage: \nHere is what "
                        f"I can do:"
            }
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": "`deploy` - Create new environment"
                },
                {
                    "type": "mrkdwn",
                    "text": "`destroy` - Destroy existing environment"
                }
            ]
        }
    ]

    client.api_call(
        "chat.postEphemeral",
        params={
            "channel": SLACK_CHANNEL,
            "blocks": blocks,
            "user": cmd.user_id})


def show_deploy_modal(cmd: SlackCommand):
    view = {
        "type": "modal",
        "title": {
            "type": "plain_text",
            "text": "Deploy environment"
        },
        "submit": {
            "type": "plain_text",
            "text": "Deploy"
        },
        "close": {
            "type": "plain_text",
            "text": "Cancel"
        },
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "plain_text",
                    "text": "Adjust parameters to customize your deployment."
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "*GLOBAL*"
                    }
                ]
            },
            {
                "type": "input",
                "block_id": "var-environment",
                "element": {
                    "type": "radio_buttons",
                    "action_id": "aid-environment",
                    "initial_option": {
                        "text": {
                            "type": "plain_text",
                            "text": "Staging"
                        },
                        "value": "staging"
                    },
                    "options": [
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "Staging"
                            },
                            "value": "staging"
                        }
                    ]
                },
                "label": {
                    "type": "plain_text",
                    "text": "environment"
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "*HORREUM SERVICE*"
                    }
                ]
            },
            {
                "type": "input",
                "block_id": "var-horreum-image-tag",
                "element": {
                    "type": "plain_text_input",
                    "action_id": "aid-horreum-image-tag",
                    "initial_value": "0.2.0",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Enter tag of Docker image"
                    }
                },
                "label": {
                    "type": "plain_text",
                    "text": "image-tag"
                }
            }
        ],
        "callback_id": "id-deploy-environment-modal"
    }
    client.views_open(trigger_id=cmd.trigger_id, view=view)


def show_destroy_modal(cmd: SlackCommand):
    view = {
        "type": "modal",
        "title": {
            "type": "plain_text",
            "text": "Destroy environment"
        },
        "submit": {
            "type": "plain_text",
            "text": "Destroy"
        },
        "close": {
            "type": "plain_text",
            "text": "Cancel"
        },
        "blocks": [
            {
                "type": "input",
                "block_id": "var-environment",
                "element": {
                    "type": "radio_buttons",
                    "action_id": "aid-environment",
                    "initial_option": {
                        "text": {
                            "type": "plain_text",
                            "text": "Staging"
                        },
                        "value": "staging"
                    },
                    "options": [
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "Staging"
                            },
                            "value": "staging"
                        }
                    ]
                },
                "label": {
                    "type": "plain_text",
                    "text": "Select environment to destroy"
                }
            }
        ],
        "callback_id": "id-destroy-environment-modal"
    }
    client.views_open(trigger_id=cmd.trigger_id, view=view)


def command_dispatcher(form_body: dict):
    try:
        command = SlackCommand(form_body)

        if command.is_deploy():
            show_deploy_modal(command)
        elif command.is_destroy():
            show_destroy_modal(command)
        else:
            print_help(command)
    except KeyError as exc:
        print(exc)
        return build_response(400, str(exc))

    return build_response()


def dispatcher(event, context):
    try:
        body = event["body"]

        if event["isBase64Encoded"]:
            from base64 import b64decode
            body = b64decode(body).decode("utf-8")

        # Convert header form string to dictionary
        form = {}
        form_arguments = body.split("&")
        for arg in form_arguments:
            key, value = arg.split("=")
            form[key] = value

        return command_dispatcher(form)
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

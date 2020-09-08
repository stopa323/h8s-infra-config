import requests

from flask import Flask, request, json, Response
from slack import WebClient
from os import getenv

SLACK_API_TOKEN = getenv("SLACK_API_TOKEN")
SLACK_CHANNEL = getenv("SLACK_CHANNEL")
FLASK_PORT = getenv("FLASK_PORT")
GITHUB_TOKEN = getenv("GITHUB_TOKEN")

if not (SLACK_API_TOKEN and SLACK_CHANNEL and FLASK_PORT and GITHUB_TOKEN):
    raise EnvironmentError("Check your env variables. Some are missing")

app = Flask(__name__)
client = WebClient(token=SLACK_API_TOKEN)


class GithubClient:

    HEADERS = {
        "accept": "application/vnd.github.v3+json",
        "Authorization": f"token {GITHUB_TOKEN}"
    }
    URL = "https://api.github.com"

    def __init__(self, form):
        self._f = form

    def create_deployment(self, msg_ts):
        url = f"{self.URL}/repos/stopa323/h8s-infra-config/deployments"
        payload = {
            "auto_merge": False,
            "environment": self._f.view.values.environment,
            "payload": {
                "env": {
                    "horreum-image-tag": self._f.view.values.horreum_image_tag,
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
            "environment": self._f.view.values.environment,
            "payload": {
                "msg_ts": msg_ts
            },
            "ref": "bob-bot-dev",
            "required_contexts": [],
            "task": "destroy-environment"
        }

        response = requests.post(url, json=payload, headers=self.HEADERS)
        response.raise_for_status()


class SlackForm:
    """Parser for messages incoming from slackbot."""

    def __init__(self, request):
        if payload := request.form.get("payload"):
            self._c = None
            self._v = SlackForm.View(payload)
        else:
            self._c = SlackForm.Command(request)
            self._v = None

    @property
    def command(self):
        return self._c

    @property
    def view(self):
        return self._v

    class Command:

        def __init__(self, request):
            self._r = request

        @property
        def name(self):
            return self._r.form["text"]

        @property
        def trigger_id(self):
            return self._r.form["trigger_id"]

        @property
        def user_id(self):
            return self._r.form["user_id"]

        def is_deploy(self):
            return "deploy" == self.name

        def is_destroy(self):
            return "destroy" == self.name

    class View:

        def __init__(self, payload):
            self._p = json.loads(payload)

            if self.is_submission():
                self._v = SlackForm.View.Values(self._p["view"]["state"]["values"])
            else:
                self._v = None

        @property
        def user(self):
            return self._p["user"]["username"]

        @property
        def values(self):
            return self._v

        def is_submission(self):
            return "view_submission" == self._p["type"]

        def is_env_deploy_submission(self):
            return (self.is_submission() and
                    "id-deploy-environment-modal" == self._p["view"]["callback_id"])

        def is_env_destroy_submission(self):
            return (self.is_submission() and
                    "id-destroy-environment-modal" == self._p["view"]["callback_id"])

        class Values:

            def __init__(self, values):
                self._v = values

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


class SlackMessenger:
    """Manager for sending messages to Slack channel."""

    def __init__(self, form: SlackForm):
        self._f = form

    def print_help(self):
        """Prints usage message visible only to user that invoked command."""
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Your command `{self._f.command.name}` is "
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
                "user": self._f.command.user_id})

    def print_env_create_requested(self):
        """Prints message that confirms env-create deployment was created."""
        blocks = [
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f":male-construction-worker: Hello there. "
                                f"@{self._f.view.user} demanded deployment ASAP"
                    }
                ]
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": "*Status*: `in-progress` :truck:"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Environment*: "
                                f"`{self._f.view.values.environment}`"
                    }
                ]
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"*HORREUM SERVICE*\ndocker-image-tag: "
                                f"`{self._f.view.values.horreum_image_tag}`"
                    }
                ]
            }
        ]
        response = client.chat_postMessage(
            channel=SLACK_CHANNEL, blocks=blocks, link_names=1)
        return response.data["ts"]

    def print_env_destroy_requested(self):
        blocks = [
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f":recycle: Hammering down `{self._f.view.values.environment}` environment for @{self._f.view.user}"
                    }
                ]
            }
        ]
        response = client.chat_postMessage(
            channel=SLACK_CHANNEL, blocks=blocks,link_names=1)
        return response.data["ts"]

    def show_deploy_modal(self):
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
        client.views_open(trigger_id=self._f.command.trigger_id, view=view)

    def show_destroy_modal(self):
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
        client.views_open(trigger_id=self._f.command.trigger_id, view=view)


@app.route("/", methods=["POST"])
def command_dispatcher():
    form = SlackForm(request)
    if not form.command:
        return Response(status=400, response="Non-command payload received on "
                                             "command-dispatcher endpoint")

    messenger = SlackMessenger(form)

    if form.command.is_deploy():
        messenger.show_deploy_modal()
    elif form.command.is_destroy():
        messenger.show_destroy_modal()
    else:
        messenger.print_help()

    return Response(status=200)


@app.route("/submissions", methods=["POST"])
def view_submissions_dispatcher():
    form = SlackForm(request)
    if not form.view:
        return Response(status=400,
                        response="Non-submission payload received on "
                                 "view-submission-dispatcher endpoint")

    messenger = SlackMessenger(form)
    github = GithubClient(form)

    if form.view.is_env_deploy_submission():
        msg_ts = messenger.print_env_create_requested()
        github.create_deployment(msg_ts)
    elif form.view.is_env_destroy_submission():
        msg_ts = messenger.print_env_destroy_requested()
        github.destroy_deployment(msg_ts)
    else:
        return Response(status=400,
                        response="Unknown view submission")

    return Response()


@app.route("/updates/<message_ts>", methods=["POST"])
def updates_dispatcher(message_ts):
    result = request.json.get("deploymentResult")

    if "success" == result:
        client.reactions_add(
            channel=SLACK_CHANNEL,
            timestamp=message_ts,
            name="heavy_check_mark")
    elif "fail" == result:
        client.reactions_add(
            channel=SLACK_CHANNEL,
            timestamp=message_ts,
            name="x")
    else:
        return Response(status=400, response=f"Unknown result: {result}")

    return Response(status=200, response="Ok")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=FLASK_PORT)

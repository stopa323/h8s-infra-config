from flask import Flask, request, json, Response
from slack import WebClient
from os import getenv

SLACK_API_TOKEN = getenv("SLACK_API_TOKEN")
SLACK_CHANNEL = getenv("SLACK_CHANNEL")
FLASK_PORT = getenv("FLASK_PORT")

if not (SLACK_API_TOKEN and SLACK_CHANNEL and FLASK_PORT):
    raise EnvironmentError("Check your env variables. Some are missing")

DEPLOY_MODAL = {
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
         "type": "input",
         "block_id": "var-environment",
         "element": {
            "type": "radio_buttons",
            "action_id": "aid-environment",
            "options": [
               {
                  "text": {
                     "type": "plain_text",
                     "text": "Staging (QA testing)"
                  },
                  "value": "staging"
               }
            ]
         },
         "label": {
            "type": "plain_text",
            "text": "Environment"
         }
      },
      {
         "type": "divider"
      },
      {
         "type": "section",
         "text": {
            "type": "mrkdwn",
            "text": "*Horreum service*"
         }
      },
      {
         "type": "input",
         "block_id": "var-horreum-image-tag",
         "element": {
            "type": "plain_text_input",
            "action_id": "aid-horreum-image-tag"
         },
         "label": {
            "type": "plain_text",
            "text": "Docker image tag"
         }
      }
   ]
}

app = Flask(__name__)
client = WebClient(token=SLACK_API_TOKEN)


def show_deploy_modal():
   trigger_id = request.form["trigger_id"]
   client.views_open(trigger_id=trigger_id, view=DEPLOY_MODAL)


def show_destroy_modal():
   print("DESTROY")


def print_help():
   blocks = [
      {
         "type": "section",
         "text": {
            "type": "mrkdwn",
            "text": f"Your command `{request.form['text']}` is fucked -"
                  f" I can't build it :rage: \nHere is what I can do:"
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
         "user": request.form["user_id"]})


@app.route("/", methods=["POST"])
def root_dispatcher():
   command = request.form["text"]
   if "deploy" == command:
      show_deploy_modal()
   elif "destroy" == command:
      show_destroy_modal()
   else:
      print_help()

   return Response()


def get_radio_button_value(var_body):
   value = var_body["selected_option"]["value"]
   return value


def get_environment(values):
   body = values["var-environment"]["aid-environment"]
   environment = get_radio_button_value(body)
   return environment


def get_horreum_image_tag(values):
   body = values["var-horreum-image-tag"]["aid-horreum-image-tag"]
   horreum_image_tag = body["value"]
   return horreum_image_tag


@app.route("/submissions", methods=["POST"])
def interactions_handler():
   payload = json.loads(request.form["payload"])
   values = payload["view"]["state"]["values"]

   print(get_environment(values))
   print(get_horreum_image_tag(values))

   return Response()


if __name__ == "__main__":
   app.run(host="127.0.0.1", port=FLASK_PORT)

import argparse
import base64
import datetime
import logging
import mimetypes
import os
import os.path
from pathlib import Path
import pickle
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.utils import COMMASPACE, formatdate
from email import encoders
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient import errors
from googleapiclient.discovery import build
from ReportWriter import *


SUBJECT = "SkySight Roof Report™: " + ADDRESS
BODY = """Good TIMEOFDAY,

Attached is your SkySight Roof Report™ for ADDRESS. Your payment of $12 will be processed within 24 hours of completion of the report. Please reach out if you have any questions or concerns.

Thank you for using SkySight!
The SkySight Team
skysightdata.com

Follow us on:
Facebook - https://www.facebook.com/SkySightData/
Instagram - https://www.instagram.com/SkySightData/
Twitter - https://twitter.com/SkySightData
"""

dt = datetime.datetime.now()

if dt.hour < 12:
  tod = "morning"
elif dt.hour < 18:
  tod = "afternoon"
else:
  tod = "evening"

BODY = BODY.replace("TIMEOFDAY", tod)
BODY = BODY.replace("ADDRESS", ADDRESS)


def get_service():
    """Gets an authorized Gmail API service instance.

    Returns:
        An authorized Gmail API service instance..
    """

    # If modifying these scopes, delete the file token.pickle.
    SCOPES = [
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.send'
    ]

    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('gmail', 'v1', credentials=creds, cache_discovery=False)

    return service

def send_message(service, sender, message):
  """Send an email message.

  Args:
    service: Authorized Gmail API service instance.
    user_id: User's email address. The special value "me"
    can be used to indicate the authenticated user.
    message: Message to be sent.

  Returns:
    Sent Message.
  """
  try:
    sent_message = (service.users().messages().send(userId="me", body=message)
               .execute())
    logging.info('Message Id: %s', sent_message['id'])
    return sent_message
  except errors.HttpError as error:
    logging.error('An HTTP error occurred: %s', error)

def create_message(sender, to, subject, message_text, files):
  """Create a message for an email.

  Args:
    sender: Email address of the sender.
    to: Email address of the receiver.
    subject: The subject of the email message.
    message_text: The text of the email message.

  Returns:
    An object containing a base64url encoded email object.
  """
  message = MIMEMultipart()
  message.attach(MIMEText(message_text))

  message['to'] = to
  message['from'] = sender
  message['subject'] = subject

  for path in files:
      part = MIMEBase('application', "octet-stream")
      with open(path, 'rb') as file:
          part.set_payload(file.read())
      encoders.encode_base64(part)
      part.add_header('Content-Disposition',
                      'attachment; filename="{}"'.format(Path(path).name))
      message.attach(part)

  s = message.as_string()
  b = base64.urlsafe_b64encode(s.encode('utf-8'))
  return {'raw': b.decode('utf-8')}

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--f", dest="folder")
    args = parser.parse_args()

    report = os.path.join(args.folder, "report.pdf")


    logging.basicConfig(
        format="[%(levelname)s] %(message)s",
        level=logging.INFO
    )

    logging.getLogger('googleapicliet.discovery_cache').setLevel(logging.ERROR)

    try:
        service = get_service()
        message = create_message(
          "contact@skysightdata.com",
          CONTACT,
          SUBJECT,
          BODY,
          [report])

        send_message(service, "contact@skysightdata.com", message)

    except Exception as e:
        logging.error(e)
        raise
import argparse
import smtplib
from pathlib import Path
import os
import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate
from email import encoders
import ssl
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

BODY = BODY.replace("TIMEOFDAY", {True: "morning", False: "afternoon"}[dt.hour < 12])
BODY = BODY.replace("ADDRESS", ADDRESS)

def send_email(send_from, send_to, subject, message, files=[],
              server="smtp.gmail.com", port=587, username='', password='',
              use_tls=True):
    """Compose and send email with provided info and attachments.

    Args:
        send_from (str): from name
        send_to (list[str]): to name(s)
        subject (str): message title
        message (str): message body
        files (list[str]): list of file paths to be attached to email
        server (str): mail server host name
        port (int): port number
        username (str): server auth username
        password (str): server auth password
        use_tls (bool): use TLS mode
    """
    msg = MIMEMultipart()
    msg['From'] = send_from
    msg['To'] = COMMASPACE.join(send_to)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject

    msg.attach(MIMEText(message))

    for path in files:
        part = MIMEBase('application', "octet-stream")
        with open(path, 'rb') as file:
            part.set_payload(file.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition',
                        'attachment; filename="{}"'.format(Path(path).name))
        msg.attach(part)

    smtp = smtplib.SMTP(server, port)

    context = ssl.create_default_context()
    smtp.starttls(context=context)

    smtp.login(send_from, password)
    smtp.sendmail(send_from, send_to, msg.as_string())
    smtp.quit()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--f", dest="folder")
    args = parser.parse_args()

    report = os.path.join(args.folder, "report.pdf")

    password = input("Enter email password: ")

    send_email(
        "skysightdata@gmail.com",
        [CONTACT],
        SUBJECT,
        BODY,
        files=[report],
        password=password
    )


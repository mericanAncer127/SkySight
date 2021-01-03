import smtplib
import ssl
from email.message import EmailMessage
import argparse
import datetime as dt

SUBJECT = "SkySight Roof Report: ADDRESS"
BODY = """Good TIMEOFDAY,

Attached is your SkySight Roof Report for ADDRESS. Your payment of $12 will be processed within 24 hours of completion of the report. Please reach out if you have any questions or concerns.

Thank you for using SkySight!
The SkySight Team
skysightdata.com
"""

def send_email(folder):
    sender_email = 'skysightdata@gmail.com'
    receiver_email = 'clymersam@gmail.com'
    password = 'MoserDome15!'

    server = smtplib.SMTP('smtp.gmail.com', 587)

    context = ssl.create_default_context()
    server.starttls(context=context)

    msg = "Subject: {}\n\n{}".format(SUBJECT, BODY)

    server.login(sender_email, password)
    server.sendmail(sender_email, receiver_email, msg)
    server.quit()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--f", dest="folder")
    args = parser.parse_args()

    send_email(args.folder)

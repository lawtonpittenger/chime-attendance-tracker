
import os
import asyncio
from amazon_transcribe.client import TranscribeStreamingClient
from amazon_transcribe.handlers import TranscriptResultStreamHandler
from amazon_transcribe.model import TranscriptEvent
import sounddevice as sd
from datetime import datetime, timedelta
import bisect

import boto3
import json
import re
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import requests

meeting_platform = os.environ['MEETING_PLATFORM']
meeting_id = os.environ['MEETING_ID']
meeting_password = os.environ['MEETING_PASSWORD']
meeting_name = os.environ['MEETING_NAME']

email_sender = os.environ['EMAIL_SENDER']
email_receiver = os.environ['EMAIL_RECEIVER']

scribe_name = "Attendance Tracker"
scribe_identity = f"{scribe_name} ({email_receiver})"

waiting_timeout = 300000 # 5 minutes
meeting_timeout = 21600000 # 6 hours

speakers = []
speaker_timestamps = []

async def speaker_change(speaker):
    speaker_timestamps.append(datetime.now())
    speakers.append(speaker)
    print('New Speaker:', speaker)

def encapsulate():
    email_source = f"{scribe_name} <{'+attendance@'.join(email_sender.split('@'))}>"
    email_destinations = [email_receiver]
    
    msg = MIMEMultipart('mixed')
    msg['From'] = email_source
    msg['To'] = ', '.join(email_destinations)
    msg['Subject'] = f"{meeting_name} - Attendance Report"

    # Calculate attendance durations for each unique participant
    attendance_data = {}
    for speaker, timestamp in zip(speakers, speaker_timestamps):
        if speaker not in attendance_data:
            attendance_data[speaker] = {
                'first_seen': timestamp,
                'last_seen': timestamp
            }
        else:
            attendance_data[speaker]['last_seen'] = timestamp

    # Generate attendance report
    attendance_lines = []
    for speaker, data in sorted(attendance_data.items()):
        duration = int((data['last_seen'] - data['first_seen']).total_seconds() / 60)
        attendance_lines.append(f"{speaker} | {duration} minutes")

    html = f"""
        <html>
            <body>
                <h2>{meeting_name}</h2>
                <pre style="font-family: monospace;">
{chr(10).join(attendance_lines)}
                </pre>
            </body>
        </html>
    """

    body = MIMEMultipart('alternative')
    charset = "utf-8"
    body.attach(MIMEText(html.encode(charset), 'html', charset))
    msg.attach(body)

    boto3.client("ses").send_raw_email(
        Source=email_source,
        Destinations=email_destinations,
        RawMessage={
            'Data':msg.as_string(),
        }
    )
    print("Email sent!")

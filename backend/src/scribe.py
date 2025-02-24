
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

    # Create attendance report with timestamps
    attendance_data = {}
    for speaker, timestamp in zip(speakers, speaker_timestamps):
        if speaker not in attendance_data:
            attendance_data[speaker] = []
        attendance_data[speaker].append(timestamp)

    html = f"""
        <html>
            <body>
                <h2>Meeting Attendance Report</h2>
                <h3>Meeting Details:</h3>
                <p>Meeting Name: {meeting_name}</p>
                <p>Date: {datetime.now().strftime('%Y-%m-%d')}</p>
                <p>Total Unique Participants: {len(attendance_data)}</p>
                <h3>Participants:</h3>
                <table border="1">
                    <tr>
                        <th>Participant</th>
                        <th>First Detected</th>
                        <th>Last Detected</th>
                        <th>Times Detected</th>
                    </tr>
                    {''.join(f'''
                        <tr>
                            <td>{participant}</td>
                            <td>{min(times).strftime('%H:%M:%S')}</td>
                            <td>{max(times).strftime('%H:%M:%S')}</td>
                            <td>{len(times)}</td>
                        </tr>
                    ''' for participant, times in attendance_data.items())}
                </table>
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
    print("Attendance report email sent!")


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

def calculate_attendance_duration(speaker_list, timestamp_list):
    attendance_data = {}
    
    for speaker, timestamp in zip(speaker_list, timestamp_list):
        if speaker not in attendance_data:
            attendance_data[speaker] = {
                'first_seen': timestamp,
                'last_seen': timestamp,
                'duration': timedelta(0)
            }
        else:
            attendance_data[speaker]['last_seen'] = timestamp
            
    # Calculate duration for each participant
    for speaker in attendance_data:
        duration = attendance_data[speaker]['last_seen'] - attendance_data[speaker]['first_seen']
        attendance_data[speaker]['duration'] = duration.total_seconds() / 60  # Convert to minutes
        
    return attendance_data

def encapsulate():
    email_source = f"{scribe_name} <{'+attendance@'.join(email_sender.split('@'))}>"
    email_destinations = [email_receiver]
    
    msg = MIMEMultipart('mixed')
    msg['From'] = email_source
    msg['To'] = ', '.join(email_destinations)
    msg['Subject'] = f"{meeting_name} - Attendance Report"

    # Calculate attendance durations
    attendance_data = calculate_attendance_duration(speakers, speaker_timestamps)
    
    # Sort participants by name
    sorted_participants = sorted(attendance_data.items())
    
    # Create attendance report
    attendance_report = []
    for participant, data in sorted_participants:
        duration = int(round(data['duration']))  # Round to nearest minute
        attendance_report.append(f"{participant} | {duration} minutes")

    participants_text = '\n'.join(attendance_report)

    html = f"""
        <html>
            <body>
                <h2>{meeting_name}</h2>
                <h3>Attendance Report</h3>
                <pre style="font-family: monospace;">
{participants_text}
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

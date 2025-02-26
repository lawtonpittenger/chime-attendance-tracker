import os

meeting_platform = os.environ["MEETING_PLATFORM"]
meeting_id = os.environ["MEETING_ID"]
meeting_password = os.environ["MEETING_PASSWORD"]
meeting_name = os.environ["MEETING_NAME"]

email_sender = os.environ["EMAIL_SENDER"]
email_receiver = os.environ["EMAIL_RECEIVER"]

scribe_name = "Scribe"
scribe_identity = f"{scribe_name} ({email_receiver})"

waiting_timeout = 300000  # 5 minutes
meeting_timeout = 21600000  # 6 hours

start = True

start_command = "START"
pause_command = "PAUSE"
end_command = "END"

intro_messages = [
    (
        "Hello! I am a automated meeting attendance tracking bot."
        "I will be tracking attendance and saving chat messages during this meeting."
    )
]
start_messages = [
    "Saving attendance and chat messages",
    f'Send "{pause_command}" in the chat to stop saving meeting details.',
]
pause_messages = [
    "Not saving attendance and chat messages.",
    f'Send "{start_command}" in the chat to start saving meeting details.',
]

messages = []
attachments = {}
captions = []
speakers = []

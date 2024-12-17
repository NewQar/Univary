import os
from flask import Flask, request, jsonify, redirect, session, url_for
import requests
import google.oauth2.credentials
import google_auth_oauthlib.flow
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import jwt
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = "awi"

# ================= GOOGLE MEET CONFIG ===================
GOOGLE_REDIRECT_URI = "http://localhost:5000/google/callback"
GOOGLE_SCOPES = ['https://www.googleapis.com/auth/calendar']
GOOGLE_CREDENTIALS = "credentials.json"

# ================= ZOOM CONFIG ===========================
ZOOM_API_KEY = "awiZoomAPI"
ZOOM_API_SECRET = "awiZoomSecret"
ZOOM_REDIRECT_URI = "http://localhost:5000/zoom/callback"

# ================= MICROSOFT TEAMS CONFIG =================
MS_CLIENT_ID = "awiTeamsClientID"
MS_CLIENT_SECRET = "awiTeamsSecret"
MS_REDIRECT_URI = "http://localhost:5000/teams/callback"

# ================= ROUTES ================================

# Home
@app.route('/')
def home():
    return "Welcome to Univary Backend - Integrating Google Meet, Zoom, and Microsoft Teams!"

# =================== GOOGLE MEET ROUTES ==================

@app.route('/google/auth')
def google_auth():
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(GOOGLE_CREDENTIALS, scopes=GOOGLE_SCOPES)
    flow.redirect_uri = GOOGLE_REDIRECT_URI
    authorization_url, state = flow.authorization_url(access_type='offline', include_granted_scopes='true')
    session['state'] = state
    return redirect(authorization_url)

@app.route('/google/callback')
def google_callback():
    state = session['state']
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(GOOGLE_CREDENTIALS, scopes=GOOGLE_SCOPES, state=state)
    flow.redirect_uri = GOOGLE_REDIRECT_URI
    flow.fetch_token(authorization_response=request.url)
    session['google_credentials'] = credentials_to_dict(flow.credentials)
    return jsonify({"message": "Google Authentication Successful"})

@app.route('/google/create_event', methods=['POST'])
def google_create_event():
    creds = google.oauth2.credentials.Credentials(**session['google_credentials'])
    service = build('calendar', 'v3', credentials=creds)
    data = request.json

    event = {
        'summary': data.get('summary', 'Univary Meeting'),
        'start': {'dateTime': data['start_time'], 'timeZone': 'UTC'},
        'end': {'dateTime': data['end_time'], 'timeZone': 'UTC'},
        'conferenceData': {'createRequest': {'requestId': 'google123'}}
    }

    created_event = service.events().insert(calendarId='primary', body=event, conferenceDataVersion=1).execute()
    return jsonify({"meeting_link": created_event.get('hangoutLink')})

# =================== ZOOM ROUTES =========================

@app.route('/zoom/auth')
def zoom_auth():
    zoom_auth_url = f"https://zoom.us/oauth/authorize?response_type=code&client_id={ZOOM_API_KEY}&redirect_uri={ZOOM_REDIRECT_URI}"
    return redirect(zoom_auth_url)

@app.route('/zoom/callback')
def zoom_callback():
    code = request.args.get('code')
    token_url = "https://zoom.us/oauth/token"
    response = requests.post(token_url, data={
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': ZOOM_REDIRECT_URI
    }, headers={"Authorization": f"Basic {jwt.encode({}, ZOOM_API_SECRET, algorithm='HS256')}"})
    session['zoom_token'] = response.json()['access_token']
    return jsonify({"message": "Zoom Authentication Successful"})

@app.route('/zoom/create_meeting', methods=['POST'])
def zoom_create_meeting():
    token = session['zoom_token']
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    data = request.json

    meeting_payload = {
        "topic": data.get("topic", "Univary Zoom Meeting"),
        "type": 2,
        "start_time": data['start_time'],
        "duration": data.get("duration", 30),
        "timezone": "UTC",
        "settings": {"join_before_host": True}
    }

    response = requests.post("https://api.zoom.us/v2/users/me/meetings", headers=headers, json=meeting_payload)
    return jsonify(response.json())

# ================= MICROSOFT TEAMS ROUTES ===============

@app.route('/teams/auth')
def teams_auth():
    auth_url = f"https://login.microsoftonline.com/common/oauth2/v2.0/authorize?client_id={MS_CLIENT_ID}&response_type=code&redirect_uri={MS_REDIRECT_URI}&response_mode=query&scope=Calendars.ReadWrite online_meetings.create"
    return redirect(auth_url)

@app.route('/teams/callback')
def teams_callback():
    code = request.args.get('code')
    token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"

    response = requests.post(token_url, data={
        'client_id': MS_CLIENT_ID,
        'scope': 'Calendars.ReadWrite online_meetings.create',
        'code': code,
        'redirect_uri': MS_REDIRECT_URI,
        'grant_type': 'authorization_code',
        'client_secret': MS_CLIENT_SECRET
    })

    session['teams_token'] = response.json()['access_token']
    return jsonify({"message": "Microsoft Teams Authentication Successful"})

@app.route('/teams/create_meeting', methods=['POST'])
def teams_create_meeting():
    token = session['teams_token']
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    data = request.json

    meeting_payload = {
        "subject": data.get("subject", "Univary Teams Meeting"),
        "startDateTime": data['start_time'],
        "endDateTime": data['end_time'],
        "attendees": [{"emailAddress": {"address": email}, "type": "required"} for email in data.get('attendees', [])]
    }

    response = requests.post("https://graph.microsoft.com/v1.0/me/onlineMeetings", headers=headers, json=meeting_payload)
    return jsonify(response.json())

# ================= HELPER FUNCTIONS ======================

def credentials_to_dict(credentials):
    return {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }

# =================== START SERVER ========================
if __name__ == '__main__':
    app.run(debug=True)

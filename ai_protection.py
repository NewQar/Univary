import os
import jwt
import numpy as np
import pandas as pd
from flask import Flask, request, jsonify
from sklearn.ensemble import IsolationForest
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = "awi"

# ================= SECURITY SETTINGS =================
TOKEN_SECRET = "awiTokenSecret"
AI_MODEL_PATH = "ai_model.pkl"  # Placeholder for saving/loading trained models

# ================= DUMMY DATABASE ====================
user_activity_logs = []  # Store user activity logs temporarily
THRESHOLD_SCORE = -0.1   # AI threshold for anomaly detection

# ================= JWT TOKEN MANAGEMENT =================
def create_token(data, expires_in=3600):
    payload = {"data": data, "exp": datetime.utcnow() + timedelta(seconds=expires_in)}
    return jwt.encode(payload, TOKEN_SECRET, algorithm="HS256")

def verify_token(token):
    try:
        decoded = jwt.decode(token, TOKEN_SECRET, algorithms=["HS256"])
        return decoded
    except jwt.ExpiredSignatureError:
        return None

# ================= AI ANOMALY DETECTION =================
class AIAnomalyDetector:
    def __init__(self):
        self.model = IsolationForest(n_estimators=100, contamination=0.1, random_state=42)
        self.data = pd.DataFrame(columns=["user_id", "api_usage", "access_time"])

    def update_data(self, user_id):
        access_time = datetime.utcnow().timestamp()
        api_usage = np.random.randint(1, 100)  # Simulating API calls
        self.data = pd.concat([self.data, pd.DataFrame([[user_id, api_usage, access_time]],
                                                      columns=self.data.columns)], ignore_index=True)

    def train_model(self):
        if len(self.data) > 10:  # Train only if there is sufficient data
            self.model.fit(self.data[["api_usage", "access_time"]])

    def detect_anomaly(self, user_id):
        if self.data.empty:
            return False  # No data to analyze

        recent_data = self.data[self.data["user_id"] == user_id].iloc[-1:]
        prediction = self.model.decision_function(recent_data[["api_usage", "access_time"]])
        return prediction[0] < THRESHOLD_SCORE  # True if anomaly detected

# Initialize AI model
ai_protector = AIAnomalyDetector()

# ================= ROUTES =================

# Home
@app.route('/')
def home():
    return "AI Protection Backend Running."

# ================= TOKEN AUTH ROUTES =================

@app.route('/generate_token', methods=['POST'])
def generate_token():
    data = request.json
    user_id = data.get("user_id", "unknown_user")
    token = create_token({"user_id": user_id})
    return jsonify({"token": token})

@app.route('/verify_token', methods=['POST'])
def token_verification():
    data = request.json
    token = data.get("token")
    decoded = verify_token(token)

    if decoded:
        user_id = decoded["data"]["user_id"]
        return jsonify({"message": "Token is valid", "user_id": user_id})
    return jsonify({"message": "Invalid or expired token"}), 401

# ================= AI SECURITY ROUTES =================

@app.route('/log_activity', methods=['POST'])
def log_activity():
    data = request.json
    token = data.get("token")
    decoded = verify_token(token)

    if not decoded:
        return jsonify({"message": "Unauthorized"}), 401

    user_id = decoded["data"]["user_id"]
    ai_protector.update_data(user_id)
    ai_protector.train_model()
    anomaly_detected = ai_protector.detect_anomaly(user_id)

    user_activity_logs.append({"user_id": user_id, "timestamp": datetime.utcnow()})
    if anomaly_detected:
        return jsonify({"message": "Unusual activity detected. AI has flagged this action."})
    return jsonify({"message": "Activity logged successfully."})

@app.route('/check_logs', methods=['GET'])
def check_logs():
    return jsonify({"logs": user_activity_logs})

# ================= MEETING DATA AI PROTECTION =================

@app.route('/secure_data', methods=['POST'])
def secure_meeting_data():
    data = request.json
    token = data.get("token")
    decoded = verify_token(token)

    if not decoded:
        return jsonify({"message": "Unauthorized"}), 401

    meeting_data = data.get("meeting_data", {})
    user_id = decoded["data"]["user_id"]

    # AI Protection Check
    ai_protector.update_data(user_id)
    ai_protector.train_model()
    anomaly_detected = ai_protector.detect_anomaly(user_id)

    if anomaly_detected:
        return jsonify({"message": "Data access blocked due to suspicious activity."})

    return jsonify({"message": "Data is secured and accessible.", "data": meeting_data})

# ================= SERVER RUN ========================
if __name__ == '__main__':
    app.run(debug=True)

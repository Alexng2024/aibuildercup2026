# GoEyeVoice

## Overview

GoEyeVoice is an AI-powered real-time scam call detection system that monitors live phone conversations, analyzes speech content using Google Gemini AI, and generates risk assessments to identify potential fraud and social engineering attacks.

---

## Problem Statement
Problem Statement: BFSI institutions are facing a surge of sophisticated, multi-channel fraud—ranging from social engineering voice calls to malicious SMS and phishing links. While basic solutions exist, they rely heavily on simple phone number matching, which is fundamentally insufficient since scammers can easily change or spoof numbers. Traditional, siloed systems fail to detect these cross-platform threats, leading to severe financial losses, compliance risks, and eroded customer trust.

---

## Solution Features

### Real-Time Call Monitoring
- Live audio streaming using Twilio Media Streams
- Continuous processing during active calls

### Speech-to-Text Transcription
- Real-time transcription using Google Speech-to-Text

### AI Scam Analysis
- Gemini 2.5 Flash analyzes call conversations
- Context-aware analysis using a 15-second rolling window

### Scam Detection
Detects:
- Police impersonation
- Government impersonation
- Bank fraud
- Investment scams
- OTP theft attempts
- Social engineering attacks
- Urgent payment requests

### Risk Assessment
- Risk score (0–100)
- Scam category classification
- AI-generated explanation

### Live Dashboard
- Real-time monitoring
- Alert history
- Color-coded risk levels
  - 🟢 Low Risk
  - 🟠 Medium Risk
  - 🔴 High Risk

---

## Architecture

```text
Caller
   │
   ▼
Twilio Voice
   │
   ▼
Twilio Media Stream
   │
   ▼
FastAPI Backend (Cloud Run)
   │
   ▼
Google Speech-to-Text
   │
   ▼
15-Second Context Buffer
   │
   ▼
Gemini AI Analysis
   │
   ▼
Risk Assessment
   │
   ▼
Firestore Database
   │
   ▼
Live Dashboard





Technology Stack
Communication
Twilio Voice
Twilio Media Streams
Backend
Python
FastAPI
WebSocket
Artificial Intelligence
Google Gemini 2.5 Flash
Speech Processing
Google Speech-to-Text
Cloud Services
Google Cloud Run
Google Firestore
Frontend
HTML
CSS
JavaScript

Live Demo
Dashboard

https://realtime-listener-322055493672.asia-southeast1.run.app/dashboard

Source Code

https://github.com/Alexng2024/aibuildercup2026

Example Detection

Transcript

"I am Officer James from the investigation department. Your account is linked to money laundering activities. You must transfer funds to a government account immediately or face legal consequences."

Result

JSON
{
"risk_score": 100,
"category": "Government Impersonation Scam",
"alert": true
}
Future Enhancements
Multi-language support (English, Cantonese, Mandarin)
SMS notifications
WhatsApp notifications
Dashboard analytics
Family member alerting
AI-assisted intervention
Team

AI Builder Cup 2026




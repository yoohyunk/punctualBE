# Punctual - Smart Transit Alert Service

Never miss your bus again! Get intelligent, multi-stage SMS notifications for your daily commute.

## 🌟 Features

- **3-Stage Smart Notifications**: Wake up, Departure, Transit arrival alerts
- **Google Directions API**: Automatic route calculation with real-time transit
- **Twilio SMS**: Reliable text notifications
- **Smart Timing**: Rounded departure times (0/15/30/45 min) + 3-min transit warnings

## 🚀 Quick Start (Local)

### Prerequisites

- Python 3.13+
- Google Maps API Key
- Twilio Account

### Installation

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Create `.env` file:

```bash
GOOGLE_MAPS_API_KEY=your_api_key
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890
```

3. Run:

```bash
# API Server
python server.py

# Scheduler (separate terminal)
python scheduler.py
```

## 🌐 Deploy to Render

### Method 1: Using render.yaml (Recommended)

1. **Push to GitHub:**

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin YOUR_GITHUB_REPO_URL
git push -u origin main
```

2. **Connect to Render:**

   - Go to [render.com](https://render.com)
   - Click "New" → "Blueprint"
   - Connect your GitHub repository
   - Render will automatically detect `render.yaml`

3. **Set Environment Variables:**

   - In Render dashboard, go to each service
   - Add environment variables:
     - `GOOGLE_MAPS_API_KEY`
     - `TWILIO_ACCOUNT_SID`
     - `TWILIO_AUTH_TOKEN`
     - `TWILIO_PHONE_NUMBER`

4. **Deploy!**
   - Render will build and deploy both services automatically

### Method 2: Manual Setup

1. **Create Web Service:**

   - New → Web Service
   - Connect repository
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn server:app`

2. **Create Worker Service:**

   - New → Background Worker
   - Connect repository
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python scheduler.py`

3. **Add Environment Variables** to both services

## 📡 API Endpoints

### Test SMS

```bash
POST /test/sms
{
  "phone_number": "+18255613205"
}
```

### Create Alert

```bash
POST /alerts
{
  "phone_number": "+18255613205",
  "origin_text": "Calgary Tower, Calgary",
  "destination_text": "University of Calgary, Calgary",
  "target_type": "ARRIVAL",
  "target_time": "2025-11-16T09:00:00-07:00",
  "preparation_minutes": 30
}
```

### Manual Notifications (Testing)

```bash
POST /alerts/{id}/notify/wake-up
POST /alerts/{id}/notify/departure
POST /alerts/{id}/notify/transit
```

### Get Alerts

```bash
GET /alerts
GET /alerts/{id}
GET /alerts/pending?type=wake_up
```

## 🔧 Tech Stack

- Flask 3.1.2
- SQLite (auto-creates on startup)
- Google Maps Directions API
- Twilio SMS API
- APScheduler (background tasks)
- Gunicorn (production server)

## 📱 How It Works

1. User creates alert: "I want to arrive at University by 9:00 AM"
2. Server calls Google Directions API
3. Calculates:
   - Departure time (e.g., 8:20 AM)
   - Rounded time (8:15 AM)
   - Wake up time (7:45 AM with 30min prep)
   - First transit time (e.g., bus at 8:25 AM)
   - Transit alert (8:22 AM, 3min before)
4. Scheduler sends SMS at each calculated time

## 🎯 Example Notifications

**7:45 AM - Wake Up:**

```
⏰ Good morning! Time to wake up!

You need to leave at 08:15 AM to reach
University of Calgary on time.
Start getting ready!
```

**8:15 AM - Departure:**

```
🚪 Time to leave!

Destination: University of Calgary
Arrival: 09:00 AM

Route:
🚶 Walk 0.2 km
🚌 Route 9: 7 Ave SW → University Station

Have a safe trip!
```

**8:22 AM - Transit:**

```
🚌 Transit Alert!

Route 9 is arriving at 7 Ave SW in 3 minutes.
Head to the stop now!
```

## 📝 Environment Variables

Required for both local and Render deployment:

- `GOOGLE_MAPS_API_KEY` - Get from [Google Cloud Console](https://console.cloud.google.com/google/maps-apis)
- `TWILIO_ACCOUNT_SID` - Get from [Twilio Console](https://www.twilio.com/console)
- `TWILIO_AUTH_TOKEN` - Get from Twilio Console
- `TWILIO_PHONE_NUMBER` - Your Twilio phone number (format: +1234567890)

Optional:

- `PORT` - Server port (default: 8080, Render sets automatically)
- `DATABASE_URL` - SQLite path (default: sqlite:///punctual.db)

## 🐛 Troubleshooting

### Local Development

**Port already in use:**

```bash
# Find and kill process
lsof -ti:8080 | xargs kill -9
```

**Database issues:**

```bash
# Reset database
rm -f instance/punctual.db
python init_db.py
```

### Render Deployment

**Build fails:**

- Check Python version in render.yaml matches requirements
- Verify requirements.txt is in root directory

**App crashes:**

- Check Render logs for errors
- Verify all environment variables are set
- Check that gunicorn is in requirements.txt

**Scheduler not working:**

- Verify worker service is running in Render dashboard
- Check worker logs for errors
- Ensure DATABASE_URL is accessible from worker

## 📄 License

MIT

## 🤝 Contributing

Pull requests welcome!

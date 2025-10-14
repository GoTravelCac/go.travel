# 🌍 go.travel - Travel Itinerary Generator

# **Live Website:** https://gotravel-app-407949658262.us-central1.run.app

## 🛠️ Technology Stack

- **Backend**: Python Flask
- **AI Model**: Google Gemini 2.5 Flash
- **APIs**: Google Maps, Places, Geocoding, Weather, Time Zone
- **Deployment**: Google Cloud Run
- **Frontend**: HTML5, CSS3, JavaScript

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Google Cloud Platform account
- API keys for Google Cloud and OpenWeatherMap

### Local Development
```bash
# Clone the repository
git clone https://github.com/GoTravelCac/go.travel.git
cd go.travel

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# Run the application
python app.py
```

### Environment Variables
```
GEMINI_API_KEY=your_gemini_api_key
GOOGLE_API_KEY=your_google_api_key
OPENWEATHERMAP_API_KEY=your_openweathermap_api_key
```

## 📦 Deployment

The application is deployed on Google Cloud Run with automatic scaling and HTTPS.

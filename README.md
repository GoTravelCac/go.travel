# 🌍 go.travel - AI-Powered Travel Itinerary Generator

[![Live Demo](https://img.shields.io/badge/Live-Demo-blue?style=for-the-badge)](https://gotravel-41611891727.us-central1.run.app)
[![Python](https://img.shields.io/badge/Python-3.13-blue?style=for-the-badge&logo=python)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0-green?style=for-the-badge&logo=flask)](https://flask.palletsprojects.com)
[![Google Cloud](https://img.shields.io/badge/Google%20Cloud-Run-orange?style=for-the-badge&logo=googlecloud)](https://cloud.google.com)

# **Live Website:** [go.travel](https://gotravel-41611891727.us-central1.run.app)

## ✨ Features

🤖 **AI-Powered Planning** - Leverages Google Gemini 2.5 Flash for intelligent itinerary generation
🗺️ **Interactive Maps** - Google Maps integration with autocomplete and location services  
🌤️ **Real-time Weather** - Live weather data and forecasts for your destinations
� **Responsive Design** - Optimized for desktop, tablet, and mobile devices
✈️ **Comprehensive Options** - Lodging, transportation, budget, and interest preferences
📄 **Export & Share** - Download itineraries as PDF or share via email
🔄 **AI Refinement** - Modify and improve your itinerary with natural language requests

## �🛠️ Technology Stack

### **Backend & AI**
- **Python Flask** - Web framework and API server
- **Google Gemini 2.5 Flash** - Advanced AI for itinerary generation
- **RESTful APIs** - Clean, scalable backend architecture

### **APIs & Services**  
- **Google Maps JavaScript API** - Interactive maps and location services
- **Google Places API** - Location autocomplete and place details
- **Google Geocoding API** - Address and coordinate conversion
- **OpenWeatherMap API** - Weather data and forecasts
- **Google Time Zone API** - Accurate time zone calculations

### **Infrastructure**
- **Google Cloud Run** - Serverless container deployment
- **Docker** - Containerized application (Python 3.13-slim)
- **HTTPS/SSL** - Secure connections with automatic certificates
- **Auto-scaling** - Handles traffic spikes automatically

### **Frontend**
- **HTML5/CSS3** - Modern, semantic markup and styling
- **Vanilla JavaScript** - Interactive UI without heavy frameworks
- **Google Fonts** - Inter & Dancing Script typography
- **Responsive Design** - Mobile-first approach

## 🚀 Quick Start

### Prerequisites
- **Python 3.11+** (3.13 recommended)
- **Google Cloud Platform account** with billing enabled
- **API Keys** for Google Cloud services and OpenWeatherMap

### Local Development
```bash
# 1. Clone the repository
git clone https://github.com/GoTravelCac/go.travel.git
cd go.travel

# 2. Create virtual environment (recommended)
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux  
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env
# Edit .env with your API keys (see configuration below)

# 5. Run the application
python app.py
```

### 🔑 API Configuration

Create a `.env` file with the following variables:

```env
# Gemini AI API Key (Get from: https://makersuite.google.com/app/apikey)
GEMINI_API_KEY=your_gemini_api_key_here

# Google API Key (Get from: https://console.cloud.google.com/)
# Required APIs: Maps JavaScript, Places, Geocoding, Directions, Time Zone
GOOGLE_API_KEY=your_google_api_key_here

# OpenWeatherMap API Key (Get from: https://openweathermap.org/api)
OPENWEATHERMAP_API_KEY=your_openweathermap_api_key_here

# Flask Environment
FLASK_ENV=development
PORT=5000
```

### � Google Cloud Setup

1. **Create a Google Cloud Project**
2. **Enable Required APIs:**
   - Maps JavaScript API
   - Places API (New)  
   - Geocoding API
   - Directions API
   - Time Zone API

3. **Configure API Key Restrictions:**
   - **Application restrictions:** HTTP referrers
   - **Allowed referrers:** 
     - `https://your-domain.com/*`
     - `http://localhost:5000/*` (for development)
   - **API restrictions:** Enable only the required APIs above

## �📦 Deployment

### Google Cloud Run (Recommended)

```bash
# 1. Build and deploy using provided script
.\deploy.ps1  # Windows PowerShell
# OR
./deploy.sh   # Linux/macOS

# 2. Manual deployment
gcloud run deploy gotravel \
    --source . \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars "GEMINI_API_KEY=$GEMINI_API_KEY,GOOGLE_API_KEY=$GOOGLE_API_KEY,OPENWEATHERMAP_API_KEY=$OPENWEATHERMAP_API_KEY"
```

### Docker Deployment

```bash
# Build the Docker image
docker build -t go-travel .

# Run locally
docker run -p 8080:8080 \
    -e GEMINI_API_KEY=your_key \
    -e GOOGLE_API_KEY=your_key \
    -e OPENWEATHERMAP_API_KEY=your_key \
    go-travel
```

## 🏗️ Project Structure

```
go.travel/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies  
├── Dockerfile            # Container configuration
├── .env.example          # Environment template
├── deploy.ps1           # Deployment script
├── templates/           # HTML templates
│   ├── base.html       # Base template with navigation
│   ├── home.html       # Landing page
│   ├── planner.html    # Trip planner interface
│   ├── explore.html    # Destination explorer
│   └── about.html      # About page
├── favicon/            # Favicon files
└── static/            # Static assets (if any)
```

## 🌟 Key Features Explained

### **Enhanced Trip Planner**
- **4 Transportation Options:** Air, ground, rail, and local transport
- **Lodging Preferences:** Hotels, hostels, Airbnb, resorts, etc.
- **Budget Categories:** Economy, mid-range, luxury options
- **Family-Friendly:** Children count and age considerations
- **Interest Matching:** Museums, food, nature, nightlife, etc.

### **AI-Powered Itinerary Generation**
- **Context-Aware:** Understands destination, dates, and preferences
- **Detailed Scheduling:** Day-by-day breakdown with timing
- **Local Insights:** Cultural tips, safety information, costs
- **Weather Integration:** Real-time forecasts and recommendations
- **Refinement System:** Natural language itinerary modifications

### **Interactive Experience**
- **Google Maps Integration:** Visual location previews
- **Autocomplete Search:** Smart destination suggestions  
- **Mobile Optimization:** Touch-friendly interface
- **Export Options:** PDF download and email sharing

## 🔧 Development

### **Adding New Features**
1. **Backend:** Extend `app.py` with new routes
2. **Frontend:** Update templates in `templates/`
3. **Styling:** Modify CSS in template `{% block styles %}`
4. **JavaScript:** Add interactivity in `{% block scripts %}`

### **API Integration**
- **New APIs:** Add to configuration in `app.py`
- **Environment Variables:** Update `.env.example`
- **Error Handling:** Implement graceful fallbacks

### **Testing**
```bash
# Run local development server
python app.py

# Test API endpoints
curl http://localhost:5000/api/status
curl http://localhost:5000/api/destinations
```

## 🤝 Contributing

We welcome contributions! Here's how to get started:

1. **Fork the repository**
2. **Create a feature branch:** `git checkout -b feature-name`
3. **Make your changes** and test thoroughly
4. **Commit:** `git commit -m "Add feature description"`
5. **Push:** `git push origin feature-name`
6. **Submit a Pull Request**

### **Contribution Guidelines**
- Follow Python PEP 8 style guidelines
- Add comments for complex logic
- Test new features thoroughly
- Update documentation as needed

## 📄 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) file for details.

## 🙋‍♂️ Support

- **Issues:** [GitHub Issues](https://github.com/GoTravelCac/go.travel/issues)
- **Documentation:** This README and inline code comments
- **API Status:** Check `/api/status` endpoint on live site

## 🎯 Roadmap

- [ ] User authentication and saved itineraries
- [ ] Social sharing and community features  
- [ ] Multi-language support
- [ ] Offline map downloads
- [ ] Integration with booking platforms
- [ ] Advanced AI personalization

---

**Made with ❤️ for the Congressional App Challenge**  
*Empowering travelers with AI-driven itinerary planning*

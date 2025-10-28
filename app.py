#!/usr/bin/env python3
"""
go.travel - AI Travel Itinerary Generator
A Flask-based web application that generates personalized travel itineraries using Gemini AI.
"""

import os
import json
import requests
from datetime import datetime
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configuration
class Config:
    def __init__(self):
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        self.google_api_key = os.getenv('GOOGLE_API_KEY')
        self.openweathermap_api_key = os.getenv('OPENWEATHERMAP_API_KEY')
        self.gemini_model = None
        self.setup_apis()
    
    def setup_apis(self):
        """Initialize all API services"""
        self.setup_gemini()
        self.validate_google_apis()
    
    def setup_gemini(self):
        """Initialize Gemini AI model"""
        if not self.gemini_api_key:
            print("❌ GEMINI_API_KEY not found in environment variables")
            return
        
        try:
            genai.configure(api_key=self.gemini_api_key)
            self.gemini_model = genai.GenerativeModel('gemini-2.5-flash')
            print("✅ Gemini 2.5 Flash model initialized successfully")
        except Exception as e:
            print(f"❌ Gemini initialization error: {e}")
            # Fallback to gemini-pro if 2.0 flash is not available
            try:
                self.gemini_model = genai.GenerativeModel('gemini-pro')
                print("✅ Gemini Pro model initialized (fallback)")
            except Exception as e2:
                print(f"❌ Gemini fallback error: {e2}")
                self.gemini_model = None
    
    def validate_google_apis(self):
        """Validate Google API key works with various services"""
        if not self.google_api_key:
            print("❌ GOOGLE_API_KEY not found in environment variables")
            return
        
        print("🔧 Validating Google API services...")
        
        # Test Geocoding API
        try:
            test_url = f"https://maps.googleapis.com/maps/api/geocode/json?address=Paris&key={self.google_api_key}"
            response = requests.get(test_url, timeout=5)
            if response.status_code == 200:
                print("✅ Google APIs accessible (tested with Geocoding)")
            else:
                print(f"⚠️ Google API warning: Status {response.status_code}")
        except Exception as e:
            print(f"⚠️ Could not validate Google APIs: {e}")
    
    def get_api_status(self):
        """Get status of all configured APIs"""
        return {
            'gemini_available': self.gemini_model is not None,
            'google_api_available': self.google_api_key is not None,
            'supported_apis': [
                'Weather API',
                'Time Zone API', 
                'Roads API',
                'Places API (New)',
                'Places API',
                'Maps Static API',
                'Maps Embed API',
                'Maps JavaScript API',
                'Geocoding API',
                'Geolocation API',
                'Directions API'
            ]
        }

# Google API Service Classes
class GoogleAPIService:
    """Base service class for Google APIs"""
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://maps.googleapis.com/maps/api"
    
    def make_request(self, endpoint, params=None):
        """Make a request to Google API with error handling"""
        try:
            if params is None:
                params = {}
            params['key'] = self.api_key
            
            response = requests.get(f"{self.base_url}/{endpoint}", params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"API request error: {e}")
            return {"error": str(e)}

class GeocodingService(GoogleAPIService):
    """Google Geocoding API service"""
    
    def get_coordinates(self, address):
        """Get latitude and longitude for an address"""
        params = {'address': address}
        return self.make_request('geocode/json', params)
    
    def reverse_geocode(self, lat, lng):
        """Get address from coordinates"""
        params = {'latlng': f"{lat},{lng}"}
        return self.make_request('geocode/json', params)

class PlacesService(GoogleAPIService):
    """Google Places API service"""
    
    def search_nearby(self, lat, lng, place_type, radius=5000):
        """Search for nearby places"""
        params = {
            'location': f"{lat},{lng}",
            'radius': radius,
            'type': place_type
        }
        return self.make_request('place/nearbysearch/json', params)
    
    def get_place_details(self, place_id):
        """Get detailed information about a place"""
        params = {'place_id': place_id}
        return self.make_request('place/details/json', params)
    
    def text_search(self, query, location=None, radius=50000):
        """Search for places by text query"""
        params = {'query': query}
        if location:
            params['location'] = location
            params['radius'] = radius
        return self.make_request('place/textsearch/json', params)

class DirectionsService(GoogleAPIService):
    """Google Directions API service"""
    
    def get_directions(self, origin, destination, mode='driving', waypoints=None):
        """Get directions between locations"""
        params = {
            'origin': origin,
            'destination': destination,
            'mode': mode
        }
        if waypoints:
            params['waypoints'] = '|'.join(waypoints)
        return self.make_request('directions/json', params)

class TimeZoneService(GoogleAPIService):
    """Google Time Zone API service"""
    
    def get_timezone(self, lat, lng, timestamp=None):
        """Get timezone information for coordinates"""
        import time
        if timestamp is None:
            timestamp = int(time.time())
        
        params = {
            'location': f"{lat},{lng}",
            'timestamp': timestamp
        }
        return self.make_request('timezone/json', params)

class WeatherService:
    """Weather service using OpenWeatherMap API"""
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.openweathermap.org/data/2.5"
    
    def get_current_weather(self, lat, lng):
        """Get current weather for coordinates"""
        try:
            params = {
                'lat': lat,
                'lon': lng,
                'appid': self.api_key,
                'units': 'metric'
            }
            response = requests.get(f"{self.base_url}/weather", params=params, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"OpenWeatherMap API error: {response.status_code}")
                return self._get_fallback_weather()
        except Exception as e:
            print(f"Weather API error: {e}")
            return self._get_fallback_weather()
    
    def get_forecast(self, lat, lng, days=5):
        """Get weather forecast for coordinates"""
        try:
            params = {
                'lat': lat,
                'lon': lng,
                'appid': self.api_key,
                'units': 'metric',
                'cnt': days * 8  # 8 forecasts per day (3-hour intervals)
            }
            response = requests.get(f"{self.base_url}/forecast", params=params, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": "Forecast data unavailable"}
        except Exception as e:
            print(f"Weather forecast API error: {e}")
            return {"error": "Forecast data unavailable"}
    
    def _get_fallback_weather(self):
        """Return fallback weather data when API is unavailable"""
        return {
            "weather": [{"main": "Clear", "description": "clear sky"}],
            "main": {"temp": 22, "feels_like": 25, "humidity": 60},
            "wind": {"speed": 3.5},
            "name": "Location",
            "note": "Sample data - OpenWeatherMap API unavailable"
        }

class CurrencyService:
    """Currency conversion service using free Exchange Rates API"""
    
    def __init__(self):
        self.base_url = "https://api.exchangerate-api.com/v4/latest"
        self.cache = {}
        self.cache_duration = 3600  # 1 hour cache
        
    def get_exchange_rate(self, from_currency, to_currency="USD"):
        """Get exchange rate between two currencies"""
        cache_key = f"{from_currency}_{to_currency}"
        current_time = datetime.now()
        
        # Check cache first
        if cache_key in self.cache:
            cached_data, cached_time = self.cache[cache_key]
            if (current_time - cached_time).seconds < self.cache_duration:
                return cached_data
        
        try:
            response = requests.get(f"{self.base_url}/{from_currency}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                rate = data.get('rates', {}).get(to_currency, 1)
                self.cache[cache_key] = (rate, current_time)
                return rate
            else:
                return 1  # Fallback rate
        except Exception as e:
            print(f"Currency API error: {e}")
            return 1  # Fallback rate
    
    def convert_price(self, amount, from_currency, to_currency="USD"):
        """Convert price from one currency to another"""
        if from_currency == to_currency:
            return amount
        
        rate = self.get_exchange_rate(from_currency, to_currency)
        return round(amount * rate, 2)
    
    def format_price_with_conversion(self, local_amount, local_currency, destination_country=None):
        """Format price showing both local and USD equivalent"""
        if local_currency == "USD":
            return f"${local_amount}"
        
        usd_amount = self.convert_price(local_amount, local_currency, "USD")
        
        # Currency symbols mapping
        symbols = {
            "EUR": "€", "GBP": "£", "JPY": "¥", "CNY": "¥", 
            "INR": "₹", "CAD": "C$", "AUD": "A$", "CHF": "CHF",
            "SEK": "kr", "NOK": "kr", "DKK": "kr", "THB": "฿"
        }
        
        symbol = symbols.get(local_currency, local_currency)
        return f"{symbol}{local_amount} (~${usd_amount} USD)"
    
    def get_country_currency(self, country):
        """Get the primary currency for a country"""
        currency_map = {
            "United States": "USD", "USA": "USD", "US": "USD",
            "United Kingdom": "GBP", "UK": "GBP", "England": "GBP", "Britain": "GBP",
            "France": "EUR", "Germany": "EUR", "Italy": "EUR", "Spain": "EUR", 
            "Netherlands": "EUR", "Austria": "EUR", "Belgium": "EUR", "Portugal": "EUR",
            "Japan": "JPY", "China": "CNY", "India": "INR", "Canada": "CAD",
            "Australia": "AUD", "Switzerland": "CHF", "Sweden": "SEK", 
            "Norway": "NOK", "Denmark": "DKK", "Thailand": "THB",
            "South Korea": "KRW", "Singapore": "SGD", "Hong Kong": "HKD",
            "Mexico": "MXN", "Brazil": "BRL", "Russia": "RUB", "Turkey": "TRY"
        }
        
        # Try exact match first
        if country in currency_map:
            return currency_map[country]
        
        # Try partial matching
        country_lower = country.lower()
        for country_name, currency in currency_map.items():
            if country_lower in country_name.lower() or country_name.lower() in country_lower:
                return currency
        
        return "USD"  # Default fallback

class RoadsService(GoogleAPIService):
    """Google Roads API service"""
    
    def snap_to_roads(self, path, interpolate=False):
        """Snap GPS coordinates to road network"""
        base_url = "https://roads.googleapis.com/v1"
        params = {
            'path': path,
            'interpolate': interpolate,
            'key': self.api_key
        }
        try:
            response = requests.get(f"{base_url}/snapToRoads", params=params, timeout=10)
            return response.json()
        except Exception as e:
            return {"error": str(e)}

# Service Manager
class GoogleServicesManager:
    """Manager for all Google API services"""
    
    def __init__(self, google_api_key, openweathermap_api_key):
        self.api_key = google_api_key
        self.geocoding = GeocodingService(google_api_key)
        self.places = PlacesService(google_api_key)
        self.directions = DirectionsService(google_api_key)
        self.timezone = TimeZoneService(google_api_key)
        self.weather = WeatherService(openweathermap_api_key)  # Use OpenWeatherMap API key
        self.roads = RoadsService(google_api_key)
    
    def get_location_info(self, location_query):
        """Get comprehensive information about a location"""
        try:
            # Step 1: Geocode the location
            geocode_result = self.geocoding.get_coordinates(location_query)
            if 'error' in geocode_result or 'results' not in geocode_result or not geocode_result['results']:
                return {"error": "Location not found"}
            
            location_data = geocode_result['results'][0]
            lat = location_data['geometry']['location']['lat']
            lng = location_data['geometry']['location']['lng']
            formatted_address = location_data['formatted_address']
            
            # Step 2: Get additional information
            timezone_info = self.timezone.get_timezone(lat, lng)
            weather_info = self.weather.get_current_weather(lat, lng)
            
            # Step 3: Find nearby attractions
            attractions = self.places.search_nearby(lat, lng, 'tourist_attraction')
            restaurants = self.places.search_nearby(lat, lng, 'restaurant')
            
            return {
                'location': {
                    'address': formatted_address,
                    'coordinates': {'lat': lat, 'lng': lng}
                },
                'timezone': timezone_info,
                'weather': weather_info,
                'nearby': {
                    'attractions': attractions,
                    'restaurants': restaurants
                }
            }
        except Exception as e:
            return {"error": f"Failed to get location info: {str(e)}"}

# Initialize services
config = Config()
currency_service = CurrencyService()

# Initialize Google services with proper error handling
try:
    if config.google_api_key and config.openweathermap_api_key:
        google_services = GoogleServicesManager(config.google_api_key, config.openweathermap_api_key)
        print("✅ Google services initialized successfully")
    else:
        google_services = None
        print("❌ Missing API keys - Google services not available")
        if not config.google_api_key:
            print("   Missing GOOGLE_API_KEY")
        if not config.openweathermap_api_key:
            print("   Missing OPENWEATHERMAP_API_KEY")
except Exception as e:
    google_services = None
    print(f"❌ Failed to initialize Google services: {e}")

@app.route('/')
def home():
    """Serve the home page"""
    return render_template('home.html', google_api_key=config.google_api_key)

@app.route('/planner')
def planner():
    """Serve the trip planner page"""
    return render_template('planner.html', google_api_key=config.google_api_key)

@app.route('/explore')
def explore():
    """Serve the explore destinations page"""
    return render_template('explore.html', google_api_key=config.google_api_key)

@app.route('/about')
def about():
    """Serve the about page"""
    return render_template('about.html', google_api_key=config.google_api_key)

@app.route('/sitemap.xml')
def sitemap():
    """Generate sitemap.xml for SEO"""
    from flask import Response
    
    sitemap_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>https://gotravel-41611891727.us-central1.run.app/</loc>
        <lastmod>{}</lastmod>
        <changefreq>weekly</changefreq>
        <priority>1.0</priority>
    </url>
    <url>
        <loc>https://gotravel-41611891727.us-central1.run.app/planner</loc>
        <lastmod>{}</lastmod>
        <changefreq>weekly</changefreq>
        <priority>0.9</priority>
    </url>
    <url>
        <loc>https://gotravel-41611891727.us-central1.run.app/explore</loc>
        <lastmod>{}</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.8</priority>
    </url>
    <url>
        <loc>https://gotravel-41611891727.us-central1.run.app/about</loc>
        <lastmod>{}</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.7</priority>
    </url>
</urlset>'''.format(
        datetime.now().strftime('%Y-%m-%d'),
        datetime.now().strftime('%Y-%m-%d'),
        datetime.now().strftime('%Y-%m-%d'),
        datetime.now().strftime('%Y-%m-%d')
    )
    
    return Response(sitemap_xml, mimetype='application/xml')

@app.route('/robots.txt')
def robots():
    """Generate robots.txt for SEO"""
    from flask import Response
    
    robots_txt = '''User-agent: *
Allow: /
Disallow: /api/
Disallow: /admin/

Sitemap: https://gotravel-41611891727.us-central1.run.app/sitemap.xml'''
    
    return Response(robots_txt, mimetype='text/plain')

@app.route('/api/status')
def api_status():
    """Check the status of all configured APIs"""
    status = {
        'timestamp': datetime.now().isoformat(),
        'apis': {
            'gemini': {
                'configured': config.gemini_api_key is not None,
                'model_available': config.gemini_model is not None,
                'key_preview': f"{config.gemini_api_key[:10]}..." if config.gemini_api_key else None
            },
            'google': {
                'configured': config.google_api_key is not None,
                'services_available': google_services is not None,
                'key_preview': f"{config.google_api_key[:10]}..." if config.google_api_key else None,
                'services': [
                    'Maps JavaScript API',
                    'Places API',
                    'Geocoding API',
                    'Directions API',
                    'Time Zone API',
                    'Roads API'
                ]
            },
            'openweather': {
                'configured': config.openweathermap_api_key is not None,
                'key_preview': f"{config.openweathermap_api_key[:10]}..." if config.openweathermap_api_key else None
            }
        },
        'overall_status': 'healthy' if all([
            config.gemini_api_key,
            config.google_api_key,
            config.openweathermap_api_key,
            config.gemini_model
        ]) else 'degraded'
    }
    
    return jsonify(status)

# Static file routes
@app.route('/gotravel.png')
def logo():
    """Serve the logo file"""
    return send_from_directory('.', 'gotravel.png')

@app.route('/favicon/<path:filename>')
def favicon(filename):
    """Serve favicon files"""
    return send_from_directory('favicon', filename)

@app.route('/api/destinations', methods=['GET'])
def get_destinations():
    """Get popular travel destinations with real-time data"""
    try:
        # Popular destinations with coordinates and safety ratings
        popular_destinations = [
            {"name": "Paris", "country": "France", "emoji": "🗼", "lat": 48.8566, "lng": 2.3522, "category": ["city", "popular", "cultural"], "safety_rating": 4.2, "safety_tips": "Be aware of pickpockets in tourist areas"},
            {"name": "Tokyo", "country": "Japan", "emoji": "🏯", "lat": 35.6762, "lng": 139.6503, "category": ["city", "popular", "cultural"], "safety_rating": 4.8, "safety_tips": "Very safe city with excellent public safety"},
            {"name": "New York", "country": "USA", "emoji": "🗽", "lat": 40.7128, "lng": -74.0060, "category": ["city", "popular"], "safety_rating": 4.0, "safety_tips": "Stay alert in busy areas, avoid isolated places at night"},
            {"name": "London", "country": "UK", "emoji": "🇬🇧", "lat": 51.5074, "lng": -0.1278, "category": ["city", "popular", "cultural"], "safety_rating": 4.3, "safety_tips": "Generally safe, watch for petty theft in crowded areas"},
            {"name": "Dubai", "country": "UAE", "emoji": "🏙️", "lat": 25.2048, "lng": 55.2708, "category": ["city", "popular"], "safety_rating": 4.6, "safety_tips": "Very safe with strict laws and good security"},
            {"name": "Reykjavik", "country": "Iceland", "emoji": "🌋", "lat": 64.1466, "lng": -21.9426, "category": ["nature", "adventure"], "safety_rating": 4.9, "safety_tips": "Extremely safe, main concerns are weather-related"},
            {"name": "Cape Town", "country": "South Africa", "emoji": "🦁", "lat": -33.9249, "lng": 18.4241, "category": ["nature", "adventure", "cultural"], "safety_rating": 3.5, "safety_tips": "Avoid walking alone at night, stay in safe neighborhoods"},
            {"name": "Maldives", "country": "Maldives", "emoji": "🏖️", "lat": 3.2028, "lng": 73.2207, "category": ["beach", "popular"], "safety_rating": 4.7, "safety_tips": "Very safe resorts, follow water safety guidelines"},
            {"name": "Bali", "country": "Indonesia", "emoji": "🌺", "lat": -8.3405, "lng": 115.0920, "category": ["beach", "cultural", "nature"], "safety_rating": 4.1, "safety_tips": "Generally safe, be cautious with street food and water"},
            {"name": "Kyoto", "country": "Japan", "emoji": "🎌", "lat": 35.0116, "lng": 135.7681, "category": ["cultural", "nature"], "safety_rating": 4.8, "safety_tips": "Extremely safe with very low crime rates"},
            {"name": "Petra", "country": "Jordan", "emoji": "🏜️", "lat": 30.3285, "lng": 35.4444, "category": ["cultural", "adventure"], "safety_rating": 4.0, "safety_tips": "Generally safe, follow tour guides and stay hydrated"},
            {"name": "Barcelona", "country": "Spain", "emoji": "🏖️", "lat": 41.3851, "lng": 2.1734, "category": ["city", "beach", "cultural"], "safety_rating": 4.1, "safety_tips": "Watch for pickpockets, especially in tourist areas"},
        ]
        
        destinations_with_data = []
        
        for dest in popular_destinations:
            try:
                # Get real weather data
                weather = "Weather data unavailable"
                if google_services and google_services.weather:
                    weather_data = google_services.weather.get_current_weather(dest['lat'], dest['lng'])
                    if weather_data and 'main' in weather_data:
                        temp = round(weather_data['main']['temp'])
                        desc = weather_data['weather'][0]['description'].title() if 'weather' in weather_data and weather_data['weather'] else 'Clear'
                        weather = f"{temp}°C, {desc}"
                    elif weather_data and not weather_data.get('error'):
                        # Handle fallback weather data
                        temp = weather_data.get('main', {}).get('temp', 22)
                        weather = f"{round(temp)}°C, Clear"
                
                # Get timezone and population from Google APIs if available
                timezone = "UTC"
                population = "Unknown"
                
                if google_services:
                    # Get location details
                    location_name = f"{dest['name']}, {dest['country']}"
                    location_info = google_services.get_location_info(location_name)
                    
                    if 'timezone' in location_info:
                        tz_data = location_info['timezone']
                        if isinstance(tz_data, dict) and 'timeZoneName' in tz_data:
                            timezone = tz_data['timeZoneName']
                        else:
                            timezone = str(tz_data)
                    if 'population' in location_info:
                        pop_data = location_info['population']
                        if isinstance(pop_data, (int, float)):
                            if pop_data >= 1000000:
                                population = f"{pop_data/1000000:.1f}M"
                            elif pop_data >= 1000:
                                population = f"{pop_data/1000:.0f}K"
                            else:
                                population = str(int(pop_data))
                        else:
                            population = str(pop_data)
                
                destination_data = {
                    **dest,
                    'weather': weather,
                    'timezone': timezone,
                    'safety_rating': dest.get('safety_rating', 4.0),
                    'safety_tips': dest.get('safety_tips', 'Follow standard travel safety precautions'),
                    'description': f"Explore the amazing {dest['name']} with its unique culture, attractions, and experiences."
                }
                
                destinations_with_data.append(destination_data)
                
            except Exception as e:
                # If there's an error getting data for this destination, include basic info
                destinations_with_data.append({
                    **dest,
                    'weather': 'Data unavailable',
                    'timezone': 'UTC',
                    'safety_rating': dest.get('safety_rating', 4.0),
                    'safety_tips': dest.get('safety_tips', 'Follow standard travel safety precautions'),
                    'description': f"Discover the wonders of {dest['name']}, {dest['country']}."
                })
        
        return jsonify({
            'destinations': destinations_with_data,
            'count': len(destinations_with_data),
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        return jsonify({'error': f'Destinations API error: {str(e)}'}), 500

@app.route('/api/destination-details/<destination_name>', methods=['GET'])
def get_destination_details(destination_name):
    """Get detailed information about a specific destination"""
    try:
        if not google_services:
            return jsonify({'error': 'Google services not available'}), 503
        
        # Get comprehensive location information
        location_info = google_services.get_location_info(destination_name)
        
        # Get nearby attractions
        if 'coordinates' in location_info:
            coords = location_info['coordinates']
            attractions = google_services.places.search_nearby(
                coords['lat'], coords['lng'], 'tourist_attraction', radius=10000
            )
        else:
            attractions = {'results': []}
        
        return jsonify({
            'destination': destination_name,
            'details': location_info,
            'attractions': attractions.get('results', [])[:10],  # Top 10 attractions
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        return jsonify({'error': f'Destination details error: {str(e)}'}), 500

@app.route('/api/location-info', methods=['POST'])
def get_location_info():
    """Get comprehensive location information"""
    try:
        data = request.get_json()
        location = data.get('location')
        
        if not location:
            return jsonify({'error': 'Location is required'}), 400
        
        if not google_services:
            return jsonify({'error': 'Google services not available'}), 503
        
        location_info = google_services.get_location_info(location)
        return jsonify(location_info)
    
    except Exception as e:
        return jsonify({'error': f'Location info error: {str(e)}'}), 500

@app.route('/api/weather-forecast', methods=['POST'])
def get_weather_forecast():
    """Get weather forecast for a location"""
    try:
        data = request.get_json()
        location = data.get('location')
        days = data.get('days', 5)
        
        if not location:
            return jsonify({'error': 'Location is required'}), 400
        
        if not google_services:
            return jsonify({'error': 'Weather services not available'}), 503
        
        # First get coordinates
        geocode_result = google_services.geocoding.get_coordinates(location)
        if 'error' in geocode_result or 'results' not in geocode_result or not geocode_result['results']:
            return jsonify({'error': 'Location not found'}), 404
        
        location_data = geocode_result['results'][0]
        lat = location_data['geometry']['location']['lat']
        lng = location_data['geometry']['location']['lng']
        
        # Get forecast
        forecast = google_services.weather.get_forecast(lat, lng, days)
        return jsonify(forecast)
    
    except Exception as e:
        return jsonify({'error': f'Weather forecast error: {str(e)}'}), 500

@app.route('/api/directions', methods=['POST'])
def get_directions():
    """Get directions between locations"""
    try:
        data = request.get_json()
        origin = data.get('origin')
        destination = data.get('destination')
        mode = data.get('mode', 'driving')
        waypoints = data.get('waypoints')
        
        if not origin or not destination:
            return jsonify({'error': 'Origin and destination are required'}), 400
        
        if not google_services:
            return jsonify({'error': 'Google services not available'}), 503
        
        directions = google_services.directions.get_directions(origin, destination, mode, waypoints)
        return jsonify(directions)
    
    except Exception as e:
        return jsonify({'error': f'Directions error: {str(e)}'}), 500

@app.route('/api/places/search', methods=['POST'])
def search_places():
    """Search for places"""
    try:
        data = request.get_json()
        query = data.get('query')
        location = data.get('location')
        place_type = data.get('type')
        
        if not google_services:
            return jsonify({'error': 'Google services not available'}), 503
        
        if query:
            # Text search
            results = google_services.places.text_search(query, location)
        elif location and place_type:
            # Get coordinates first
            geocode_result = google_services.geocoding.get_coordinates(location)
            if 'results' in geocode_result and geocode_result['results']:
                coords = geocode_result['results'][0]['geometry']['location']
                results = google_services.places.search_nearby(coords['lat'], coords['lng'], place_type)
            else:
                return jsonify({'error': 'Could not geocode location'}), 400
        else:
            return jsonify({'error': 'Query or location+type are required'}), 400
        
        return jsonify(results)
    
    except Exception as e:
        return jsonify({'error': f'Places search error: {str(e)}'}), 500

@app.route('/api/maps/static', methods=['POST'])
def get_static_map():
    """Generate static map URL"""
    try:
        data = request.get_json()
        center = data.get('center')
        zoom = data.get('zoom', 13)
        size = data.get('size', '600x400')
        markers = data.get('markers', [])
        
        if not center:
            return jsonify({'error': 'Center location is required'}), 400
        
        if not config.google_api_key:
            return jsonify({'error': 'Google API key not available'}), 503
        
        # Build static map URL
        base_url = "https://maps.googleapis.com/maps/api/staticmap"
        params = [
            f"center={center}",
            f"zoom={zoom}",
            f"size={size}",
            f"key={config.google_api_key}"
        ]
        
        # Add markers
        for marker in markers:
            marker_param = f"markers={marker}"
            params.append(marker_param)
        
        map_url = f"{base_url}?" + "&".join(params)
        
        return jsonify({'map_url': map_url})
    
    except Exception as e:
        return jsonify({'error': f'Static map error: {str(e)}'}), 500

@app.route('/api/currency/<destination>')
@app.route('/api/currency/<destination>/<base_currency>')
def get_currency_info(destination, base_currency="USD"):
    """Get currency information for a destination"""
    try:
        # Extract country from destination
        country = destination.split(',')[-1].strip() if ',' in destination else destination
        local_currency = currency_service.get_country_currency(country)
        
        # Get exchange rate
        rate = currency_service.get_exchange_rate(base_currency, local_currency)
        
        return jsonify({
            'success': True,
            'destination': destination,
            'country': country,
            'local_currency': local_currency,
            'base_currency': base_currency,
            'exchange_rate': rate,
            'formatted_rate': f"1 {base_currency} = {rate:.2f} {local_currency}",
            'last_updated': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Currency lookup error: {str(e)}'
        }), 500

@app.route('/api/generate-itinerary', methods=['POST'])
def generate_itinerary():
    """Generate travel itinerary using Gemini AI"""
    try:
        # Get request data
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['destination', 'start_date', 'end_date', 'duration', 'people']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            return jsonify({
                'success': False,
                'error': f'Missing required fields: {", ".join(missing_fields)}'
            }), 400
        
        # Check if Gemini is available
        if not config.gemini_model:
            return jsonify({
                'success': False,
                'error': 'Gemini AI is not available. Please check the API key configuration.'
            }), 503
        
        # Extract data
        destination = data.get('destination')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        duration = data.get('duration')
        people = data.get('people')
        children = data.get('children', 0)
        budget = data.get('budget', '')
        lodging = data.get('lodging', '')
        travel_transport = data.get('travelTransport', '')
        local_transport = data.get('localTransport', '')
        interests = data.get('interests', [])
        special_requests = data.get('special_requests', '')
        
        # Create enhanced prompt with Google API integration
        prompt = create_enhanced_itinerary_prompt(
            destination, start_date, end_date, duration, people, children,
            budget, lodging, travel_transport, local_transport, interests, special_requests
        )
        
        print(f"🎯 Generating enhanced itinerary for {destination} ({duration} days)")
        
        # Get location context if Google services available
        location_context = ""
        if google_services:
            try:
                location_info = google_services.get_location_info(destination)
                if 'location' in location_info:
                    location_context = f"\n\nLocation Context:\n"
                    location_context += f"Address: {location_info['location']['address']}\n"
                    
                    if 'weather' in location_info and 'main' in location_info['weather']:
                        weather = location_info['weather']
                        location_context += f"Current Weather: {weather['main']['temp']}°C, {weather['weather'][0]['description']}\n"
                    
                    if 'nearby' in location_info:
                        nearby = location_info['nearby']
                        if 'attractions' in nearby and 'results' in nearby['attractions']:
                            attractions = [place['name'] for place in nearby['attractions']['results'][:5]]
                            location_context += f"Nearby Attractions: {', '.join(attractions)}\n"
                        
                        if 'restaurants' in nearby and 'results' in nearby['restaurants']:
                            restaurants = [place['name'] for place in nearby['restaurants']['results'][:5]]
                            location_context += f"Nearby Restaurants: {', '.join(restaurants)}\n"
                    
                    prompt += location_context
            except Exception as e:
                print(f"Could not get location context: {e}")
        else:
            print("Google services not available for enhanced context")
        
        # Generate itinerary using Gemini
        response = config.gemini_model.generate_content(prompt)
        itinerary = response.text
        
        # Clean the itinerary text (remove unwanted markdown characters)
        formatted_itinerary = clean_itinerary_text(itinerary)
        
        # Enhance with currency information
        enhanced_itinerary = enhance_itinerary_with_currency(formatted_itinerary, destination)
        
        return jsonify({
            'success': True,
            'itinerary': enhanced_itinerary,
            'destination': destination,
            'duration': duration,
            'start_date': start_date,
            'end_date': end_date,
            'generated_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"❌ Error generating itinerary: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to generate itinerary: {str(e)}'
        }), 500

def clean_itinerary_text(text):
    """Clean itinerary text by removing unwanted markdown characters while preserving content."""
    import re
    
    if not text or text.strip() == '':
        return ''
    
    # More careful cleaning to avoid removing content
    cleaned_text = text
    
    # Remove markdown headers (# ## ###) but keep the header text
    cleaned_text = re.sub(r'^#{1,6}\s*', '', cleaned_text, flags=re.MULTILINE)
    
    # Remove bold markdown (**text**) but keep the text content
    cleaned_text = re.sub(r'\*\*([^*]+)\*\*', r'\1', cleaned_text)
    
    # Remove remaining single asterisks used for emphasis
    cleaned_text = re.sub(r'(?<!\*)\*(?!\*)', '', cleaned_text)
    
    # Clean up excessive whitespace while preserving paragraph breaks
    cleaned_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned_text)
    
    # Remove leading/trailing whitespace but preserve structure
    lines = cleaned_text.split('\n')
    cleaned_lines = [line.rstrip() for line in lines]
    cleaned_text = '\n'.join(cleaned_lines)
    
    return cleaned_text.strip()

def enhance_itinerary_with_currency(itinerary_text, destination):
    """Enhance itinerary text with currency conversion information"""
    try:
        # Get currency for destination
        country = destination.split(',')[-1].strip() if ',' in destination else destination
        local_currency = currency_service.get_country_currency(country)
        
        if local_currency == "USD":
            return itinerary_text  # No conversion needed
        
        # Add currency information header if not already present
        currency_info = f"\n\nCURRENCY INFORMATION:\n"
        currency_info += f"Local Currency: {local_currency}\n"
        currency_info += f"Exchange Rate: 1 USD = {currency_service.get_exchange_rate('USD', local_currency):.2f} {local_currency}\n"
        currency_info += f"Note: All prices shown as {local_currency} amount (~USD equivalent)\n"
        
        # Insert currency info after the first paragraph if not already present
        if "CURRENCY INFORMATION" not in itinerary_text and "Exchange Rate" not in itinerary_text:
            lines = itinerary_text.split('\n')
            insert_index = 3 if len(lines) > 3 else len(lines)
            lines.insert(insert_index, currency_info)
            itinerary_text = '\n'.join(lines)
        
        return itinerary_text
        
    except Exception as e:
        print(f"Error enhancing currency info: {e}")
        return itinerary_text

def create_enhanced_itinerary_prompt(destination, start_date, end_date, duration, people, children, budget, lodging, travel_transport, local_transport, interests, special_requests):
    """Create an enhanced prompt with Google API integration"""
    
    # Get currency information for the destination
    country = destination.split(',')[-1].strip() if ',' in destination else destination
    local_currency = currency_service.get_country_currency(country)
    
    # Convert interests list to readable format
    interests_text = ', '.join(interests) if interests else 'general sightseeing'
    
    # People and children context
    people_text = f"{people} {'person' if people == 1 else 'people'}"
    if children > 0:
        people_text += f" (including {children} {'child' if children == 1 else 'children'})"
    
    group_context = ""
    if children > 0:
        group_context = f"\n- Plan family-friendly activities suitable for children"
        group_context += f"\n- Consider child safety, accessibility, and age-appropriate attractions"
    elif people == 1:
        group_context = "\n- Plan activities suitable for solo travelers"
    elif people == 2:
        group_context = "\n- Plan romantic and couple-friendly activities"
    elif people <= 4:
        group_context = "\n- Plan activities suitable for small groups and families"
    else:
        group_context = "\n- Plan activities suitable for larger groups, consider group discounts and reservations"
    
    # Budget context
    budget_context = ""
    if budget:
        if budget == 'budget':
            budget_context = "\n- Focus on budget-friendly options, free attractions, and affordable accommodations"
        elif budget == 'moderate':
            budget_context = "\n- Include mid-range accommodations and dining options"
        elif budget == 'luxury':
            budget_context = "\n- Include luxury accommodations, fine dining, and premium experiences"
    
    # Lodging context
    lodging_context = ""
    if lodging:
        if lodging == 'hotel':
            lodging_context = "\n- Recommend hotels with appropriate amenities for the group size"
        elif lodging == 'airbnb':
            lodging_context = "\n- Suggest Airbnb or vacation rental properties suitable for the group"
        elif lodging == 'resort':
            lodging_context = "\n- Focus on resort accommodations with inclusive amenities"
        elif lodging == 'hostel':
            lodging_context = "\n- Recommend hostels with private rooms or dorms as appropriate"
        elif lodging == 'already_booked':
            lodging_context = "\n- Accommodation is already booked, focus on activities and dining"
    
    # Transportation context
    transport_context = ""
    if travel_transport:
        transport_context += f"\n- Travel method: {travel_transport}"
        if travel_transport == 'plane':
            transport_context += " (include airport transfer recommendations)"
        elif travel_transport == 'drive':
            transport_context += " (include parking information and scenic route suggestions)"
        elif travel_transport == 'train':
            transport_context += " (include train station information and connections)"
        elif travel_transport == 'cruise':
            transport_context += " (include port information and shore excursions)"
    
    if local_transport:
        transport_context += f"\n- Local transportation: {local_transport}"
        if local_transport == 'rental_car':
            transport_context += " (include rental locations, parking, and driving tips)"
        elif local_transport == 'public_transport':
            transport_context += " (include transit passes, routes, and schedules)"
        elif local_transport == 'walking':
            transport_context += " (focus on walkable attractions and neighborhoods)"
        elif local_transport == 'rideshare':
            transport_context += " (include ride-hailing apps and taxi information)"
    
    # Special requests context
    special_context = f"\n- Special considerations: {special_requests}" if special_requests else ""
    
    prompt = f"""As a travel planner, create a detailed {duration}-day travel itinerary for {destination} from {start_date} to {end_date} for {people_text}.

TRAVELER PREFERENCES:
- Group size: {people_text}
- Interests: {interests_text}{budget_context}{lodging_context}{transport_context}{group_context}{special_context}

CURRENCY & PRICING REQUIREMENTS:
- Local currency for {destination}: {local_currency}
- ALL prices must be provided in local currency ({local_currency}) with USD conversion in parentheses
- Format: "{local_currency}100 (~$75 USD)" for local prices
- Include realistic price ranges for restaurants, attractions, transportation, and activities
- Consider group size when calculating total costs (multiply individual prices by {people})
- Mention any group discounts available for attractions or activities

REQUIREMENTS:
- Provide a day-by-day breakdown (Day 1, Day 2, etc.)
- Include specific activities, attractions, and experiences with prices in {local_currency} and USD conversions for {people_text}
- Suggest actual restaurant names and local cuisine with menu price ranges in both currencies for {people_text}
- Include timing recommendations (morning, afternoon, evening)
- Add transportation tips between locations with costs in {local_currency} and USD for {people_text}
- Consider group size when recommending accommodations and dining reservations
- Include daily budget estimates in both {local_currency} and USD

LOCATION & SAFETY REQUIREMENTS:
- Provide EXACT FULL ADDRESSES for all attractions, restaurants, and hotels
- Format addresses as: "Address: [Complete Street Address, City, Postal Code, Country]"
- Include a dedicated "SAFETY INFORMATION" section at the end covering:
  * General safety tips for {destination}
  * Areas to avoid, especially at night
  * Common scams and how to avoid them
  * Emergency contact numbers (police, medical, tourist help)
  * Transportation safety advice
  * Cultural considerations and local customs
  * Money and document safety tips
- Add location-specific safety warnings for attractions in high-risk areas
- Mention cultural insights and local tips
- Consider opening hours and seasonal factors
- Include approximate time needed for each activity
- Mention any group rates or family packages available

FORMAT & STRUCTURE:
- Use clear headings for each day (Day 1:, Day 2:, etc.)
- Organize activities by time of day (Morning, Afternoon, Evening)
- Do NOT use any separators like -- or === in your text
- Do not include any *, **, or # characters, use indents, hyphens, and em dashes for cleaner formatting
- Make it engaging and informative with natural text formatting
- Include practical details and insider tips
- Include weather considerations and timezone information when available
- End with a comprehensive "SAFETY INFORMATION" section
- Write content continuously without manual separators - the system will add visual dividers automatically

REQUIRED SECTION STRUCTURE:
1. Day 1 activities and details with pricing in {local_currency} and USD
2. Day 2 activities and details (if multi-day) with pricing in both currencies
3. Additional days as needed with consistent pricing format
4. DAILY BUDGET SUMMARY (estimated total daily costs in {local_currency} and USD)
5. CURRENCY & PAYMENT INFORMATION (exchange rates, payment methods, tipping customs)
6. STRESS RELIEF & WELLNESS SECTION (dedicated section for relaxation and mental well-being)
7. SAFETY INFORMATION (always include this major section)
8. Cultural Considerations and Local Customs
9. Money and Document Safety Tips
10. Emergency Contacts

STRESS RELIEF & WELLNESS REQUIREMENTS:
- Include a dedicated "STRESS RELIEF & WELLNESS" section after the daily activities
- Provide specific stress-relief activities and locations in {destination}
- Include local spas, wellness centers, parks, or meditation spots with addresses and prices
- Suggest calming activities for each day (morning yoga spots, evening relaxation, etc.)
- Add breathing exercises, mindfulness tips, and relaxation techniques for travelers
- Include information about local wellness traditions and practices
- Recommend quiet spaces for decompression after busy sightseeing days
- Provide tips for managing travel anxiety and maintaining mental health during the trip
- Include contact information for wellness services and mental health resources if needed
- Add suggestions for healthy local foods and hydration tips
- Mention jet lag management and sleep optimization techniques

Write clean, flowing text with realistic pricing in both currencies - visual separators will be added automatically by the system.

IMPORTANT: Always include a comprehensive "STRESS RELIEF & WELLNESS" section that provides practical relaxation techniques, local wellness resources, and mental health tips for travelers. This section should help travelers manage stress, anxiety, and fatigue during their trip.

Please create a comprehensive, well-structured itinerary that maximizes the travel experience while being practical, actionable, safe, budget-conscious with accurate currency conversions, and supportive of traveler mental health and well-being."""

    return prompt

def create_itinerary_prompt(destination, start_date, end_date, duration, people, budget, interests, special_requests):
    """Create a detailed prompt for Gemini AI (legacy function)"""
    # Use default values for new parameters to maintain backward compatibility
    return create_enhanced_itinerary_prompt(destination, start_date, end_date, duration, people, 0, budget, '', '', '', interests, special_requests)

@app.route('/api/refine-itinerary', methods=['POST'])
def refine_itinerary():
    """Refine existing itinerary based on user feedback"""
    try:
        data = request.get_json()
        
        current_itinerary = data.get('current_itinerary')
        feedback = data.get('feedback')
        destination = data.get('destination')
        
        if not all([current_itinerary, feedback, destination]):
            return jsonify({
                'success': False,
                'error': 'Missing required data for refinement'
            }), 400
        
        if not config.gemini_model:
            return jsonify({
                'success': False,
                'error': 'Gemini AI is not available'
            }), 503
        
        # Create refinement prompt
        refinement_prompt = f"""The user has requested changes to their travel itinerary for {destination}.

ORIGINAL ITINERARY:
{current_itinerary}

USER FEEDBACK:
{feedback}

Please update the itinerary based on the user's feedback. Keep the same format and structure, but incorporate the requested changes. Maintain the quality and detail of the original while addressing the specific feedback provided."""

        response = config.gemini_model.generate_content(refinement_prompt)
        refined_itinerary = response.text
        
        return jsonify({
            'success': True,
            'itinerary': refined_itinerary,
            'refined_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"❌ Error refining itinerary: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to refine itinerary: {str(e)}'
        }), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500

if __name__ == '__main__':
    import os
    print("🚀 go.travel - AI Travel Itinerary Generator")
    print("=" * 50)
    print(f"✅ Flask app initialized")
    print(f"✅ Gemini API: {'Available' if config.gemini_model else 'Not Available'}")
    
    # Get port from environment variable (Heroku assigns this)
    port = int(os.environ.get('PORT', 5000))
    host = '0.0.0.0'  # Heroku requires 0.0.0.0
    debug = os.environ.get('FLASK_ENV') != 'production'
    
    print(f"🌐 Starting server on {host}:{port}")
    print("=" * 50)
    
    # Run the Flask app
    app.run(
        host=host,
        port=port,
        debug=debug,
        threaded=True
    )
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

# Application constants
APP_NAME = "go.travel"
APP_DESCRIPTION = "AI Travel Itinerary Generator"
APP_VERSION = "1.0.0"
APP_URL = "https://gotravel.com"

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configuration
class Config:
    def __init__(self):
        # Try multiple environment variable names for compatibility
        self.gemini_api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_GEMINI_API_KEY')
        self.google_api_key = os.getenv('GOOGLE_API_KEY') or os.getenv('GOOGLE_MAPS_API_KEY')
        self.openweathermap_api_key = os.getenv('OPENWEATHERMAP_API_KEY') or os.getenv('OPENWEATHER_API_KEY')
        self.gemini_model = None
        self.setup_apis()
    
    def setup_apis(self):
        """Initialize all API services"""
        self.setup_gemini()
        self.validate_google_apis()
    
    def setup_gemini(self):
        """Initialize Gemini AI model with fallback options"""
        if not self.gemini_api_key:
            print("❌ GEMINI_API_KEY not found in environment variables")
            return
        
        try:
            genai.configure(api_key=self.gemini_api_key)
            
            # Try different models in order of preference
            models_to_try = [
                'gemini-1.5-pro',
                'gemini-1.5-flash', 
                'gemini-pro'
            ]
            
            for model_name in models_to_try:
                try:
                    self.gemini_model = genai.GenerativeModel(model_name)
                    # Test the model with a simple request
                    test_response = self.gemini_model.generate_content("Hello")
                    if test_response:
                        print(f"✅ Gemini model '{model_name}' initialized successfully")
                        return
                except Exception as model_error:
                    print(f"⚠️ Model '{model_name}' failed: {model_error}")
                    continue
            
            print("❌ No Gemini models available")
            self.gemini_model = None
            
        except Exception as e:
            print(f"❌ Gemini initialization error: {e}")
            self.gemini_model = None
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

@app.route('/api/config')
def get_config():
    """Get client-side configuration"""
    return jsonify({
        'google_maps_api_key': config.google_api_key,
        'backend_url': '',  # Use relative URLs
        'app_name': APP_NAME,
        'app_description': APP_DESCRIPTION,
        'app_version': APP_VERSION,
        'app_url': APP_URL
    })

@app.route('/')
def home():
    """Serve the home page"""
    return render_template('home.html')

@app.route('/planner')
def planner():
    """Serve the trip planner page"""
    return render_template('planner.html')

@app.route('/explore')
def explore():
    """Serve the explore destinations page"""
    return render_template('explore.html')

@app.route('/about')
def about():
    """Serve the about page"""
    return render_template('about.html')

# Legacy route for backwards compatibility
@app.route('/index')
def index():
    """Redirect to planner for backwards compatibility"""
    return render_template('index.html')

# Static file routes
@app.route('/gotravel.png')
def logo():
    """Serve the logo file"""
    return send_from_directory('.', 'gotravel.png')

@app.route('/favicon/<path:filename>')
def favicon(filename):
    """Serve favicon files"""
    return send_from_directory('favicon', filename)

@app.route('/api/status', methods=['GET'])
def api_status():
    """Check API status"""
    status = config.get_api_status()
    status.update({
        'status': 'online',
        'google_services_available': google_services is not None,
        'timestamp': datetime.now().isoformat(),
        'model': 'gemini-2.0-flash-exp' if config.gemini_model else None
    })
    return jsonify(status)

@app.route('/api/destinations', methods=['GET'])
def get_destinations():
    """Get popular travel destinations with real-time data"""
    try:
        # Popular destinations with coordinates and alternative stats
        popular_destinations = [
            {"name": "Paris", "country": "France", "emoji": "🗼", "lat": 48.8566, "lng": 2.3522, "category": ["city", "popular", "cultural"], "area": "105 km²", "attractions": "130+ museums", "safety_rating": "4.1/5"},
            {"name": "Tokyo", "country": "Japan", "emoji": "🏯", "lat": 35.6762, "lng": 139.6503, "category": ["city", "popular", "cultural"], "area": "2,194 km²", "attractions": "100+ temples", "safety_rating": "4.8/5"},
            {"name": "New York", "country": "USA", "emoji": "🗽", "lat": 40.7128, "lng": -74.0060, "category": ["city", "popular"], "area": "1,214 km²", "attractions": "50+ neighborhoods", "safety_rating": "3.8/5"},
            {"name": "London", "country": "UK", "emoji": "🇬🇧", "lat": 51.5074, "lng": -0.1278, "category": ["city", "popular", "cultural"], "area": "1,572 km²", "attractions": "240+ museums", "safety_rating": "4.2/5"},
            {"name": "Dubai", "country": "UAE", "emoji": "🏙️", "lat": 25.2048, "lng": 55.2708, "category": ["city", "popular"], "area": "4,114 km²", "attractions": "200+ malls", "safety_rating": "4.6/5"},
            {"name": "Reykjavik", "country": "Iceland", "emoji": "🌋", "lat": 64.1466, "lng": -21.9426, "category": ["nature", "adventure"], "area": "274 km²", "attractions": "50+ hot springs", "safety_rating": "4.9/5"},
            {"name": "Cape Town", "country": "South Africa", "emoji": "🦁", "lat": -33.9249, "lng": 18.4241, "category": ["nature", "adventure", "cultural"], "area": "2,461 km²", "attractions": "300+ wine estates", "safety_rating": "3.5/5"},
            {"name": "Maldives", "country": "Maldives", "emoji": "🏖️", "lat": 3.2028, "lng": 73.2207, "category": ["beach", "popular"], "area": "298 km²", "attractions": "1,200+ islands", "safety_rating": "4.7/5"},
            {"name": "Bali", "country": "Indonesia", "emoji": "🌺", "lat": -8.3405, "lng": 115.0920, "category": ["beach", "cultural", "nature"], "area": "5,780 km²", "attractions": "2,000+ temples", "safety_rating": "4.3/5"},
            {"name": "Kyoto", "country": "Japan", "emoji": "🎌", "lat": 35.0116, "lng": 135.7681, "category": ["cultural", "nature"], "area": "827 km²", "attractions": "1,600+ temples", "safety_rating": "4.8/5"},
            {"name": "Petra", "country": "Jordan", "emoji": "🏜️", "lat": 30.3285, "lng": 35.4444, "category": ["cultural", "adventure"], "area": "264 km²", "attractions": "800+ monuments", "safety_rating": "4.1/5"},
            {"name": "Barcelona", "country": "Spain", "emoji": "🏖️", "lat": 41.3851, "lng": 2.1734, "category": ["city", "beach", "cultural"], "area": "101 km²", "attractions": "60+ beaches", "safety_rating": "4.0/5"},
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
                
                # Get timezone from Google APIs if available
                timezone = "UTC"
                
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
                
                destination_data = {
                    **dest,
                    'weather': weather,
                    'timezone': timezone,
                    'area': dest.get('area', 'Area unknown'),
                    'attractions': dest.get('attractions', 'Multiple attractions'),
                    'safety_rating': dest.get('safety_rating', '4.0/5'),
                    'description': f"Explore the amazing {dest['name']} with its unique culture, attractions, and experiences."
                }
                
                destinations_with_data.append(destination_data)
                
            except Exception as e:
                # If there's an error getting data for this destination, include basic info
                destinations_with_data.append({
                    **dest,
                    'weather': 'Data unavailable',
                    'timezone': 'UTC',
                    'area': dest.get('area', 'Area unknown'),
                    'attractions': dest.get('attractions', 'Multiple attractions'),
                    'safety_rating': dest.get('safety_rating', '4.0/5'),
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
        budget = data.get('budget', '')
        interests = data.get('interests', [])
        special_requests = data.get('special_requests', '')
        
        # Create enhanced prompt with Google API integration
        prompt = create_enhanced_itinerary_prompt(
            destination, start_date, end_date, duration, people,
            budget, interests, special_requests
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
        try:
            response = config.gemini_model.generate_content(prompt)
            if not response or not response.text:
                raise Exception("Gemini returned empty response")
            
            itinerary = response.text
            print("✅ Itinerary generated successfully")
        except Exception as gemini_error:
            print(f"❌ Gemini generation error: {gemini_error}")
            # Return a fallback error message
            return jsonify({
                'success': False,
                'error': f'AI service error: {str(gemini_error)}. Please try again.'
            }), 503
        
        # Format the itinerary for better readability
        formatted_itinerary = format_itinerary_text(itinerary)
        
        return jsonify({
            'success': True,
            'itinerary': formatted_itinerary,
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

def format_itinerary_text(text):
    """Format itinerary text with proper indentation, hyphens, and em dashes for better readability."""
    
    import re
    
    # Replace common markers with em dashes
    text = re.sub(r'^[\s]*[-*•]\s*', '— ', text, flags=re.MULTILINE)
    text = re.sub(r'(?<=\n)[\s]*[-*•]\s*', '— ', text)
    
    # Format day headers
    text = re.sub(r'^(Day\s+\d+[:\-\s]*.*?)$', r'<h3 style="color: var(--primary-color); margin: 2rem 0 1rem 0; padding: 0.5rem 0; border-bottom: 2px solid var(--primary-color);">\1</h3>', text, flags=re.MULTILINE | re.IGNORECASE)
    
    # Format time-based sections (Morning, Afternoon, Evening)
    text = re.sub(r'^((?:Morning|Afternoon|Evening|Night)[\s:]*.*?)$', r'<h4 style="color: var(--secondary-color); margin: 1.5rem 0 0.5rem 0; font-weight: 600;">\1</h4>', text, flags=re.MULTILINE | re.IGNORECASE)
    
    # Format activity lines with proper indentation
    lines = text.split('\n')
    formatted_lines = []
    
    for line in lines:
        stripped_line = line.strip()
        
        if not stripped_line:
            formatted_lines.append('<br>')
            continue
            
        # Skip lines that are already HTML
        if stripped_line.startswith('<h'):
            formatted_lines.append(line)
            continue
            
        # Format bullet points with indentation
        if stripped_line.startswith('—'):
            # Main bullet points
            formatted_line = f'<div style="margin: 0.5rem 0; padding-left: 1rem;">{stripped_line}</div>'
        elif re.match(r'^\s*[\d]+[\.\)]\s*', stripped_line):
            # Numbered lists
            formatted_line = f'<div style="margin: 0.5rem 0; padding-left: 1rem; font-weight: 500;">{stripped_line}</div>'
        elif re.match(r'^\s*[A-Z][^:]*:', stripped_line):
            # Category headers (like "Restaurant:", "Activity:", etc.)
            formatted_line = f'<div style="margin: 0.8rem 0 0.3rem 0; font-weight: 600; color: var(--text-color);">{stripped_line}</div>'
        else:
            # Regular text with proper spacing
            if len(stripped_line) > 80:  # Long paragraphs
                formatted_line = f'<p style="margin: 1rem 0; line-height: 1.6; text-align: justify;">{stripped_line}</p>'
            else:  # Short lines
                formatted_line = f'<div style="margin: 0.3rem 0; padding-left: 0.5rem;">{stripped_line}</div>'
        
        formatted_lines.append(formatted_line)
    
    # Join all lines
    formatted_text = '\n'.join(formatted_lines)
    
    # Clean up multiple consecutive breaks
    formatted_text = re.sub(r'(<br>\s*){3,}', '<br><br>', formatted_text)
    
    # Add overall container styling
    formatted_text = f'''
    <div style="font-family: var(--font-body); color: var(--text-color); line-height: 1.6; max-width: none;">
        {formatted_text}
    </div>
    '''
    
    return formatted_text

def create_enhanced_itinerary_prompt(destination, start_date, end_date, duration, people, budget, interests, special_requests):
    """Create an enhanced prompt with Google API integration"""
    
    # Convert interests list to readable format
    interests_text = ', '.join(interests) if interests else 'general sightseeing'
    
    # People context
    people_text = f"{people} {'person' if people == 1 else 'people'}"
    group_context = ""
    if people == 1:
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
        elif budget == 'mid-range':
            budget_context = "\n- Include mid-range accommodations and dining options"
        elif budget == 'luxury':
            budget_context = "\n- Include luxury accommodations, fine dining, and premium experiences"
    
    # Special requests context
    special_context = f"\n- Special considerations: {special_requests}" if special_requests else ""
    
    prompt = f"""As a travel planner, create a detailed {duration}-day travel itinerary for {destination} from {start_date} to {end_date} for {people_text}.

TRAVELER PREFERENCES:
- Group size: {people_text}
- Interests: {interests_text}{budget_context}{group_context}{special_context}

REQUIREMENTS:
- Provide a day-by-day breakdown (Day 1, Day 2, etc.)
- Include specific activities, attractions, and experiences with prices for {people_text}
- Suggest actual restaurant names and local cuisine with seating for {people_text}
- Include timing recommendations (morning, afternoon, evening)
- Add transportation tips between locations for {people_text}
- Consider group size when recommending accommodations and dining reservations
- Mention cultural insights and local tips
- Consider opening hours and seasonal factors
- Include approximate time needed for each activity
- Provide coordinates or addresses for major attractions when possible
- Mention any group rates or family packages available

HIDDEN GEMS & LOCAL EXPERIENCES:
- Include at least 2-3 hidden gems or lesser-known attractions per day
- Recommend local favorites that tourists typically miss
- Suggest authentic local experiences and off-the-beaten-path locations
- Include local markets, neighborhood cafes, and community events
- Mention secret viewpoints, hidden restaurants, and local hangout spots
- Balance popular attractions with unique, authentic experiences

TRAVEL TIMES & LOGISTICS:
- Include estimated travel times between each location/activity
- Specify transportation methods (walk, taxi, metro, bus) with approximate costs
- Account for realistic travel time including waiting and boarding
- Group nearby attractions to minimize travel time
- Suggest optimal routes to reduce backtracking
- Include buffer time for unexpected delays

SAFETY & SECURITY REQUIREMENTS:
- Include a dedicated SAFETY SECTION at the end with:
  * Emergency contact numbers (police, ambulance, tourist helpline)
  * Common safety concerns and how to avoid them
  * Safe areas vs areas to avoid, especially at night
  * Local scams to watch out for
  * Recommended safety apps or resources
  * Cultural customs and etiquette to avoid offending locals
  * Health and medical considerations
  * Travel insurance recommendations
- Add safety tips for each day's activities when relevant
- Mention secure transportation options
- Highlight any areas known for pickpocketing or tourist scams

FORMAT:
- Use clear headings for each day
- Organize activities by time of day
- Include practical details and insider tips
- Add a comprehensive SAFETY SECTION at the end
- Make it engaging and informative
- Include weather considerations and timezone information when available

Please create a comprehensive, well-structured itinerary that maximizes the travel experience while prioritizing traveler safety and being practical and actionable."""

    return prompt

def create_itinerary_prompt(destination, start_date, end_date, duration, people, budget, interests, special_requests):
    """Create a detailed prompt for Gemini AI (legacy function)"""
    return create_enhanced_itinerary_prompt(destination, start_date, end_date, duration, people, budget, interests, special_requests)

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
    print(f"🚀 {APP_NAME} - {APP_DESCRIPTION}")
    print("=" * 50)
    print(f"📝 Version: {APP_VERSION}")
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
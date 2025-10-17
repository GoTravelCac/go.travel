"""
Flight API Service for GoTravel
Provides flight search and information using Amadeus Travel API
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class FlightAPIService:
    """Service class for flight-related API operations using Amadeus"""
    
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://api.amadeus.com/v1"
        self.auth_url = "https://api.amadeus.com/v1/security/oauth2/token"
        self.access_token = None
        self.token_expires = None
        
    def _get_access_token(self) -> str:
        """Get or refresh access token for Amadeus API"""
        if (self.access_token and self.token_expires and 
            datetime.now() < self.token_expires):
            return self.access_token
            
        auth_data = {
            'grant_type': 'client_credentials',
            'client_id': self.api_key,
            'client_secret': self.api_secret
        }
        
        try:
            response = requests.post(self.auth_url, data=auth_data)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data['access_token']
            
            # Set expiration time (usually 30 minutes, subtract 5 min buffer)
            expires_in = token_data.get('expires_in', 1800)
            self.token_expires = datetime.now() + timedelta(seconds=expires_in - 300)
            
            return self.access_token
            
        except Exception as e:
            print(f"❌ Error getting Amadeus access token: {e}")
            return None
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make authenticated request to Amadeus API"""
        token = self._get_access_token()
        if not token:
            return None
            
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        try:
            url = f"{self.base_url}/{endpoint}"
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            print(f"❌ Amadeus API error for {endpoint}: {e}")
            return None
    
    def search_airports(self, query: str) -> List[Dict]:
        """Search for airports by city or airport name"""
        params = {
            'keyword': query,
            'max': 5
        }
        
        result = self._make_request('reference-data/locations', params)
        if not result or 'data' not in result:
            return []
            
        airports = []
        for location in result['data']:
            if location.get('subType') == 'AIRPORT':
                airports.append({
                    'code': location.get('iataCode'),
                    'name': location.get('name'),
                    'city': location.get('address', {}).get('cityName'),
                    'country': location.get('address', {}).get('countryName')
                })
                
        return airports
    
    def search_flights(self, origin: str, destination: str, departure_date: str, 
                      return_date: str = None, adults: int = 1, children: int = 0) -> Dict:
        """Search for flights between origin and destination"""
        params = {
            'originLocationCode': origin,
            'destinationLocationCode': destination,
            'departureDate': departure_date,
            'adults': adults,
            'max': 10
        }
        
        if return_date:
            params['returnDate'] = return_date
            
        if children > 0:
            params['children'] = children
            
        result = self._make_request('shopping/flight-offers', params)
        if not result or 'data' not in result:
            return {'flights': [], 'error': 'No flights found'}
            
        flights = []
        for offer in result['data'][:5]:  # Limit to top 5 results
            try:
                itinerary = offer['itineraries'][0]  # Outbound journey
                segment = itinerary['segments'][0]   # First segment
                
                flight_info = {
                    'airline': segment['carrierCode'],
                    'flight_number': f"{segment['carrierCode']}{segment['number']}",
                    'departure_time': segment['departure']['at'],
                    'arrival_time': segment['arrival']['at'],
                    'duration': itinerary['duration'],
                    'price': f"{offer['price']['total']} {offer['price']['currency']}",
                    'departure_airport': segment['departure']['iataCode'],
                    'arrival_airport': segment['arrival']['iataCode']
                }
                flights.append(flight_info)
                
            except KeyError as e:
                print(f"⚠️ Error parsing flight data: {e}")
                continue
                
        return {
            'flights': flights,
            'total_results': len(result['data']),
            'search_params': {
                'origin': origin,
                'destination': destination,
                'departure_date': departure_date,
                'return_date': return_date,
                'passengers': adults + children
            }
        }
    
    def get_flight_inspiration(self, origin: str, max_price: int = None) -> List[Dict]:
        """Get flight inspiration - popular destinations from origin"""
        params = {
            'origin': origin,
            'max': 10
        }
        
        if max_price:
            params['maxPrice'] = max_price
            
        result = self._make_request('shopping/flight-destinations', params)
        if not result or 'data' not in result:
            return []
            
        destinations = []
        for dest in result['data']:
            destinations.append({
                'destination': dest.get('destination'),
                'price': f"{dest['price']['total']} {dest['price']['currency']}",
                'departure_date': dest.get('departureDate'),
                'return_date': dest.get('returnDate')
            })
            
        return destinations
    
    def get_airline_info(self, airline_code: str) -> Optional[Dict]:
        """Get airline information by code"""
        params = {'airlineCodes': airline_code}
        
        result = self._make_request('reference-data/airlines', params)
        if not result or 'data' not in result or not result['data']:
            return None
            
        airline = result['data'][0]
        return {
            'code': airline.get('iataCode'),
            'name': airline.get('commonName'),
            'business_name': airline.get('businessName')
        }

# Alternative Flight API Services (for backup/comparison)

class AviationstackService:
    """Alternative flight API service using Aviationstack"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.aviationstack.com/v1"
    
    def get_flight_status(self, flight_iata: str) -> Optional[Dict]:
        """Get real-time flight status"""
        params = {
            'access_key': self.api_key,
            'flight_iata': flight_iata
        }
        
        try:
            response = requests.get(f"{self.base_url}/flights", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('data'):
                flight = data['data'][0]
                return {
                    'flight_number': flight.get('flight', {}).get('iata'),
                    'status': flight.get('flight_status'),
                    'departure': flight.get('departure'),
                    'arrival': flight.get('arrival'),
                    'airline': flight.get('airline', {}).get('name')
                }
                
        except Exception as e:
            print(f"❌ Aviationstack API error: {e}")
            
        return None

class RapidAPIFlightService:
    """Flight service using RapidAPI Skyscanner endpoint"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://skyscanner-skyscanner-flight-search-v1.p.rapidapi.com/apiservices"
        
    def search_flights_rapid(self, origin: str, destination: str, departure_date: str) -> Dict:
        """Search flights using RapidAPI Skyscanner"""
        headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": "skyscanner-skyscanner-flight-search-v1.p.rapidapi.com"
        }
        
        params = {
            "originplace": f"{origin}-sky",
            "destinationplace": f"{destination}-sky", 
            "outbounddate": departure_date,
            "adults": 1
        }
        
        try:
            response = requests.get(
                f"{self.base_url}/browsequotes/v1.0/US/USD/en-US/{origin}/{destination}/{departure_date}",
                headers=headers,
                params=params,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            print(f"❌ RapidAPI Skyscanner error: {e}")
            return {'error': str(e)}
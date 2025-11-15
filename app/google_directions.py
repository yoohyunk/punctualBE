"""
Google Directions API integration module
"""
import os
import googlemaps
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple


class DirectionsService:
    """Google Directions API service"""
    
    def __init__(self):
        api_key = os.getenv('GOOGLE_MAPS_API_KEY')
        if not api_key:
            raise ValueError("GOOGLE_MAPS_API_KEY not set. Please check your .env file.")
        self.client = googlemaps.Client(key=api_key)
    
    def calculate_route(
        self,
        origin: str,
        destination: str,
        target_type: str,
        target_time: datetime
    ) -> Dict:
        """
        Calculate route and determine departure/arrival times
        
        Args:
            origin: Starting point (address or place name)
            destination: Destination (address or place name)
            target_type: 'DEPARTURE' or 'ARRIVAL'
            target_time: User's target time
        
        Returns:
            Dict: {
                'departure_time': datetime,
                'arrival_time': datetime,
                'duration_seconds': int,
                'distance_meters': int,
                'steps': List[Dict]  # Step-by-step route information
            }
        """
        try:
            # Determine API call method based on target_type
            if target_type == 'DEPARTURE':
                # Departure time basis: when will they arrive if leaving at this time
                directions = self.client.directions(
                    origin=origin,
                    destination=destination,
                    mode="transit",  # Public transit
                    departure_time=target_time,
                    alternatives=False
                )
                
                if not directions or len(directions) == 0:
                    raise ValueError("No route found")
                
                route = directions[0]
                leg = route['legs'][0]
                
                departure_time = target_time
                duration_seconds = leg['duration']['value']
                arrival_time = departure_time + timedelta(seconds=duration_seconds)
                
            else:  # ARRIVAL
                # Arrival time basis: when must they leave to arrive at this time
                directions = self.client.directions(
                    origin=origin,
                    destination=destination,
                    mode="transit",
                    arrival_time=target_time,
                    alternatives=False
                )
                
                if not directions or len(directions) == 0:
                    raise ValueError("No route found")
                
                route = directions[0]
                leg = route['legs'][0]
                
                arrival_time = target_time
                duration_seconds = leg['duration']['value']
                departure_time = arrival_time - timedelta(seconds=duration_seconds)
            
            # Distance information
            distance_meters = leg['distance']['value']
            
            # Extract step information (including transit details)
            steps = self._extract_steps(leg['steps'])
            
            return {
                'departure_time': departure_time,
                'arrival_time': arrival_time,
                'duration_seconds': duration_seconds,
                'distance_meters': distance_meters,
                'steps': steps,
                'success': True
            }
            
        except googlemaps.exceptions.ApiError as e:
            return {
                'success': False,
                'error': f'Google API error: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Route calculation error: {str(e)}'
            }
    
    def _extract_steps(self, steps: list) -> list:
        """
        Extract route step information (simplified)
        
        Args:
            steps: Steps data from Google Directions API
        
        Returns:
            List[Dict]: Simplified step information
        """
        extracted = []
        
        for step in steps:
            step_info = {
                'travel_mode': step.get('travel_mode'),
                'distance': step.get('distance', {}).get('text'),
                'duration': step.get('duration', {}).get('text'),
                'instructions': step.get('html_instructions', '').replace('<b>', '').replace('</b>', '')
            }
            
            # Add transit information if available
            if 'transit_details' in step:
                transit = step['transit_details']
                step_info['transit_details'] = transit  # Store full transit details
                step_info['transit'] = {
                    'type': transit.get('line', {}).get('vehicle', {}).get('type'),
                    'line_name': transit.get('line', {}).get('name'),
                    'line_short_name': transit.get('line', {}).get('short_name'),
                    'departure_stop': transit.get('departure_stop', {}).get('name'),
                    'arrival_stop': transit.get('arrival_stop', {}).get('name'),
                    'num_stops': transit.get('num_stops'),
                    'headsign': transit.get('headsign'),
                    'departure_time': transit.get('departure_time', {}).get('value'),  # Unix timestamp
                    'arrival_time': transit.get('arrival_time', {}).get('value'),  # Unix timestamp
                }
            
            extracted.append(step_info)
        
        return extracted


# Singleton instance
_directions_service: Optional[DirectionsService] = None


def get_directions_service() -> DirectionsService:
    """Get DirectionsService singleton instance"""
    global _directions_service
    if _directions_service is None:
        _directions_service = DirectionsService()
    return _directions_service


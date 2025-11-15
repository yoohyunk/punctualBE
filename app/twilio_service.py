"""
Twilio SMS notification service
"""
import os
from twilio.rest import Client
from typing import Optional


class TwilioService:
    """Twilio SMS service for sending notifications"""
    
    def __init__(self):
        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.from_number = os.getenv('TWILIO_PHONE_NUMBER')
        
        if not all([account_sid, auth_token, self.from_number]):
            raise ValueError(
                "Twilio credentials not set. Please check your .env file:\n"
                "TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER"
            )
        
        self.client = Client(account_sid, auth_token)
    
    def send_sms(self, to_number: str, message: str) -> dict:
        """
        Send SMS message
        
        Args:
            to_number: Recipient phone number (with country code)
            message: Message content
        
        Returns:
            dict: {'success': bool, 'message_sid': str or 'error': str}
        """
        try:
            message = self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=to_number
            )
            
            return {
                'success': True,
                'message_sid': message.sid,
                'status': message.status
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_wake_up_notification(self, to_number: str, departure_time: str, destination: str) -> dict:
        """
        Send wake up notification
        
        Args:
            to_number: Recipient phone number
            departure_time: When to leave (formatted string)
            destination: Where they're going
        
        Returns:
            dict: Result of SMS send
        """
        message = (
            f"⏰ Good morning! Time to wake up!\n\n"
            f"You need to leave at {departure_time} to reach {destination} on time.\n"
            f"Start getting ready!"
        )
        return self.send_sms(to_number, message)
    
    def send_departure_notification(
        self,
        to_number: str,
        destination: str,
        arrival_time: str,
        steps: list
    ) -> dict:
        """
        Send departure notification with route details
        
        Args:
            to_number: Recipient phone number
            destination: Where they're going
            arrival_time: Expected arrival time
            steps: Route steps from Google Directions
        
        Returns:
            dict: Result of SMS send
        """
        # Build route summary
        route_summary = []
        for step in steps[:3]:  # Show first 3 steps
            if 'transit' in step:
                transit = step['transit']
                route_summary.append(
                    f"🚌 {transit.get('line_short_name', 'Transit')}: "
                    f"{transit.get('departure_stop', '')} → {transit.get('arrival_stop', '')}"
                )
            elif step['travel_mode'] == 'WALKING':
                route_summary.append(f"🚶 Walk {step.get('distance', '')}")
        
        message = (
            f"🚪 Time to leave!\n\n"
            f"Destination: {destination}\n"
            f"Arrival: {arrival_time}\n\n"
            f"Route:\n" + "\n".join(route_summary) +
            f"\n\nHave a safe trip!"
        )
        return self.send_sms(to_number, message)
    
    def send_transit_arrival_notification(
        self,
        to_number: str,
        transit_info: dict,
        minutes_until: int = 3
    ) -> dict:
        """
        Send notification that transit is arriving soon
        
        Args:
            to_number: Recipient phone number
            transit_info: Transit details (line, stop, etc.)
            minutes_until: Minutes until arrival
        
        Returns:
            dict: Result of SMS send
        """
        line_name = transit_info.get('line_short_name', 'Your transit')
        stop_name = transit_info.get('departure_stop', 'the stop')
        
        message = (
            f"🚌 Transit Alert!\n\n"
            f"{line_name} is arriving at {stop_name} in {minutes_until} minutes.\n"
            f"Head to the stop now!"
        )
        return self.send_sms(to_number, message)


# Singleton instance
_twilio_service: Optional[TwilioService] = None


def get_twilio_service() -> TwilioService:
    """Get TwilioService singleton instance"""
    global _twilio_service
    if _twilio_service is None:
        _twilio_service = TwilioService()
    return _twilio_service


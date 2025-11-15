"""
Transit alert service logic with smart notifications
"""
from datetime import datetime, timedelta
from .models import db, TransitAlert
from .google_directions import get_directions_service
from .twilio_service import get_twilio_service


def round_to_quarter_hour(dt: datetime) -> datetime:
    """
    Round datetime to nearest quarter hour (0, 15, 30, 45 minutes)
    
    Args:
        dt: Datetime to round
    
    Returns:
        Rounded datetime
    """
    minute = dt.minute
    
    # Round to nearest 15-minute mark
    if minute < 8:
        rounded_minute = 0
    elif minute < 23:
        rounded_minute = 15
    elif minute < 38:
        rounded_minute = 30
    elif minute < 53:
        rounded_minute = 45
    else:
        # Round up to next hour
        dt = dt + timedelta(hours=1)
        rounded_minute = 0
    
    return dt.replace(minute=rounded_minute, second=0, microsecond=0)


def extract_first_transit_time(steps: list) -> tuple:
    """
    Extract when first transit arrives at the stop
    
    Args:
        steps: Route steps from Google Directions API
    
    Returns:
        tuple: (transit_time: datetime or None, transit_info: dict or None)
    """
    for step in steps:
        if 'transit' in step:
            transit_info = step['transit']
            # Get departure time from transit info
            dep_time_ts = transit_info.get('departure_time')
            if dep_time_ts:
                try:
                    from datetime import timezone
                    transit_time = datetime.fromtimestamp(dep_time_ts, tz=timezone.utc)
                    return transit_time, transit_info
                except:
                    pass
    
    return None, None


def calculate_and_update_route(alert_id: int):
    """
    Call Google Directions API and calculate all notification times
    
    Args:
        alert_id: Alert ID
    
    Returns:
        Tuple[TransitAlert, Dict]: (updated alert, calculation result)
    """
    alert = TransitAlert.query.get(alert_id)
    if not alert:
        return None, {'success': False, 'error': 'Alert not found'}
    
    try:
        # Call Google Directions API
        directions_service = get_directions_service()
        result = directions_service.calculate_route(
            origin=alert.origin_text,
            destination=alert.destination_text,
            target_type=alert.target_type,
            target_time=alert.target_time
        )
        
        if not result.get('success'):
            return alert, result
        
        # Save Google API results
        alert.calculated_departure_time = result['departure_time']
        alert.calculated_arrival_time = result['arrival_time']
        alert.total_duration_seconds = result['duration_seconds']
        
        # Calculate rounded departure time (0, 15, 30, 45 min)
        alert.rounded_departure_time = round_to_quarter_hour(result['departure_time'])
        
        # Calculate wake up time (departure - preparation time)
        prep_minutes = alert.preparation_minutes or 30
        alert.wake_up_time = alert.rounded_departure_time - timedelta(minutes=prep_minutes)
        
        # Extract first transit arrival time
        first_transit_time, transit_info = extract_first_transit_time(result.get('steps', []))
        if first_transit_time:
            alert.first_transit_stop_time = first_transit_time
            # Notify 3 minutes before transit arrives
            alert.transit_notify_time = first_transit_time - timedelta(minutes=3)
        
        alert.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Add transit info to result
        if transit_info:
            result['first_transit'] = transit_info
        
        return alert, result
        
    except Exception as e:
        return alert, {
            'success': False,
            'error': f'Route calculation error: {str(e)}'
        }


def send_wake_up_notification(alert_id: int) -> dict:
    """
    Send wake up notification via Twilio
    
    Args:
        alert_id: Alert ID
    
    Returns:
        dict: Send result
    """
    alert = TransitAlert.query.get(alert_id)
    if not alert:
        return {'success': False, 'error': 'Alert not found'}
    
    if alert.wake_up_sent:
        return {'success': False, 'error': 'Wake up notification already sent'}
    
    try:
        twilio = get_twilio_service()
        departure_time = alert.rounded_departure_time.strftime('%I:%M %p')
        
        result = twilio.send_wake_up_notification(
            to_number=alert.phone_number,
            departure_time=departure_time,
            destination=alert.destination_text
        )
        
        if result.get('success'):
            alert.wake_up_sent = True
            db.session.commit()
        
        return result
        
    except Exception as e:
        return {'success': False, 'error': str(e)}


def send_departure_notification(alert_id: int) -> dict:
    """
    Send departure notification via Twilio
    
    Args:
        alert_id: Alert ID
    
    Returns:
        dict: Send result
    """
    alert = TransitAlert.query.get(alert_id)
    if not alert:
        return {'success': False, 'error': 'Alert not found'}
    
    if alert.departure_sent:
        return {'success': False, 'error': 'Departure notification already sent'}
    
    try:
        # Get route steps again for notification
        directions_service = get_directions_service()
        result = directions_service.calculate_route(
            origin=alert.origin_text,
            destination=alert.destination_text,
            target_type=alert.target_type,
            target_time=alert.target_time
        )
        
        twilio = get_twilio_service()
        arrival_time = alert.calculated_arrival_time.strftime('%I:%M %p')
        
        sms_result = twilio.send_departure_notification(
            to_number=alert.phone_number,
            destination=alert.destination_text,
            arrival_time=arrival_time,
            steps=result.get('steps', [])
        )
        
        if sms_result.get('success'):
            alert.departure_sent = True
            db.session.commit()
        
        return sms_result
        
    except Exception as e:
        return {'success': False, 'error': str(e)}


def send_transit_notification(alert_id: int) -> dict:
    """
    Send transit arrival notification via Twilio
    
    Args:
        alert_id: Alert ID
    
    Returns:
        dict: Send result
    """
    alert = TransitAlert.query.get(alert_id)
    if not alert:
        return {'success': False, 'error': 'Alert not found'}
    
    if alert.transit_sent:
        return {'success': False, 'error': 'Transit notification already sent'}
    
    try:
        # Get route to find transit info
        directions_service = get_directions_service()
        result = directions_service.calculate_route(
            origin=alert.origin_text,
            destination=alert.destination_text,
            target_type=alert.target_type,
            target_time=alert.target_time
        )
        
        _, transit_info = extract_first_transit_time(result.get('steps', []))
        
        if not transit_info:
            return {'success': False, 'error': 'No transit information found'}
        
        twilio = get_twilio_service()
        sms_result = twilio.send_transit_arrival_notification(
            to_number=alert.phone_number,
            transit_info=transit_info,
            minutes_until=3
        )
        
        if sms_result.get('success'):
            alert.transit_sent = True
            db.session.commit()
        
        return sms_result
        
    except Exception as e:
        return {'success': False, 'error': str(e)}


def get_pending_alerts(notification_type: str = None) -> list:
    """
    Get pending alerts that need notifications
    
    Args:
        notification_type: 'wake_up', 'departure', or 'transit'
    
    Returns:
        List of alerts
    """
    query = TransitAlert.query.filter_by(status='PENDING')
    
    now = datetime.utcnow()
    
    if notification_type == 'wake_up':
        query = query.filter(
            TransitAlert.wake_up_sent == False,
            TransitAlert.wake_up_time <= now
        )
    elif notification_type == 'departure':
        query = query.filter(
            TransitAlert.departure_sent == False,
            TransitAlert.rounded_departure_time <= now
        )
    elif notification_type == 'transit':
        query = query.filter(
            TransitAlert.transit_sent == False,
            TransitAlert.transit_notify_time <= now
        )
    
    return query.all()


def mark_alert_complete(alert_id: int):
    """Mark alert as complete if all notifications sent"""
    alert = TransitAlert.query.get(alert_id)
    if alert and alert.wake_up_sent and alert.departure_sent and alert.transit_sent:
        alert.status = 'SENT'
        db.session.commit()
    return alert


def cancel_alert(alert_id: int):
    """Cancel an alert"""
    alert = TransitAlert.query.get(alert_id)
    if alert:
        alert.status = 'CANCELLED'
        alert.updated_at = datetime.utcnow()
        db.session.commit()
    return alert

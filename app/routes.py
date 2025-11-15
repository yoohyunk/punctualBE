from flask import Blueprint, request, jsonify
from datetime import datetime
from .models import db, TransitAlert
from .services import (
    calculate_and_update_route,
    send_wake_up_notification,
    send_departure_notification,
    send_transit_notification,
    cancel_alert,
    get_pending_alerts
)

main_bp = Blueprint("main", __name__)


@main_bp.get("/")
def home():
    return {"msg": "Punctual API - Smart Transit Alert Service"}


@main_bp.post("/test/sms")
def test_sms():
    """Send a test SMS to verify Twilio is working"""
    try:
        data = request.get_json()
        
        if not data or 'phone_number' not in data:
            return jsonify({"error": "phone_number is required"}), 400
        
        phone_number = data['phone_number']
        message = data.get('message', '🧪 Test SMS from Punctual!\n\nIf you received this, Twilio is working correctly! ✅')
        
        from .twilio_service import get_twilio_service
        twilio = get_twilio_service()
        
        result = twilio.send_sms(phone_number, message)
        
        if result.get('success'):
            return jsonify({
                "success": True,
                "message": "SMS sent successfully!",
                "message_sid": result.get('message_sid'),
                "to": phone_number
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": result.get('error')
            }), 400
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@main_bp.post("/alerts")
def create_alert():
    """Create new transit alert with automatic route calculation"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['phone_number', 'origin_text', 'destination_text', 'target_type', 'target_time']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Create new alert
        alert = TransitAlert(
            phone_number=data['phone_number'],
            origin_text=data['origin_text'],
            destination_text=data['destination_text'],
            target_type=data['target_type'],
            target_time=datetime.fromisoformat(data['target_time']),
            preparation_minutes=data.get('preparation_minutes', 30)
        )
        
        db.session.add(alert)
        db.session.commit()
        
        # Calculate route and notification times using Google Directions API
        alert, calculation_result = calculate_and_update_route(alert.id)
        
        response_data = alert.to_dict()
        
        # Add route calculation result
        if calculation_result.get('success'):
            response_data['route_calculation'] = {
                'success': True,
                'distance_meters': calculation_result.get('distance_meters'),
                'steps_count': len(calculation_result.get('steps', [])),
                'steps': calculation_result.get('steps', []),
                'first_transit': calculation_result.get('first_transit')
            }
        else:
            response_data['route_calculation'] = {
                'success': False,
                'error': calculation_result.get('error')
            }
        
        return jsonify(response_data), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


@main_bp.get("/alerts")
def get_alerts():
    """Get all alerts"""
    alerts = TransitAlert.query.all()
    return jsonify([alert.to_dict() for alert in alerts]), 200


@main_bp.get("/alerts/<int:alert_id>")
def get_alert(alert_id):
    """Get specific alert"""
    alert = TransitAlert.query.get_or_404(alert_id)
    return jsonify(alert.to_dict()), 200


@main_bp.put("/alerts/<int:alert_id>")
def update_alert(alert_id):
    """Update alert information"""
    try:
        alert = TransitAlert.query.get_or_404(alert_id)
        data = request.get_json()
        
        # Updatable fields
        updatable_fields = [
            'status', 'preparation_minutes'
        ]
        
        for field in updatable_fields:
            if field in data:
                setattr(alert, field, data[field])
        
        alert.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify(alert.to_dict()), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


@main_bp.post("/alerts/<int:alert_id>/recalculate")
def recalculate_route(alert_id):
    """Recalculate route for existing alert"""
    try:
        alert, calculation_result = calculate_and_update_route(alert_id)
        
        if not alert:
            return jsonify({"error": "Alert not found"}), 404
        
        response_data = alert.to_dict()
        
        # Add route calculation result
        if calculation_result.get('success'):
            response_data['route_calculation'] = {
                'success': True,
                'distance_meters': calculation_result.get('distance_meters'),
                'steps_count': len(calculation_result.get('steps', [])),
                'steps': calculation_result.get('steps', []),
                'first_transit': calculation_result.get('first_transit')
            }
        else:
            response_data['route_calculation'] = {
                'success': False,
                'error': calculation_result.get('error')
            }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@main_bp.post("/alerts/<int:alert_id>/notify/wake-up")
def notify_wake_up(alert_id):
    """Send wake up notification"""
    result = send_wake_up_notification(alert_id)
    
    if result.get('success'):
        return jsonify(result), 200
    else:
        return jsonify(result), 400


@main_bp.post("/alerts/<int:alert_id>/notify/departure")
def notify_departure(alert_id):
    """Send departure notification"""
    result = send_departure_notification(alert_id)
    
    if result.get('success'):
        return jsonify(result), 200
    else:
        return jsonify(result), 400


@main_bp.post("/alerts/<int:alert_id>/notify/transit")
def notify_transit(alert_id):
    """Send transit arrival notification"""
    result = send_transit_notification(alert_id)
    
    if result.get('success'):
        return jsonify(result), 200
    else:
        return jsonify(result), 400


@main_bp.post("/alerts/<int:alert_id>/cancel")
def cancel_alert_route(alert_id):
    """Cancel alert"""
    alert = cancel_alert(alert_id)
    
    if alert:
        return jsonify(alert.to_dict()), 200
    else:
        return jsonify({"error": "Alert not found"}), 404


@main_bp.get("/alerts/pending")
def get_pending_alerts_route():
    """Get pending alerts that need notifications"""
    notification_type = request.args.get('type')  # wake_up, departure, or transit
    
    alerts = get_pending_alerts(notification_type)
    return jsonify([alert.to_dict() for alert in alerts]), 200


@main_bp.delete("/alerts/<int:alert_id>")
def delete_alert(alert_id):
    """Delete alert"""
    try:
        alert = TransitAlert.query.get_or_404(alert_id)
        db.session.delete(alert)
        db.session.commit()
        return jsonify({"message": "Alert deleted successfully"}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

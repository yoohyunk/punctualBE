from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import BigInteger, String, Text, Integer, DateTime, Boolean
from sqlalchemy.sql import func
import enum

db = SQLAlchemy()


class TargetType(enum.Enum):
    """Route calculation basis"""
    DEPARTURE = "DEPARTURE"  # Based on departure time
    ARRIVAL = "ARRIVAL"      # Based on arrival time


class AlertStatus(enum.Enum):
    """Alert notification status"""
    PENDING = "PENDING"      # Not sent yet
    SENT = "SENT"           # Successfully sent
    FAILED = "FAILED"       # Failed to send
    CANCELLED = "CANCELLED"  # Cancelled by user


class NotificationType(enum.Enum):
    """Type of notification"""
    WAKE_UP = "WAKE_UP"                 # Wake up notification
    DEPARTURE = "DEPARTURE"             # Time to leave home
    TRANSIT_ARRIVAL = "TRANSIT_ARRIVAL" # Transit arriving soon (3 min before)


class TransitAlert(db.Model):
    """Transit alert model with smart notifications"""
    __tablename__ = 'transit_alerts'

    # Primary Key
    id = db.Column(Integer, primary_key=True, autoincrement=True)

    # User information
    phone_number = db.Column(String(20), nullable=False, comment='Phone number with country code (+1)')

    # Route information
    origin_text = db.Column(Text, nullable=False, comment='Starting point (e.g., Calgary Tower)')
    destination_text = db.Column(Text, nullable=False, comment='Destination (e.g., SAIT Main Campus)')

    # User's target time
    target_type = db.Column(String(20), nullable=False, comment='DEPARTURE or ARRIVAL')
    target_time = db.Column(DateTime(timezone=True), nullable=False, comment='User specified time')

    # Google API calculation results
    calculated_departure_time = db.Column(DateTime(timezone=True), comment='When to leave home')
    calculated_arrival_time = db.Column(DateTime(timezone=True), comment='Expected arrival time')
    total_duration_seconds = db.Column(Integer, comment='Total travel time in seconds')

    # Preparation time (from wake up to leaving home)
    preparation_minutes = db.Column(Integer, default=30, comment='Minutes needed to get ready (default 30 min)')

    # Smart notification times
    wake_up_time = db.Column(DateTime(timezone=True), comment='When to wake up')
    rounded_departure_time = db.Column(DateTime(timezone=True), comment='Departure time rounded to 0/15/30/45 min')
    first_transit_stop_time = db.Column(DateTime(timezone=True), comment='When first transit arrives at stop')
    transit_notify_time = db.Column(DateTime(timezone=True), comment='3 minutes before transit arrives')

    # Notification status flags
    wake_up_sent = db.Column(Boolean, default=False, comment='Wake up notification sent')
    departure_sent = db.Column(Boolean, default=False, comment='Departure notification sent')
    transit_sent = db.Column(Boolean, default=False, comment='Transit notification sent')

    # Overall status
    status = db.Column(String(20), nullable=False, default='PENDING', comment='Overall alert status')

    # Timestamps
    created_at = db.Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = db.Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f'<TransitAlert {self.id}: {self.origin_text} → {self.destination_text}>'

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'phone_number': self.phone_number,
            'origin_text': self.origin_text,
            'destination_text': self.destination_text,
            'target_type': self.target_type,
            'target_time': self.target_time.isoformat() if self.target_time else None,
            'calculated_departure_time': self.calculated_departure_time.isoformat() if self.calculated_departure_time else None,
            'calculated_arrival_time': self.calculated_arrival_time.isoformat() if self.calculated_arrival_time else None,
            'total_duration_seconds': self.total_duration_seconds,
            'preparation_minutes': self.preparation_minutes,
            'wake_up_time': self.wake_up_time.isoformat() if self.wake_up_time else None,
            'rounded_departure_time': self.rounded_departure_time.isoformat() if self.rounded_departure_time else None,
            'first_transit_stop_time': self.first_transit_stop_time.isoformat() if self.first_transit_stop_time else None,
            'transit_notify_time': self.transit_notify_time.isoformat() if self.transit_notify_time else None,
            'wake_up_sent': self.wake_up_sent,
            'departure_sent': self.departure_sent,
            'transit_sent': self.transit_sent,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
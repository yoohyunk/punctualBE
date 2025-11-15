"""
Notification scheduler
Automatically sends wake up, departure, and transit notifications at the right time
"""
from apscheduler.schedulers.background import BackgroundScheduler
from app import create_app
from app.services import (
    get_pending_alerts,
    send_wake_up_notification,
    send_departure_notification,
    send_transit_notification,
    mark_alert_complete
)
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_and_send_wake_up_notifications():
    """Check and send wake up notifications"""
    app = create_app()
    with app.app_context():
        alerts = get_pending_alerts('wake_up')
        logger.info(f"Found {len(alerts)} wake up notifications to send")
        
        for alert in alerts:
            try:
                result = send_wake_up_notification(alert.id)
                if result.get('success'):
                    logger.info(f"✅ Wake up notification sent for alert {alert.id}")
                else:
                    logger.error(f"❌ Failed to send wake up for alert {alert.id}: {result.get('error')}")
            except Exception as e:
                logger.error(f"❌ Error sending wake up for alert {alert.id}: {e}")


def check_and_send_departure_notifications():
    """Check and send departure notifications"""
    app = create_app()
    with app.app_context():
        alerts = get_pending_alerts('departure')
        logger.info(f"Found {len(alerts)} departure notifications to send")
        
        for alert in alerts:
            try:
                result = send_departure_notification(alert.id)
                if result.get('success'):
                    logger.info(f"✅ Departure notification sent for alert {alert.id}")
                else:
                    logger.error(f"❌ Failed to send departure for alert {alert.id}: {result.get('error')}")
            except Exception as e:
                logger.error(f"❌ Error sending departure for alert {alert.id}: {e}")


def check_and_send_transit_notifications():
    """Check and send transit arrival notifications"""
    app = create_app()
    with app.app_context():
        alerts = get_pending_alerts('transit')
        logger.info(f"Found {len(alerts)} transit notifications to send")
        
        for alert in alerts:
            try:
                result = send_transit_notification(alert.id)
                if result.get('success'):
                    logger.info(f"✅ Transit notification sent for alert {alert.id}")
                    # Mark alert as complete if all notifications sent
                    mark_alert_complete(alert.id)
                else:
                    logger.error(f"❌ Failed to send transit for alert {alert.id}: {result.get('error')}")
            except Exception as e:
                logger.error(f"❌ Error sending transit for alert {alert.id}: {e}")


def start_scheduler():
    """Start the notification scheduler"""
    scheduler = BackgroundScheduler()
    
    # Check every 30 seconds for notifications
    scheduler.add_job(
        check_and_send_wake_up_notifications,
        'interval',
        seconds=30,
        id='wake_up_check'
    )
    
    scheduler.add_job(
        check_and_send_departure_notifications,
        'interval',
        seconds=30,
        id='departure_check'
    )
    
    scheduler.add_job(
        check_and_send_transit_notifications,
        'interval',
        seconds=30,
        id='transit_check'
    )
    
    scheduler.start()
    logger.info("🚀 Notification scheduler started! Checking every 30 seconds...")
    
    return scheduler


if __name__ == "__main__":
    import time
    
    scheduler = start_scheduler()
    
    try:
        # Keep the script running
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logger.info("Scheduler stopped")


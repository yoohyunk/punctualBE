from app import create_app
import os

app = create_app()

if __name__ == "__main__":
    # For local development
    port = int(os.environ.get("PORT", 8080))
    app.run(debug=True, host='0.0.0.0', port=port)
# For production (gunicorn will use the app object directly)

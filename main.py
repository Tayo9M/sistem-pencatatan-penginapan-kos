# Import aplikasi Flask dari app.py
from app import app, db
import logging

# Export app untuk Gunicorn
# Variabel ini akan diakses oleh Gunicorn melalui "main:app"
app = app

# Inisialisasi aplikasi dengan context
with app.app_context():
    # Import models
    import models  # noqa: F401
    
    # Create tables
    db.create_all()
    logging.info("Database tables created")
    
    # Import routes (setelah app dan db sudah siap)
    import routes  # noqa: F401
    import pdf_routes  # noqa: F401
    
    # Import data initialization functions
    from routes import create_initial_data, initialize_rooms
    
    # Initialize data
    try:
        create_initial_data()
        initialize_rooms()
    except Exception as e:
        logging.error(f"Error initializing data: {e}")

# Untuk menjalankan aplikasi secara langsung (development)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

"""
Script untuk menginisialisasi data awal aplikasi.
Jalankan script ini setelah database dibuat.
"""

from app import app, db
from models import User, Property, Room
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_initial_users():
    """Membuat data pengguna awal"""
    users_data = [
        {
            'username': 'admin',
            'password': 'admin123',
            'role': 'admin',
            'location': None
        },
        {
            'username': 'manager1',
            'password': 'manager123',
            'role': 'manager',
            'location': 'KOS ANTAPANI'
        },
        {
            'username': 'manager2',
            'password': 'manager123',
            'role': 'manager',
            'location': 'KOS GURO'
        },
        {
            'username': 'manager3',
            'password': 'manager123',
            'role': 'manager',
            'location': 'KOS PESONA GRIYA'
        },
        {
            'username': 'staff1',
            'password': 'staff123',
            'role': 'staff',
            'location': 'KOS ANTAPANI'
        }
    ]
    
    for user_data in users_data:
        existing_user = User.query.filter_by(username=user_data['username']).first()
        if not existing_user:
            user = User()
            user.username = user_data['username']
            user.role = user_data['role']
            user.location = user_data['location']
            user.set_password(user_data['password'])
            db.session.add(user)
    
    db.session.commit()
    logger.info("Initial users created")

def create_initial_properties():
    """Membuat data properti awal"""
    properties_data = [
        {
            'name': 'KOS ANTAPANI',
            'address': 'Jl. Antapani No. 123, Bandung',
            'total_rooms': 21
        },
        {
            'name': 'KOS GURO',
            'address': 'Jl. Guro No. 456, Bandung',
            'total_rooms': 32
        },
        {
            'name': 'KOS PESONA GRIYA',
            'address': 'Jl. Pesona Griya No. 789, Bandung',
            'total_rooms': 33
        }
    ]
    
    for prop_data in properties_data:
        existing_property = Property.query.filter_by(name=prop_data['name']).first()
        if not existing_property:
            property = Property()
            property.name = prop_data['name']
            property.address = prop_data['address']
            property.total_rooms = prop_data['total_rooms']
            db.session.add(property)
    
    db.session.commit()
    logger.info("Initial properties created")

def create_initial_rooms():
    """Membuat data kamar awal"""
    # KOS ANTAPANI: 21 kamar Standard
    antapani = Property.query.filter_by(name='KOS ANTAPANI').first()
    
    if antapani:
        existing_rooms = Room.query.filter_by(property_id=antapani.id).count()
        
        if existing_rooms == 0:
            for i in range(1, 22):
                room = Room()
                room.number = f'A{i:02d}'
                room.property_id = antapani.id
                room.room_type = 'Standard'
                room.monthly_rate = 850000
                room.status = 'available'
                db.session.add(room)
    
    # KOS GURO: 10 Eksekutif, 22 Standard
    guro = Property.query.filter_by(name='KOS GURO').first()
    
    if guro:
        existing_rooms = Room.query.filter_by(property_id=guro.id).count()
        
        if existing_rooms == 0:
            # 10 Eksekutif
            for i in range(1, 11):
                room = Room()
                room.number = f'GE{i:02d}'
                room.property_id = guro.id
                room.room_type = 'Eksekutif'
                room.monthly_rate = 1250000
                room.status = 'available'
                db.session.add(room)
                
            # 22 Standard
            for i in range(1, 23):
                room = Room()
                room.number = f'GS{i:02d}'
                room.property_id = guro.id
                room.room_type = 'Standard'
                room.monthly_rate = 950000
                room.status = 'available'
                db.session.add(room)
    
    # KOS PESONA GRIYA: 33 Standard
    pesona = Property.query.filter_by(name='KOS PESONA GRIYA').first()
    
    if pesona:
        existing_rooms = Room.query.filter_by(property_id=pesona.id).count()
        
        if existing_rooms == 0:
            for i in range(1, 34):
                room = Room()
                room.number = f'P{i:02d}'
                room.property_id = pesona.id
                room.room_type = 'Standard'
                room.monthly_rate = 900000
                room.status = 'available'
                db.session.add(room)
    
    db.session.commit()
    logger.info("Initial rooms created")

def initialize_all_data():
    """Inisialisasi semua data awal"""
    with app.app_context():
        create_initial_users()
        create_initial_properties()
        create_initial_rooms()
        logger.info("All initial data created successfully")

if __name__ == "__main__":
    initialize_all_data()
from datetime import datetime
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='user')  # 'admin', 'manager', 'staff', 'viewer'
    location = db.Column(db.String(100))  # For property managers assigned to specific locations
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @property
    def is_admin(self):
        return self.role == 'admin'
        
    @property
    def is_manager(self):
        return self.role == 'manager' or self.role == 'admin'
        
    @property
    def is_staff(self):
        return self.role == 'staff' or self.role == 'manager' or self.role == 'admin'
    
    @property
    def is_viewer(self):
        return self.role == 'viewer'
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Property(db.Model):
    __tablename__ = 'properties'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200))
    total_rooms = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    rooms = db.relationship('Room', backref='property', lazy='dynamic')
    
class Room(db.Model):
    __tablename__ = 'rooms'
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String(10), nullable=False)
    property_id = db.Column(db.Integer, db.ForeignKey('properties.id'), nullable=False)
    room_type = db.Column(db.String(50), nullable=False)  # Standard, Deluxe, Executive, Studio, etc.
    monthly_rate = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='available')  # available, occupied, maintenance, etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    occupancy_records = db.relationship('OccupancyRecord', backref='room', lazy='dynamic')

class OccupancyRecord(db.Model):
    __tablename__ = 'occupancy_records'
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)
    month = db.Column(db.String(7), nullable=False)  # YYYY-MM format
    is_occupied = db.Column(db.Boolean, default=True)
    tenant_name = db.Column(db.String(100))
    payment_status = db.Column(db.String(20), default='unpaid')  # 'paid', 'unpaid', 'late'
    payment_date = db.Column(db.Date, nullable=True)  # Tanggal pembayaran
    payment_due_date = db.Column(db.Date, nullable=True)  # Tanggal jatuh tempo
    payment_months = db.Column(db.Integer, default=1)  # Jumlah bulan yang dibayar
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    def is_late(self):
        """Mengecek apakah pembayaran terlambat"""
        if self.payment_status == 'paid':
            return False
        if not self.payment_due_date:
            return False
        return self.payment_due_date < datetime.now().date()
        
    def get_paid_until(self):
        """Mendapatkan bulan terakhir yang sudah dibayar"""
        if self.payment_status != 'paid' or not self.payment_date:
            return None
            
        # Parse bulan saat ini
        year, month = map(int, self.month.split('-'))
        
        # Tambahkan jumlah bulan yang dibayar
        month = month + (self.payment_months - 1)
        
        # Atur ulang bulan dan tahun jika bulan > 12
        if month > 12:
            year += month // 12
            month = month % 12
            if month == 0:  # Jika hasil modulo 0, artinya bulan Desember
                month = 12
                year -= 1
                
        return f"{year}-{str(month).zfill(2)}"

class FinancialRecord(db.Model):
    __tablename__ = 'financial_records'
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('properties.id'), nullable=False)
    transaction_date = db.Column(db.Date, nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    transaction_type = db.Column(db.String(10), nullable=False)  # 'income' or 'expense'
    category = db.Column(db.String(50))  # Rent, Maintenance, Utilities, etc.
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    property = db.relationship('Property', backref='financial_records')
    user = db.relationship('User', backref='financial_records')
    
    def to_dict(self):
        """
        Mengkonversi FinancialRecord ke format dictionary untuk kalender
        """
        return {
            'id': self.id,
            'type': self.transaction_type,  # 'income' atau 'expense'
            'category': self.category or '',
            'amount': self.amount,
            'description': self.description or ''
        }

class NationalHoliday(db.Model):
    __tablename__ = 'national_holidays'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, unique=True)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

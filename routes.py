import io
import base64
import calendar
import logging
from datetime import datetime, date, timedelta
from collections import defaultdict
from functools import wraps

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

from flask import render_template, request, redirect, url_for, flash, session, jsonify, g
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash

from app import app, db
from models import User, Property, Room, OccupancyRecord, FinancialRecord, NationalHoliday
from auth_helpers import role_required, admin_required, manager_required, staff_required, property_access_required, get_user_properties
from pdf_generator import (generate_occupancy_pdf, generate_finance_pdf, 
                          generate_room_stats_pdf, generate_financial_stats_pdf)

# Setup Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Format rupiah function
def format_rupiah(value):
    return f"Rp {value:,.0f}".replace(",", ".")

# Register the filter for use in templates
app.jinja_env.filters['rupiah'] = format_rupiah

# Add current datetime to all templates
@app.context_processor
def inject_now():
    return {'now': datetime.now()}

# Formatter for matplotlib
def rupiah_formatter(x, pos):
    return f'Rp{x/1000:.0f}K'

# Initialize database with default data
def create_initial_data():
    # Create admin user if not exists
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        
    # Create default users with different roles
    default_users = [
        {'username': 'manager1', 'password': '1234', 'role': 'manager', 'location': 'KOS ANTAPANI'},
        {'username': 'manager2', 'password': '1234', 'role': 'manager', 'location': 'KOS GURO'},
        {'username': 'manager3', 'password': '1234', 'role': 'manager', 'location': 'KOS PESONA GRIYA'},
        {'username': 'staff1', 'password': '1234', 'role': 'staff', 'location': 'KOS ANTAPANI'},
        {'username': 'staff2', 'password': '1234', 'role': 'staff', 'location': 'KOS GURO'},
        {'username': 'staff3', 'password': '1234', 'role': 'staff', 'location': 'KOS PESONA GRIYA'},
        {'username': 'viewer1', 'password': '1234', 'role': 'viewer', 'location': ''}
    ]
    
    for user_data in default_users:
        if not User.query.filter_by(username=user_data['username']).first():
            user = User(
                username=user_data['username'], 
                role=user_data['role'],
                location=user_data.get('location', '')
            )
            user.set_password(user_data['password'])
            db.session.add(user)
    
    # Create default properties if not exist
    default_properties = [
        {'name': 'KOS ANTAPANI', 'address': 'Antapani, Bandung', 'total_rooms': 21},
        {'name': 'KOS GURO', 'address': 'Karawang', 'total_rooms': 32},
        {'name': 'KOS PESONA GRIYA', 'address': 'Karawang', 'total_rooms': 33}
    ]
    
    for prop_data in default_properties:
        if not Property.query.filter_by(name=prop_data['name']).first():
            property = Property(
                name=prop_data['name'],
                address=prop_data['address'],
                total_rooms=prop_data['total_rooms']
            )
            db.session.add(property)
    
    # Create default holidays if not exist
    default_holidays = {
        '2025-01-01': 'Tahun Baru Masehi',
        '2025-03-31': 'Hari Raya Nyepi',
        '2025-04-18': 'Wafat Isa Almasih',
        '2025-05-01': 'Hari Buruh',
        '2025-05-29': 'Kenaikan Isa Almasih',
        '2025-06-01': 'Hari Lahir Pancasila',
        '2025-06-06': 'Hari Raya Idul Adha',
        '2025-07-17': 'Tahun Baru Islam',
        '2025-08-17': 'Hari Kemerdekaan RI',
        '2025-10-06': 'Maulid Nabi Muhammad SAW',
        '2025-12-25': 'Hari Natal'
    }
    
    for holiday_date, holiday_name in default_holidays.items():
        date_obj = datetime.strptime(holiday_date, '%Y-%m-%d').date()
        if not NationalHoliday.query.filter_by(date=date_obj).first():
            holiday = NationalHoliday(date=date_obj, name=holiday_name)
            db.session.add(holiday)
    
    db.session.commit()
    logging.info("Initial data created")

# Initialize rooms based on property data
def initialize_rooms():
    # For KOS ANTAPANI: 21 kamar
    property_antapani = Property.query.filter_by(name='KOS ANTAPANI').first()
    if property_antapani:
        # Check if rooms already exist for this property
        existing_rooms = Room.query.filter_by(property_id=property_antapani.id).count()
        if existing_rooms == 0:
            # Create 11 Standard rooms
            for i in range(1, 12):
                room = Room(
                    number=f"ANT-Sta-{i}",
                    property_id=property_antapani.id,
                    room_type="Standard",
                    status='available',
                    monthly_rate=0  # Tarif akan diinput oleh pengelola
                )
                db.session.add(room)
            
            # Create 10 Eksekutif rooms
            for i in range(1, 11):
                room = Room(
                    number=f"ANT-Eks-{i}",
                    property_id=property_antapani.id,
                    room_type="Eksekutif",
                    status='available',
                    monthly_rate=0  # Tarif akan diinput oleh pengelola
                )
                db.session.add(room)
    
    # For KOS GURO: 32 kamar (22 standar, 10 eksekutif)
    property_guro = Property.query.filter_by(name='KOS GURO').first()
    if property_guro:
        # Check if rooms already exist for this property
        existing_rooms = Room.query.filter_by(property_id=property_guro.id).count()
        if existing_rooms == 0:
            # Create 22 Standard rooms
            for i in range(1, 23):
                room = Room(
                    number=f"GUR-Sta-{i}",
                    property_id=property_guro.id,
                    room_type="Standard",
                    status='available',
                    monthly_rate=0  # Tarif akan diinput oleh pengelola
                )
                db.session.add(room)
            
            # Create 10 Eksekutif rooms
            for i in range(1, 11):
                room = Room(
                    number=f"GUR-Eks-{i}",
                    property_id=property_guro.id,
                    room_type="Eksekutif",
                    status='available',
                    monthly_rate=0  # Tarif akan diinput oleh pengelola
                )
                db.session.add(room)
    
    # For KOS PESONA GRIYA: 33 kamar (semua standar)
    property_pesona = Property.query.filter_by(name='KOS PESONA GRIYA').first()
    if property_pesona:
        # Check if rooms already exist for this property
        existing_rooms = Room.query.filter_by(property_id=property_pesona.id).count()
        if existing_rooms == 0:
            # Create 33 Standard rooms
            for i in range(1, 34):
                room = Room(
                    number=f"PES-Sta-{i}",
                    property_id=property_pesona.id,
                    room_type="Standard",
                    status='available',
                    monthly_rate=0  # Tarif akan diinput oleh pengelola
                )
                db.session.add(room)
    
    db.session.commit()
    logging.info("Initial rooms created")

# Call the functions to create initial data
with app.app_context():
    create_initial_data()
    initialize_rooms()

# Auth routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash('Login berhasil!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Username atau password tidak valid', 'danger')
            
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logout berhasil!', 'success')
    return redirect(url_for('login'))

# Main routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/forbidden')
def forbidden():
    return render_template('forbidden.html')

@app.route('/dashboard')
@login_required
def dashboard():
    # Dapatkan properti yang dapat diakses oleh pengguna ini
    accessible_properties = get_user_properties()
    accessible_property_ids = [prop.id for prop in accessible_properties]
    
    # Get count of properties
    property_count = len(accessible_properties)
    
    # Get current month for filtering
    current_month = datetime.now().strftime('%Y-%m')
    start_date = datetime.strptime(f'{current_month}-01', '%Y-%m-%d').date()
    
    # Get next month to calculate end date
    year = int(current_month.split('-')[0])
    month = int(current_month.split('-')[1])
    
    if month == 12:
        next_year = year + 1
        next_month = 1
    else:
        next_year = year
        next_month = month + 1
        
    end_date = datetime.strptime(f'{next_year}-{next_month:02d}-01', '%Y-%m-%d').date()
    
    # Filter data berdasarkan properti yang dapat diakses pengguna
    if current_user.is_admin:
        # Admin melihat semua data
        room_count = Room.query.count()
        
        # Query income and expense for current month (all properties)
        income = db.session.query(db.func.sum(FinancialRecord.amount)).filter(
            FinancialRecord.transaction_type == 'income',
            FinancialRecord.transaction_date >= start_date,
            FinancialRecord.transaction_date < end_date
        ).scalar() or 0
        
        expense = db.session.query(db.func.sum(FinancialRecord.amount)).filter(
            FinancialRecord.transaction_type == 'expense',
            FinancialRecord.transaction_date >= start_date,
            FinancialRecord.transaction_date < end_date
        ).scalar() or 0
        
        # Get occupancy data (all properties)
        total_rooms = Room.query.count()
        occupied_rooms = Room.query.filter_by(status='occupied').count()
    else:
        # Filter data berdasarkan properti yang dapat diakses
        room_count = Room.query.filter(Room.property_id.in_(accessible_property_ids)).count()
        
        # Query income and expense for current month (filtered by accessible properties)
        income = db.session.query(db.func.sum(FinancialRecord.amount)).filter(
            FinancialRecord.transaction_type == 'income',
            FinancialRecord.transaction_date >= start_date,
            FinancialRecord.transaction_date < end_date,
            FinancialRecord.property_id.in_(accessible_property_ids)
        ).scalar() or 0
        
        expense = db.session.query(db.func.sum(FinancialRecord.amount)).filter(
            FinancialRecord.transaction_type == 'expense',
            FinancialRecord.transaction_date >= start_date,
            FinancialRecord.transaction_date < end_date,
            FinancialRecord.property_id.in_(accessible_property_ids)
        ).scalar() or 0
        
        # Get occupancy data (filtered by accessible properties)
        total_rooms = Room.query.filter(Room.property_id.in_(accessible_property_ids)).count()
        occupied_rooms = Room.query.filter(
            Room.property_id.in_(accessible_property_ids),
            Room.status == 'occupied'
        ).count()
    
    # Calculate occupancy rate - if no rooms are occupied, set it explicitly to 0
    if occupied_rooms == 0 or total_rooms == 0:
        occupancy_rate = 0
    else:
        occupancy_rate = (occupied_rooms / total_rooms * 100)
    
    return render_template(
        'dashboard.html',
        properties=accessible_properties,
        property_count=property_count,
        room_count=room_count,
        income=income,
        expense=expense,
        profit=income-expense,
        occupancy_rate=occupancy_rate
    )

# Room management routes
@app.route('/input_occupancy', methods=['GET', 'POST'])
@login_required
@staff_required  # Hanya Admin, Manager, dan Staff yang dapat mengakses
def input_occupancy():
    if request.method == 'POST':
        property_id = request.form.get('property_id')
        
        # Periksa apakah pengguna memiliki akses ke properti ini
        if not current_user.is_admin:
            # Dapatkan properti yang diizinkan
            allowed_properties = get_user_properties()
            allowed_property_ids = [str(prop.id) for prop in allowed_properties]
            
            if property_id not in allowed_property_ids:
                flash('Anda tidak memiliki akses untuk properti ini', 'danger')
                return redirect(url_for('dashboard'))
        
        room_type = request.form.get('room_type')
        month = request.form.get('month')
        is_occupied = 'is_occupied' in request.form
        tenant_name = request.form.get('tenant_name', '')
        notes = request.form.get('notes', '')
        monthly_rate = request.form.get('monthly_rate', 0)
        
        try:
            monthly_rate = int(monthly_rate)
        except ValueError:
            monthly_rate = 0
        
        # Get or create the room
        room = Room.query.filter_by(property_id=property_id, room_type=room_type).first()
        
        if not room:
            # Create a new room
            property_obj = Property.query.get(property_id)
            if property_obj:
                room_number = f"{property_obj.name[:3]}-{room_type[:3]}-{Room.query.count() + 1}"
                room = Room(
                    number=room_number,
                    property_id=property_id,
                    room_type=room_type,
                    status='occupied' if is_occupied else 'available',
                    monthly_rate=monthly_rate
                )
                db.session.add(room)
                db.session.flush()  # To get the room.id
            else:
                flash('Property tidak ditemukan', 'danger')
                return redirect(url_for('input_occupancy'))
        else:
            # Update existing room status and rate
            room.status = 'occupied' if is_occupied else 'available'
            room.monthly_rate = monthly_rate
        
        # Get payment status fields if room is occupied
        payment_status = 'unpaid'
        payment_due_date = None
        payment_months = 1
        
        if is_occupied:
            payment_status = request.form.get('payment_status', 'unpaid')
            payment_due_date_str = request.form.get('payment_due_date')
            
            # Parse due date if provided
            if payment_due_date_str:
                try:
                    payment_due_date = datetime.strptime(payment_due_date_str, '%Y-%m-%d').date()
                except ValueError:
                    payment_due_date = None
                    
            # Get payment months
            payment_months_str = request.form.get('payment_months', '1')
            try:
                payment_months = int(payment_months_str)
                if payment_months <= 0:
                    payment_months = 1
            except ValueError:
                payment_months = 1
        
        # Create occupancy record
        occupancy = OccupancyRecord(
            room_id=room.id,
            month=month,
            is_occupied=is_occupied,
            tenant_name=tenant_name,
            notes=notes,
            payment_status=payment_status,
            payment_due_date=payment_due_date,
            payment_months=payment_months,
            created_by=current_user.id
        )
        
        db.session.add(occupancy)
        
        # Jika status pembayaran adalah 'paid', tambahkan catatan finansial
        if is_occupied and payment_status == 'paid':
            # Dapatkan data kamar dan properti
            amount = monthly_rate * payment_months
            payment_date = datetime.now().date()
            
            # Pastikan property_id tersedia
            if hasattr(room, 'property_id') and room.property_id:
                property_id_for_record = room.property_id
            else:
                property_id_for_record = property_id
                
            # Buat catatan finansial untuk pembayaran sewa
            financial_record = FinancialRecord(
                property_id=property_id_for_record,
                transaction_date=payment_date,
                amount=amount,
                transaction_type='income',
                category='Sewa',
                description=f'Pembayaran sewa kamar {room.number} ({room.room_type}) oleh {tenant_name} untuk {payment_months} bulan',
                created_by=current_user.id
            )
            
            db.session.add(financial_record)
            flash(f'Catatan keuangan untuk pembayaran sewa telah dibuat: Rp {amount:,}', 'success')
        
        db.session.commit()
        
        flash('Data hunian berhasil disimpan', 'success')
        return redirect(url_for('input_occupancy'))
    
    # Tampilkan hanya properti yang diizinkan untuk pengguna ini
    properties = get_user_properties()
    return render_template('input_occupancy.html', properties=properties)

@app.route('/manage_occupancy')
@login_required
@staff_required  # Hanya Admin, Manager, dan Staff yang dapat mengakses
def manage_occupancy():
    # Dapatkan properti yang dapat diakses oleh pengguna ini
    accessible_properties = get_user_properties()
    accessible_property_ids = [prop.id for prop in accessible_properties]
    
    # Jika admin, tampilkan semua data
    if current_user.is_admin:
        records = db.session.query(
            OccupancyRecord, Room, Property
        ).join(
            Room, OccupancyRecord.room_id == Room.id
        ).join(
            Property, Room.property_id == Property.id
        ).order_by(
            OccupancyRecord.month.desc(), 
            Property.name
        ).all()
    else:
        # Filter data berdasarkan properti yang dapat diakses
        records = db.session.query(
            OccupancyRecord, Room, Property
        ).join(
            Room, OccupancyRecord.room_id == Room.id
        ).join(
            Property, Room.property_id == Property.id
        ).filter(
            Property.id.in_(accessible_property_ids)
        ).order_by(
            OccupancyRecord.month.desc(), 
            Property.name
        ).all()
    
    return render_template('manage_occupancy.html', records=records, properties=accessible_properties)

@app.route('/delete_occupancy/<int:record_id>', methods=['POST'])
@login_required
@manager_required  # Hanya Admin dan Manager yang dapat menghapus data
def delete_occupancy(record_id):
    record = OccupancyRecord.query.get_or_404(record_id)
    
    # Dapatkan informasi kamar dan properti
    room = Room.query.get(record.room_id)
    if not room:
        flash('Data kamar tidak ditemukan', 'danger')
        return redirect(url_for('manage_occupancy'))
        
    # Dapatkan properti yang dapat diakses oleh pengguna
    accessible_properties = get_user_properties()
    accessible_property_ids = [prop.id for prop in accessible_properties]
    
    # Periksa apakah pengguna memiliki akses ke properti ini
    if not current_user.is_admin and room.property_id not in accessible_property_ids:
        flash('Anda tidak memiliki akses untuk properti ini', 'danger')
        return redirect(url_for('dashboard'))
        
    # Optional: Only allow deletion by admin or the user who created it
    if current_user.role != 'admin' and record.created_by != current_user.id:
        flash('Anda tidak memiliki izin untuk menghapus data ini', 'danger')
        return redirect(url_for('manage_occupancy'))
    
    db.session.delete(record)
    db.session.commit()
    
    flash('Data hunian berhasil dihapus', 'success')
    return redirect(url_for('manage_occupancy'))

# Financial management routes
@app.route('/input_finance', methods=['GET', 'POST'])
@login_required
@staff_required  # Hanya Admin, Manager, dan Staff yang dapat mengakses
def input_finance():
    if request.method == 'POST':
        property_id = request.form.get('property_id')
        
        # Periksa apakah pengguna memiliki akses ke properti ini
        if not current_user.is_admin:
            # Dapatkan properti yang diizinkan
            allowed_properties = get_user_properties()
            allowed_property_ids = [str(prop.id) for prop in allowed_properties]
            
            if property_id not in allowed_property_ids:
                flash('Anda tidak memiliki akses untuk properti ini', 'danger')
                return redirect(url_for('dashboard'))
        
        transaction_date = datetime.strptime(request.form.get('transaction_date'), '%Y-%m-%d').date()
        amount = int(request.form.get('amount').replace('.', '').replace('Rp', '').strip())
        transaction_type = request.form.get('transaction_type')
        category = request.form.get('category')
        description = request.form.get('description', '')
        
        record = FinancialRecord(
            property_id=property_id,
            transaction_date=transaction_date,
            amount=amount,
            transaction_type=transaction_type,
            category=category,
            description=description,
            created_by=current_user.id
        )
        
        db.session.add(record)
        db.session.commit()
        
        flash('Data keuangan berhasil disimpan', 'success')
        return redirect(url_for('input_finance'))
    
    # Tampilkan hanya properti yang diizinkan untuk pengguna ini
    properties = get_user_properties()
    return render_template('input_finance.html', properties=properties)

@app.route('/manage_finance')
@login_required
@staff_required  # Hanya Admin, Manager, dan Staff yang dapat mengakses
def manage_finance():
    # Dapatkan properti yang dapat diakses oleh pengguna ini
    accessible_properties = get_user_properties()
    accessible_property_ids = [prop.id for prop in accessible_properties]
    
    # Jika admin, tampilkan semua data
    if current_user.is_admin:
        records = db.session.query(
            FinancialRecord, Property
        ).join(
            Property, FinancialRecord.property_id == Property.id
        ).order_by(
            FinancialRecord.transaction_date.desc()
        ).all()
    else:
        # Filter data berdasarkan properti yang dapat diakses
        records = db.session.query(
            FinancialRecord, Property
        ).join(
            Property, FinancialRecord.property_id == Property.id
        ).filter(
            Property.id.in_(accessible_property_ids)
        ).order_by(
            FinancialRecord.transaction_date.desc()
        ).all()
    
    return render_template('manage_finance.html', records=records, properties=accessible_properties)

@app.route('/delete_finance/<int:record_id>', methods=['POST'])
@login_required
def delete_finance(record_id):
    record = FinancialRecord.query.get_or_404(record_id)
    
    # Dapatkan properti yang dapat diakses oleh pengguna
    accessible_properties = get_user_properties()
    accessible_property_ids = [prop.id for prop in accessible_properties]
    
    # Periksa apakah pengguna memiliki akses ke properti ini
    if not current_user.is_admin and record.property_id not in accessible_property_ids:
        flash('Anda tidak memiliki akses untuk properti ini', 'danger')
        return redirect(url_for('dashboard'))
        
    # Optional: Only allow deletion by admin or the user who created it
    if current_user.role != 'admin' and record.created_by != current_user.id:
        flash('Anda tidak memiliki izin untuk menghapus data ini', 'danger')
        return redirect(url_for('manage_finance'))
    
    db.session.delete(record)
    db.session.commit()
    
    flash('Data keuangan berhasil dihapus', 'success')
    return redirect(url_for('manage_finance'))

# Report routes
@app.route('/reports')
@login_required
def reports():
    return render_template('reports.html')

@app.route('/room_stats')
@login_required
def room_stats():
    # Dapatkan properti yang dapat diakses oleh pengguna
    accessible_properties = get_user_properties()
    accessible_property_ids = [prop.id for prop in accessible_properties]
    
    # Filter room berdasarkan properti yang dapat diakses
    if current_user.is_admin:
        # Get room stats by type (all properties)
        room_types = db.session.query(Room.room_type, db.func.count(Room.id)).group_by(Room.room_type).all()
    else:
        # Get room stats by type (filtered by accessible properties)
        room_types = db.session.query(Room.room_type, db.func.count(Room.id)).filter(
            Room.property_id.in_(accessible_property_ids)
        ).group_by(Room.room_type).all()
    
    # Get occupancy rate by month and room type
    current_year = datetime.now().year
    months = []
    for i in range(1, 13):
        month_str = f"{current_year}-{i:02d}"
        months.append(month_str)
    
    occupancy_data = {}
    room_types_list = [rt[0] for rt in room_types]
    
    for room_type in room_types_list:
        occupancy_data[room_type] = []
        for month in months:
            # Get occupancy records for this month and room type
            if current_user.is_admin:
                records = db.session.query(OccupancyRecord).join(Room).filter(
                    Room.room_type == room_type,
                    OccupancyRecord.month == month
                ).all()
            else:
                records = db.session.query(OccupancyRecord).join(Room).filter(
                    Room.room_type == room_type,
                    OccupancyRecord.month == month,
                    Room.property_id.in_(accessible_property_ids)
                ).all()
            
            occupied = sum(1 for r in records if r.is_occupied)
            total = len(records) if records else 0
            
            occupancy_rate = (occupied / total * 100) if total > 0 else 0
            occupancy_data[room_type].append(occupancy_rate)
    
    # Generate room stats chart
    plt.figure(figsize=(10, 6))
    plt.bar([rt[0] for rt in room_types], [rt[1] for rt in room_types], color='purple')
    plt.title('Jumlah Kamar per Tipe')
    plt.xlabel('Tipe Kamar')
    plt.ylabel('Jumlah')
    plt.tight_layout()
    
    room_stats_img = io.BytesIO()
    plt.savefig(room_stats_img, format='png')
    room_stats_img.seek(0)
    room_stats_plot = base64.b64encode(room_stats_img.getvalue()).decode()
    plt.close()
    
    # Generate occupancy rate chart
    plt.figure(figsize=(12, 6))
    for i, room_type in enumerate(room_types_list):
        plt.plot(
            [m.split('-')[1] for m in months],  # Just show month number
            occupancy_data[room_type],
            marker='o',
            label=room_type
        )
    
    plt.title('Tingkat Hunian per Bulan dan Tipe Kamar')
    plt.xlabel('Bulan')
    plt.ylabel('Tingkat Hunian (%)')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    
    occupancy_img = io.BytesIO()
    plt.savefig(occupancy_img, format='png')
    occupancy_img.seek(0)
    occupancy_plot = base64.b64encode(occupancy_img.getvalue()).decode()
    plt.close()
    
    return render_template(
        'room_stats.html',
        room_stats_plot=room_stats_plot,
        occupancy_plot=occupancy_plot,
        room_types=room_types,
        occupancy_data=occupancy_data,
        months=[m.split('-')[1] for m in months]
    )

@app.route('/financial_stats')
@login_required
def financial_stats():
    # Dapatkan properti yang dapat diakses oleh pengguna
    accessible_properties = get_user_properties()
    accessible_property_ids = [prop.id for prop in accessible_properties]
    
    # Get income and expense by month
    current_year = datetime.now().year
    months = []
    income_by_month = []
    expense_by_month = []
    
    for i in range(1, 13):
        month_str = f"{current_year}-{i:02d}"
        start_date = datetime.strptime(f'{month_str}-01', '%Y-%m-%d').date()
        
        # Calculate end date
        if i == 12:
            end_date = datetime.strptime(f'{current_year + 1}-01-01', '%Y-%m-%d').date()
        else:
            end_date = datetime.strptime(f'{current_year}-{i+1:02d}-01', '%Y-%m-%d').date()
        
        # Query income and expense for this month
        if current_user.is_admin:
            # Admin melihat data semua properti
            income = db.session.query(db.func.sum(FinancialRecord.amount)).filter(
                FinancialRecord.transaction_type == 'income',
                FinancialRecord.transaction_date >= start_date,
                FinancialRecord.transaction_date < end_date
            ).scalar() or 0
            
            expense = db.session.query(db.func.sum(FinancialRecord.amount)).filter(
                FinancialRecord.transaction_type == 'expense',
                FinancialRecord.transaction_date >= start_date,
                FinancialRecord.transaction_date < end_date
            ).scalar() or 0
        else:
            # Pengguna lain hanya melihat data properti yang dapat diakses
            income = db.session.query(db.func.sum(FinancialRecord.amount)).filter(
                FinancialRecord.transaction_type == 'income',
                FinancialRecord.transaction_date >= start_date,
                FinancialRecord.transaction_date < end_date,
                FinancialRecord.property_id.in_(accessible_property_ids)
            ).scalar() or 0
            
            expense = db.session.query(db.func.sum(FinancialRecord.amount)).filter(
                FinancialRecord.transaction_type == 'expense',
                FinancialRecord.transaction_date >= start_date,
                FinancialRecord.transaction_date < end_date,
                FinancialRecord.property_id.in_(accessible_property_ids)
            ).scalar() or 0
        
        months.append(calendar.month_name[i])
        income_by_month.append(income)
        expense_by_month.append(expense)
    
    # Generate income vs expense chart
    plt.figure(figsize=(12, 6))
    x = range(len(months))
    plt.bar(x, income_by_month, width=0.4, label='Pendapatan', align='center', color='green')
    plt.bar([i + 0.4 for i in x], expense_by_month, width=0.4, label='Pengeluaran', align='center', color='orange')
    plt.xticks([i + 0.2 for i in x], months, rotation=45)
    plt.title('Perbandingan Pendapatan dan Pengeluaran Bulanan')
    plt.xlabel('Bulan')
    plt.ylabel('Jumlah (Rp)')
    plt.gca().yaxis.set_major_formatter(FuncFormatter(rupiah_formatter))
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    
    income_expense_img = io.BytesIO()
    plt.savefig(income_expense_img, format='png')
    income_expense_img.seek(0)
    income_expense_plot = base64.b64encode(income_expense_img.getvalue()).decode()
    plt.close()
    
    # Get income and expense by category
    if current_user.is_admin:
        # Admin melihat semua data
        income_by_category = db.session.query(
            FinancialRecord.category,
            db.func.sum(FinancialRecord.amount)
        ).filter(
            FinancialRecord.transaction_type == 'income'
        ).group_by(FinancialRecord.category).all()
        
        expense_by_category = db.session.query(
            FinancialRecord.category,
            db.func.sum(FinancialRecord.amount)
        ).filter(
            FinancialRecord.transaction_type == 'expense'
        ).group_by(FinancialRecord.category).all()
    else:
        # Pengguna lain hanya melihat data properti yang dapat diakses
        income_by_category = db.session.query(
            FinancialRecord.category,
            db.func.sum(FinancialRecord.amount)
        ).filter(
            FinancialRecord.transaction_type == 'income',
            FinancialRecord.property_id.in_(accessible_property_ids)
        ).group_by(FinancialRecord.category).all()
        
        expense_by_category = db.session.query(
            FinancialRecord.category,
            db.func.sum(FinancialRecord.amount)
        ).filter(
            FinancialRecord.transaction_type == 'expense',
            FinancialRecord.property_id.in_(accessible_property_ids)
        ).group_by(FinancialRecord.category).all()
    
    # Generate income by category chart
    plt.figure(figsize=(10, 6))
    if income_by_category:
        plt.pie(
            [x[1] for x in income_by_category],
            labels=[x[0] for x in income_by_category],
            autopct='%1.1f%%',
            startangle=90,
            shadow=True
        )
        plt.axis('equal')
        plt.title('Pendapatan per Kategori')
    else:
        plt.text(0.5, 0.5, 'Tidak ada data pendapatan', horizontalalignment='center', verticalalignment='center')
    
    income_category_img = io.BytesIO()
    plt.savefig(income_category_img, format='png')
    income_category_img.seek(0)
    income_category_plot = base64.b64encode(income_category_img.getvalue()).decode()
    plt.close()
    
    # Generate expense by category chart
    plt.figure(figsize=(10, 6))
    if expense_by_category:
        plt.pie(
            [x[1] for x in expense_by_category],
            labels=[x[0] for x in expense_by_category],
            autopct='%1.1f%%',
            startangle=90,
            shadow=True
        )
        plt.axis('equal')
        plt.title('Pengeluaran per Kategori')
    else:
        plt.text(0.5, 0.5, 'Tidak ada data pengeluaran', horizontalalignment='center', verticalalignment='center')
    
    expense_category_img = io.BytesIO()
    plt.savefig(expense_category_img, format='png')
    expense_category_img.seek(0)
    expense_category_plot = base64.b64encode(expense_category_img.getvalue()).decode()
    plt.close()
    
    return render_template(
        'financial_stats.html',
        income_expense_plot=income_expense_plot,
        income_category_plot=income_category_plot,
        expense_category_plot=expense_category_plot,
        months=months,
        income_by_month=income_by_month,
        expense_by_month=expense_by_month
    )

@app.route('/calendar')
@login_required
def view_calendar():
    # Get current year and month
    year = request.args.get('year', type=int) or datetime.now().year
    month = request.args.get('month', type=int) or datetime.now().month
    
    # Get calendar for this month
    cal = calendar.monthcalendar(year, month)
    
    # Get national holidays for this month
    holidays = {}
    for holiday in NationalHoliday.query.filter(
        db.extract('year', NationalHoliday.date) == year,
        db.extract('month', NationalHoliday.date) == month
    ).all():
        day = holiday.date.day
        holidays[day] = holiday.name
    
    # Get financial records for this month
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)
    
    financial_records = FinancialRecord.query.filter(
        FinancialRecord.transaction_date >= start_date,
        FinancialRecord.transaction_date < end_date
    ).order_by(FinancialRecord.transaction_date).all()
    
    # Organize records by day
    records_by_day = defaultdict(list)
    for record in financial_records:
        day = record.transaction_date.day
        records_by_day[day].append(record)
    
    # Generate calendar data
    month_name = calendar.month_name[month]
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1
    
    return render_template(
        'calendar.html',
        calendar=cal,
        month=month,
        year=year,
        month_name=month_name,
        holidays=holidays,
        records_by_day=records_by_day,
        prev_month=prev_month,
        prev_year=prev_year,
        next_month=next_month,
        next_year=next_year
    )

# API endpoints for AJAX calls
@app.route('/api/rooms_by_property/<int:property_id>')
@login_required
def rooms_by_property(property_id):
    rooms = Room.query.filter_by(property_id=property_id).all()
    return jsonify([{'id': r.id, 'number': r.number, 'type': r.room_type} for r in rooms])

@app.route('/api/update_room_rate', methods=['POST'])
@login_required
def update_room_rate():
    room_id = request.form.get('room_id')
    new_rate = request.form.get('rate')
    
    try:
        room = Room.query.get(room_id)
        if room:
            room.monthly_rate = int(new_rate.replace('.', '').replace('Rp', '').strip())
            db.session.commit()
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Room not found'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# -------------------- User Management Routes --------------------

@app.route('/manage_users')
@admin_required
def manage_users():
    """
    Halaman manajemen pengguna - hanya admin yang dapat mengakses
    """
    users = User.query.all()
    properties = Property.query.all()
    return render_template('manage_users.html', 
                           users=users, 
                           properties=properties,
                           title='Manajemen Pengguna')

@app.route('/change_user_password/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def change_user_password(user_id):
    """
    Halaman untuk admin mengganti password pengguna lain
    """
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not new_password or len(new_password) < 4:
            flash('Password harus minimal 4 karakter', 'danger')
        elif new_password != confirm_password:
            flash('Password konfirmasi tidak sama', 'danger')
        else:
            user.set_password(new_password)
            db.session.commit()
            flash(f'Password untuk {user.username} berhasil diubah', 'success')
            return redirect(url_for('manage_users'))
    
    return render_template('change_password.html', 
                          user=user, 
                          is_admin_change=True,
                          title=f'Ubah Password - {user.username}')

@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    """
    Halaman untuk pengguna mengganti password sendiri
    """
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not current_user.check_password(current_password):
            flash('Password saat ini tidak sesuai', 'danger')
        elif not new_password or len(new_password) < 4:
            flash('Password baru harus minimal 4 karakter', 'danger')
        elif new_password != confirm_password:
            flash('Password konfirmasi tidak sama', 'danger')
        else:
            current_user.set_password(new_password)
            db.session.commit()
            flash('Password berhasil diubah', 'success')
            return redirect(url_for('dashboard'))
    
    return render_template('change_password.html', 
                          user=current_user, 
                          is_admin_change=False,
                          title='Ubah Password')

# ------------------------------- Fitur Pembayaran Sewa ------------------------------- #

@app.route('/payment_status')
@login_required
def payment_status():
    """
    Halaman untuk melihat status pembayaran sewa
    """
    year = datetime.now().year
    month = datetime.now().month
    
    # Get filter parameters
    year = request.args.get('year', str(year))
    month = request.args.get('month', str(month).zfill(2))
    status = request.args.get('status', 'all')
    month_key = f"{year}-{month}"
    
    # Get properties based on user role
    properties = get_user_properties()
    
    # Create a dictionary to store results by property
    property_data = {}
    late_payments = 0
    unpaid_payments = 0
    paid_payments = 0
    total_rooms = 0
    
    for prop in properties:
        # Get all rooms for the property
        rooms = Room.query.filter_by(property_id=prop.id).all()
        total_rooms += len(rooms)
        
        # Initialize property data
        if prop.name not in property_data:
            property_data[prop.name] = {
                'rooms': [],
                'late': 0,
                'unpaid': 0,
                'paid': 0,
                'total': 0
            }
        
        # Process each room
        for room in rooms:
            # Get occupancy record for the month if exists
            occupancy = OccupancyRecord.query.filter_by(
                room_id=room.id,
                month=month_key
            ).first()
            
            if occupancy and occupancy.is_occupied:
                # Format the paid until date nicely if it exists
                paid_until = None
                if occupancy.payment_status == 'paid' and occupancy.payment_months > 1:
                    paid_until_raw = occupancy.get_paid_until()
                    if paid_until_raw:
                        year_until, month_until = paid_until_raw.split('-')
                        month_names = {
                            '01': 'Januari', '02': 'Februari', '03': 'Maret', '04': 'April',
                            '05': 'Mei', '06': 'Juni', '07': 'Juli', '08': 'Agustus',
                            '09': 'September', '10': 'Oktober', '11': 'November', '12': 'Desember'
                        }
                        paid_until = f"{month_names[month_until]} {year_until}"
                
                payment_info = {
                    'room': room,
                    'occupancy': occupancy,
                    'tenant': occupancy.tenant_name,
                    'status': occupancy.payment_status,
                    'due_date': occupancy.payment_due_date,
                    'payment_date': occupancy.payment_date,
                    'is_late': occupancy.is_late(),
                    'paid_until': paid_until
                }
                
                # Filter by status if needed
                if status == 'all' or status == occupancy.payment_status:
                    property_data[prop.name]['rooms'].append(payment_info)
                
                # Update counters
                if occupancy.payment_status == 'paid':
                    property_data[prop.name]['paid'] += 1
                    paid_payments += 1
                elif occupancy.payment_status == 'late' or occupancy.is_late():
                    property_data[prop.name]['late'] += 1
                    late_payments += 1
                else:
                    property_data[prop.name]['unpaid'] += 1
                    unpaid_payments += 1
                
                property_data[prop.name]['total'] += 1
    
    # Calculate summary statistics
    total_payments = late_payments + unpaid_payments + paid_payments
    late_percent = (late_payments / total_payments * 100) if total_payments > 0 else 0
    unpaid_percent = (unpaid_payments / total_payments * 100) if total_payments > 0 else 0
    paid_percent = (paid_payments / total_payments * 100) if total_payments > 0 else 0
    
    # Prepare month and year options for filter
    months = [
        ('01', 'Januari'), ('02', 'Februari'), ('03', 'Maret'),
        ('04', 'April'), ('05', 'Mei'), ('06', 'Juni'),
        ('07', 'Juli'), ('08', 'Agustus'), ('09', 'September'),
        ('10', 'Oktober'), ('11', 'November'), ('12', 'Desember')
    ]
    
    current_year = datetime.now().year
    years = [str(y) for y in range(current_year - 2, current_year + 1)]
    
    return render_template(
        'payment_status.html',
        property_data=property_data,
        months=months,
        selected_month=month,
        years=years,
        selected_year=year,
        selected_status=status,
        late_payments=late_payments,
        unpaid_payments=unpaid_payments,
        paid_payments=paid_payments,
        late_percent=late_percent,
        unpaid_percent=unpaid_percent,
        paid_percent=paid_percent,
        total_payments=total_payments,
        title='Status Pembayaran Sewa'
    )

@app.route('/update_payment_status/<int:record_id>', methods=['POST'])
@login_required
def update_payment_status(record_id):
    """
    Update status pembayaran
    """
    status = request.form.get('status')
    payment_date_str = request.form.get('payment_date')
    due_date_str = request.form.get('due_date')
    payment_months_str = request.form.get('payment_months', '1')
    
    # Validate required fields
    if not status:
        flash('Status pembayaran harus dipilih', 'danger')
        return redirect(url_for('payment_status'))
    
    try:
        # Get the record
        record = OccupancyRecord.query.get_or_404(record_id)
        
        # Check if user has access to this property
        room = Room.query.get(record.room_id)
        if not current_user.is_admin and current_user.location != room.property.name:
            flash('Anda tidak memiliki akses untuk mengubah data ini', 'danger')
            return redirect(url_for('payment_status'))
        
        # Update payment status
        record.payment_status = status
        
        # Update payment months
        try:
            payment_months = int(payment_months_str)
            if payment_months < 1:
                payment_months = 1
            record.payment_months = payment_months
        except (ValueError, TypeError):
            record.payment_months = 1
        
        # Simpan status lama untuk perbandingan
        old_status = record.payment_status
        
        # Update payment date if provided
        if payment_date_str:
            record.payment_date = datetime.strptime(payment_date_str, '%Y-%m-%d').date()
        else:
            record.payment_date = datetime.now().date() if status == 'paid' else None
        
        # Update due date if provided
        if due_date_str:
            record.payment_due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
        
        # Jika status berubah dari unpaid/late menjadi paid, tambahkan catatan finansial
        if status == 'paid' and old_status != 'paid':
            # Dapatkan data kamar dan properti
            room = Room.query.get(record.room_id)
            if room and hasattr(room, 'property_id') and room.property_id:
                property_id = room.property_id
                amount = room.monthly_rate * record.payment_months
                payment_date = record.payment_date or datetime.now().date()
                
                # Buat catatan finansial untuk pembayaran sewa
                financial_record = FinancialRecord(
                    property_id=property_id,
                    transaction_date=payment_date,
                    amount=amount,
                    transaction_type='income',
                    category='Sewa',
                    description=f'Pembayaran sewa kamar {room.number} ({room.room_type}) oleh {record.tenant_name} untuk {record.payment_months} bulan',
                    created_by=current_user.id
                )
                
                db.session.add(financial_record)
                flash(f'Catatan keuangan untuk pembayaran sewa telah dibuat: Rp {amount:,}', 'success')
        
        db.session.commit()
        flash('Status pembayaran berhasil diperbarui', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Terjadi kesalahan: {str(e)}', 'danger')
    
    return redirect(url_for('payment_status'))
# ============= PDF EXPORT ROUTES =============

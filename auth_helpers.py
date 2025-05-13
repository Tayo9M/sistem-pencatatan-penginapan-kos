from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user

def role_required(roles):
    """
    Decorator untuk membatasi akses berdasarkan peran pengguna
    Membutuhkan list peran (roles) yang diizinkan untuk mengakses
    contoh: @role_required(['admin', 'manager'])
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Anda harus login terlebih dahulu untuk mengakses halaman ini', 'warning')
                return redirect(url_for('login'))
            
            if current_user.role not in roles:
                flash('Anda tidak memiliki hak akses untuk halaman ini', 'danger')
                return redirect(url_for('dashboard'))
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    """
    Decorator untuk membatasi akses hanya untuk admin
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Akses ditolak. Fitur ini hanya untuk administrator', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def manager_required(f):
    """
    Decorator untuk membatasi akses untuk manager dan admin
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_manager:
            flash('Akses ditolak. Fitur ini hanya untuk pengelola', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def staff_required(f):
    """
    Decorator untuk membatasi akses untuk staff, manager, dan admin
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_staff:
            flash('Akses ditolak. Fitur ini hanya untuk staf', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def property_access_required(f):
    """
    Decorator untuk memeriksa akses ke properti tertentu
    Hanya admin yang memiliki akses ke semua properti
    Manager dan staff hanya dapat mengakses properti yang ditugaskan kepada mereka
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Anda harus login terlebih dahulu untuk mengakses halaman ini', 'warning')
            return redirect(url_for('login'))
            
        # Admin memiliki akses ke semua properti
        if current_user.is_admin:
            return f(*args, **kwargs)
            
        # Cek properti_id dari parameter URL
        property_id = kwargs.get('property_id')
        if property_id is not None and current_user.location:
            # Periksa apakah property_id ada dalam daftar lokasi yang diizinkan untuk pengguna ini
            allowed_locations = [loc.strip() for loc in current_user.location.split(',')]
            # Konversi property_id ke string untuk perbandingan dengan nama properti
            if str(property_id) in allowed_locations:
                return f(*args, **kwargs)
                
        flash('Anda tidak memiliki hak akses untuk properti ini', 'danger')
        return redirect(url_for('dashboard'))
        
    return decorated_function

def get_user_properties():
    """
    Fungsi helper untuk mendapatkan daftar properti yang dapat diakses oleh pengguna saat ini
    Admin dapat mengakses semua properti
    Manager dan staff hanya dapat mengakses properti yang ditugaskan
    """
    from models import Property
    
    # Admin dapat mengakses semua properti
    if current_user.is_admin:
        return Property.query.all()
    
    # Pengguna lain hanya dapat mengakses properti yang ditugaskan
    if current_user.location:
        allowed_locations = [loc.strip() for loc in current_user.location.split(',')]
        return Property.query.filter(Property.name.in_(allowed_locations)).all()
    
    # Jika tidak ada lokasi yang ditetapkan, tidak ada properti yang bisa diakses
    return []
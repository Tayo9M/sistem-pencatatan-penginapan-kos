from flask import request, flash, redirect, url_for, render_template
from datetime import datetime, date, timedelta
from collections import defaultdict
import urllib.parse
from flask_login import login_required, current_user

from app import app, db
from models import Property, Room, OccupancyRecord, FinancialRecord
from auth_helpers import admin_required, property_access_required, get_user_properties
from pdf_generator import (generate_occupancy_pdf, generate_finance_pdf, 
                         generate_room_stats_pdf, generate_financial_stats_pdf)


@app.route('/preview_pdf')
@login_required
def preview_pdf():
    """
    Menampilkan halaman preview PDF
    """
    pdf_url = request.args.get('pdf_url', '')
    back_url = request.args.get('back_url', url_for('dashboard'))
    
    if not pdf_url:
        flash('URL PDF tidak valid.', 'danger')
        return redirect(back_url)
    
    return render_template('pdf_preview.html', pdf_url=pdf_url, back_url=back_url)

@app.route('/export_occupancy_pdf')
@login_required
@property_access_required
def export_occupancy_pdf():
    """
    Mengekspor data hunian ke PDF
    """
    property_id = request.args.get('property_id', type=int)
    start_month = request.args.get('start_month', datetime.now().strftime('%Y-%m'))
    end_month = request.args.get('end_month', start_month)
    preview = request.args.get('preview', 'false') == 'true'
    
    # Validasi format bulan
    try:
        datetime.strptime(start_month, '%Y-%m')
        datetime.strptime(end_month, '%Y-%m')
    except ValueError:
        flash('Format bulan tidak valid. Gunakan format YYYY-MM.', 'danger')
        return redirect(url_for('manage_occupancy'))
    
    if not property_id:
        flash('Properti tidak valid.', 'danger')
        return redirect(url_for('manage_occupancy'))
    
    # Pastikan pengguna memiliki akses ke properti
    accessible_properties = get_user_properties()
    property_data = next((p for p in accessible_properties if p.id == property_id), None)
    
    if not property_data:
        flash('Anda tidak memiliki akses ke properti ini.', 'danger')
        return redirect(url_for('manage_occupancy'))
    
    # Ambil data hunian untuk rentang bulan yang diminta
    occupancy_records = OccupancyRecord.query.join(Room).filter(
        Room.property_id == property_id,
        OccupancyRecord.month >= start_month,
        OccupancyRecord.month <= end_month
    ).order_by(OccupancyRecord.month, Room.number).all()
    
    # Jika mode preview, arahkan ke halaman preview
    if preview:
        pdf_url = generate_occupancy_pdf(
            property_id=property_id,
            start_month=start_month,
            end_month=end_month,
            occupancy_data=occupancy_records,
            property_name=property_data.name,
            as_attachment=False
        )
        return redirect(url_for('preview_pdf', 
                                pdf_url=pdf_url, 
                                back_url=url_for('manage_occupancy')))
    
    # Generate PDF untuk download
    return generate_occupancy_pdf(
        property_id=property_id,
        start_month=start_month,
        end_month=end_month,
        occupancy_data=occupancy_records,
        property_name=property_data.name,
        as_attachment=True
    )

@app.route('/export_finance_pdf')
@login_required
@property_access_required
def export_finance_pdf():
    """
    Mengekspor data keuangan ke PDF
    """
    property_id = request.args.get('property_id', type=int)
    start_date_str = request.args.get('start_date', datetime.now().replace(day=1).strftime('%Y-%m-%d'))
    end_date_str = request.args.get('end_date', datetime.now().strftime('%Y-%m-%d'))
    preview = request.args.get('preview', 'false') == 'true'
    
    # Validasi format tanggal
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except ValueError:
        flash('Format tanggal tidak valid. Gunakan format YYYY-MM-DD.', 'danger')
        return redirect(url_for('manage_finance'))
    
    if not property_id:
        flash('Properti tidak valid.', 'danger')
        return redirect(url_for('manage_finance'))
    
    # Pastikan pengguna memiliki akses ke properti
    accessible_properties = get_user_properties()
    property_data = next((p for p in accessible_properties if p.id == property_id), None)
    
    if not property_data:
        flash('Anda tidak memiliki akses ke properti ini.', 'danger')
        return redirect(url_for('manage_finance'))
    
    # Ambil data keuangan untuk rentang tanggal yang diminta
    finance_records = FinancialRecord.query.filter(
        FinancialRecord.property_id == property_id,
        FinancialRecord.transaction_date >= start_date,
        FinancialRecord.transaction_date <= end_date
    ).order_by(FinancialRecord.transaction_date).all()
    
    # Hitung summary data
    total_income = sum(record.amount for record in finance_records if record.transaction_type == 'income')
    total_expense = sum(record.amount for record in finance_records if record.transaction_type == 'expense')
    net_profit = total_income - total_expense
    
    # Hitung income dan expense by category
    income_by_category = {}
    expense_by_category = {}
    
    for record in finance_records:
        if record.transaction_type == 'income':
            if record.category in income_by_category:
                income_by_category[record.category] += record.amount
            else:
                income_by_category[record.category] = record.amount
        else:
            if record.category in expense_by_category:
                expense_by_category[record.category] += record.amount
            else:
                expense_by_category[record.category] = record.amount
    
    summary_data = {
        'total_income': total_income,
        'total_expense': total_expense,
        'net_profit': net_profit,
        'income_by_category': income_by_category,
        'expense_by_category': expense_by_category
    }
    
    # Jika mode preview, arahkan ke halaman preview
    if preview:
        pdf_url = generate_finance_pdf(
            property_id=property_id,
            start_date=start_date,
            end_date=end_date,
            finance_data=finance_records,
            property_name=property_data.name,
            summary_data=summary_data,
            as_attachment=False
        )
        return redirect(url_for('preview_pdf', 
                              pdf_url=pdf_url, 
                              back_url=url_for('manage_finance')))
    
    # Generate PDF untuk download
    return generate_finance_pdf(
        property_id=property_id,
        start_date=start_date,
        end_date=end_date,
        finance_data=finance_records,
        property_name=property_data.name,
        summary_data=summary_data,
        as_attachment=True
    )

@app.route('/export_room_stats_pdf')
@login_required
@property_access_required
def export_room_stats_pdf():
    """
    Mengekspor statistik kamar ke PDF
    """
    property_id = request.args.get('property_id', type=int)
    month = request.args.get('month', datetime.now().strftime('%Y-%m'))
    preview = request.args.get('preview', 'false') == 'true'
    
    # Validasi format bulan
    try:
        datetime.strptime(month, '%Y-%m')
    except ValueError:
        flash('Format bulan tidak valid. Gunakan format YYYY-MM.', 'danger')
        return redirect(url_for('room_stats'))
    
    if not property_id:
        flash('Properti tidak valid.', 'danger')
        return redirect(url_for('room_stats'))
    
    # Pastikan pengguna memiliki akses ke properti
    accessible_properties = get_user_properties()
    property_data = next((p for p in accessible_properties if p.id == property_id), None)
    
    if not property_data:
        flash('Anda tidak memiliki akses ke properti ini.', 'danger')
        return redirect(url_for('room_stats'))
    
    # Ambil data kamar dan hunian
    rooms = Room.query.filter(Room.property_id == property_id).all()
    total_rooms = len(rooms)
    occupied_rooms = sum(1 for room in rooms if room.status == 'occupied')
    vacant_rooms = total_rooms - occupied_rooms
    occupancy_rate = (occupied_rooms / total_rooms * 100) if total_rooms > 0 else 0
    
    # Get room details with tenant information
    room_details = []
    room_types = {}
    
    for room in rooms:
        # Count room types
        if room.room_type in room_types:
            room_types[room.room_type] += 1
        else:
            room_types[room.room_type] = 1
            
        # Get tenant name if room is occupied
        tenant_name = None
        if room.status == 'occupied':
            occupancy = OccupancyRecord.query.filter(
                OccupancyRecord.room_id == room.id,
                OccupancyRecord.month == month
            ).first()
            if occupancy:
                tenant_name = occupancy.tenant_name
        
        room_details.append({
            'id': room.id,
            'number': room.number,
            'room_type': room.room_type,
            'monthly_rate': room.monthly_rate,
            'status': room.status,
            'tenant_name': tenant_name
        })
    
    # Get payment status statistics
    payment_status = {
        'paid': 0,
        'unpaid': 0,
        'late': 0
    }
    
    occupancy_records = OccupancyRecord.query.join(Room).filter(
        Room.property_id == property_id,
        OccupancyRecord.month == month,
        OccupancyRecord.is_occupied == True
    ).all()
    
    for record in occupancy_records:
        if record.payment_status in payment_status:
            payment_status[record.payment_status] += 1
    
    stats_data = {
        'total_rooms': total_rooms,
        'occupied_rooms': occupied_rooms,
        'vacant_rooms': vacant_rooms,
        'occupancy_rate': occupancy_rate,
        'room_details': room_details,
        'room_types': room_types,
        'payment_status': payment_status
    }
    
    # Jika mode preview, arahkan ke halaman preview
    if preview:
        pdf_url = generate_room_stats_pdf(
            property_id=property_id,
            month=month,
            stats_data=stats_data,
            property_name=property_data.name,
            as_attachment=False
        )
        return redirect(url_for('preview_pdf', 
                                pdf_url=pdf_url, 
                                back_url=url_for('room_stats')))
    
    # Generate PDF untuk download
    return generate_room_stats_pdf(
        property_id=property_id,
        month=month,
        stats_data=stats_data,
        property_name=property_data.name,
        as_attachment=True
    )

@app.route('/export_financial_stats_pdf')
@login_required
@admin_required  # Hanya admin yang dapat mengakses statistik keuangan
def export_financial_stats_pdf():
    """
    Mengekspor statistik keuangan ke PDF
    """
    property_id = request.args.get('property_id', type=int, default=0)
    year = request.args.get('year', datetime.now().strftime('%Y'))
    preview = request.args.get('preview', 'false') == 'true'
    
    # Validasi format tahun
    try:
        year_int = int(year)
        if year_int < 2000 or year_int > 2100:
            raise ValueError("Tahun tidak valid")
    except ValueError:
        flash('Format tahun tidak valid. Gunakan format YYYY.', 'danger')
        return redirect(url_for('financial_stats'))
    
    # Tentukan properti yang akan dilihat
    if property_id:
        property_data = Property.query.get_or_404(property_id)
        property_filter = FinancialRecord.property_id == property_id
        property_name = property_data.name
    else:
        property_filter = FinancialRecord.id > 0  # All properties
        property_name = "Semua Properti"
    
    # Define the date range for the year
    start_date = date(int(year), 1, 1)
    end_date = date(int(year), 12, 31)
    
    # Calculate yearly summary
    yearly_income = db.session.query(db.func.sum(FinancialRecord.amount)).filter(
        property_filter,
        FinancialRecord.transaction_type == 'income',
        FinancialRecord.transaction_date >= start_date,
        FinancialRecord.transaction_date <= end_date
    ).scalar() or 0
    
    yearly_expense = db.session.query(db.func.sum(FinancialRecord.amount)).filter(
        property_filter,
        FinancialRecord.transaction_type == 'expense',
        FinancialRecord.transaction_date >= start_date,
        FinancialRecord.transaction_date <= end_date
    ).scalar() or 0
    
    yearly_profit = yearly_income - yearly_expense
    
    # Calculate monthly breakdown
    monthly_data = []
    month_names = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 
                  'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']
    
    highest_income_month = ""
    highest_income_amount = 0
    highest_expense_month = ""
    highest_expense_amount = 0
    highest_profit_month = ""
    highest_profit_amount = 0
    
    for month_num in range(1, 13):
        month_start = date(int(year), month_num, 1)
        if month_num == 12:
            month_end = date(int(year), month_num, 31)
        else:
            month_end = date(int(year), month_num + 1, 1) - timedelta(days=1)
        
        month_income = db.session.query(db.func.sum(FinancialRecord.amount)).filter(
            property_filter,
            FinancialRecord.transaction_type == 'income',
            FinancialRecord.transaction_date >= month_start,
            FinancialRecord.transaction_date <= month_end
        ).scalar() or 0
        
        month_expense = db.session.query(db.func.sum(FinancialRecord.amount)).filter(
            property_filter,
            FinancialRecord.transaction_type == 'expense',
            FinancialRecord.transaction_date >= month_start,
            FinancialRecord.transaction_date <= month_end
        ).scalar() or 0
        
        month_profit = month_income - month_expense
        
        # Update highest values
        if month_income > highest_income_amount:
            highest_income_amount = month_income
            highest_income_month = month_names[month_num - 1]
        
        if month_expense > highest_expense_amount:
            highest_expense_amount = month_expense
            highest_expense_month = month_names[month_num - 1]
        
        if month_profit > highest_profit_amount:
            highest_profit_amount = month_profit
            highest_profit_month = month_names[month_num - 1]
        
        monthly_data.append({
            'month_num': month_num,
            'month_name': month_names[month_num - 1],
            'income': month_income,
            'expense': month_expense,
            'profit': month_profit
        })
    
    # Get income and expense by category
    income_by_category = db.session.query(
        FinancialRecord.category,
        db.func.sum(FinancialRecord.amount)
    ).filter(
        property_filter,
        FinancialRecord.transaction_type == 'income',
        FinancialRecord.transaction_date >= start_date,
        FinancialRecord.transaction_date <= end_date
    ).group_by(FinancialRecord.category).all()
    
    expense_by_category = db.session.query(
        FinancialRecord.category,
        db.func.sum(FinancialRecord.amount)
    ).filter(
        property_filter,
        FinancialRecord.transaction_type == 'expense',
        FinancialRecord.transaction_date >= start_date,
        FinancialRecord.transaction_date <= end_date
    ).group_by(FinancialRecord.category).all()
    
    # Convert query results to dict
    income_by_category_dict = {cat: amount for cat, amount in income_by_category}
    expense_by_category_dict = {cat: amount for cat, amount in expense_by_category}
    
    stats_data = {
        'yearly_summary': {
            'total_income': yearly_income,
            'total_expense': yearly_expense,
            'net_profit': yearly_profit
        },
        'monthly_data': monthly_data,
        'income_by_category': income_by_category_dict,
        'expense_by_category': expense_by_category_dict,
        'trends': {
            'highest_income_month': highest_income_month,
            'highest_income_amount': highest_income_amount,
            'highest_expense_month': highest_expense_month,
            'highest_expense_amount': highest_expense_amount,
            'highest_profit_month': highest_profit_month,
            'highest_profit_amount': highest_profit_amount
        }
    }
    
    # Jika mode preview, arahkan ke halaman preview
    if preview:
        pdf_url = generate_financial_stats_pdf(
            property_id=property_id,
            year=year,
            stats_data=stats_data,
            property_name=property_name,
            as_attachment=False
        )
        return redirect(url_for('preview_pdf', 
                              pdf_url=pdf_url, 
                              back_url=url_for('financial_stats')))
    
    # Generate PDF untuk download
    return generate_financial_stats_pdf(
        property_id=property_id,
        year=year,
        stats_data=stats_data,
        property_name=property_name,
        as_attachment=True
    )
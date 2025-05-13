import os
from datetime import datetime
from app import app, db
from models import OccupancyRecord, Room, FinancialRecord
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

def create_financial_records_for_existing_payments():
    with app.app_context():
        # 1. Dapatkan data ocupansi dengan status 'paid'
        paid_occupancies = OccupancyRecord.query.filter_by(payment_status='paid').all()
        print(f'Menemukan {len(paid_occupancies)} catatan pembayaran dengan status paid')
        
        # 2. Untuk setiap catatan paid, buat catatan finansial
        for occupancy in paid_occupancies:
            room = Room.query.get(occupancy.room_id)
            if not room:
                print(f'Kamar dengan id {occupancy.room_id} tidak ditemukan')
                continue
                
            # Hitung jumlah pembayaran
            amount = room.monthly_rate * occupancy.payment_months
            payment_date = occupancy.payment_date or datetime.now().date()
            
            # Cek apakah sudah ada catatan finansial untuk occupancy ini
            existing_record = FinancialRecord.query.filter(
                FinancialRecord.description.like(f'%occupancy_id={occupancy.id}%')
            ).first()
            
            if existing_record:
                print(f'Catatan finansial untuk occupancy_id={occupancy.id} sudah ada')
            else:
                # Buat catatan finansial baru
                financial_record = FinancialRecord(
                    property_id=room.property_id,
                    transaction_date=payment_date,
                    amount=amount,
                    transaction_type='income',
                    category='Sewa',
                    description=f'Pembayaran sewa oleh {occupancy.tenant_name} untuk {occupancy.payment_months} bulan (occupancy_id={occupancy.id})',
                    created_by=1  # admin user
                )
                db.session.add(financial_record)
                print(f'Membuat catatan finansial untuk occupancy_id={occupancy.id}, jumlah={amount}')
        
        # Commit transaksi
        db.session.commit()
        print('Semua catatan finansial telah dibuat')

if __name__ == '__main__':
    create_financial_records_for_existing_payments()
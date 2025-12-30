from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from sqlalchemy import func, extract
from extensions import db
from models.student import Student
from models.payment import Payment
from models.fee import FeeStructure

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
@login_required
def index():
    """Main dashboard"""
    return render_template('dashboard.html')

@dashboard_bp.route('/api/dashboard/stats')
@login_required
def get_stats():
    """Get dashboard statistics"""
    # Total students
    total_students = Student.query.filter_by(is_active=True).count()
    
    # Fees collected (all time)
    fees_collected = db.session.query(func.sum(Payment.amount)).scalar() or 0
    
    # Outstanding balance
    outstanding_balance = db.session.query(func.sum(Student.balance)).scalar() or 0
    
    # This month's payments
    first_day = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    monthly_payments = Payment.query.filter(Payment.payment_date >= first_day).count()
    
    return jsonify({
        'total_students': total_students,
        'fees_collected': float(fees_collected),
        'outstanding_balance': float(outstanding_balance),
        'monthly_payments': monthly_payments
    })

@dashboard_bp.route('/api/dashboard/payment-trends')
@login_required
def payment_trends():
    """Get payment trends for the last 6 months"""
    months_data = []
    
    for i in range(5, -1, -1):
        date = datetime.now() - timedelta(days=30 * i)
        month_start = date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        if i == 0:
            month_end = datetime.now()
        else:
            next_month = month_start + timedelta(days=32)
            month_end = next_month.replace(day=1) - timedelta(seconds=1)
        
        total = db.session.query(func.sum(Payment.amount)).filter(
            Payment.payment_date >= month_start.date(),
            Payment.payment_date <= month_end.date()
        ).scalar() or 0
        
        months_data.append({
            'month': month_start.strftime('%b %Y'),
            'amount': float(total)
        })
    
    return jsonify(months_data)

@dashboard_bp.route('/api/dashboard/payment-calendar/<int:year>/<int:month>')
@login_required
def payment_calendar(year, month):
    """Get payments for a specific month"""
    start_date = datetime(year, month, 1).date()
    
    if month == 12:
        end_date = datetime(year + 1, 1, 1).date()
    else:
        end_date = datetime(year, month + 1, 1).date()
    
    payments = db.session.query(
        Payment.payment_date,
        func.count(Payment.id).label('count'),
        func.sum(Payment.amount).label('total')
    ).filter(
        Payment.payment_date >= start_date,
        Payment.payment_date < end_date
    ).group_by(Payment.payment_date).all()
    
    calendar_data = {}
    for payment in payments:
        calendar_data[payment.payment_date.isoformat()] = {
            'count': payment.count,
            'total': float(payment.total)
        }
    
    return jsonify(calendar_data)
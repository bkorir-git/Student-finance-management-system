from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from datetime import datetime, timedelta
from sqlalchemy import func
from extensions import db
from models.student import Student
from models.payment import Payment
from models.fee import FeeStructure

report_bp = Blueprint('report', __name__)

@report_bp.route('/')
@login_required
def index():
    """Reports dashboard"""
    return render_template('reports/index.html')

@report_bp.route('/api/payment-by-grade')
@login_required
def payment_by_grade():
    """Get payment distribution by grade"""
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    query = db.session.query(
        Student.grade,
        func.sum(Payment.amount).label('total')
    ).join(Payment).group_by(Student.grade)
    
    if date_from:
        query = query.filter(Payment.payment_date >= datetime.strptime(date_from, '%Y-%m-%d').date())
    
    if date_to:
        query = query.filter(Payment.payment_date <= datetime.strptime(date_to, '%Y-%m-%d').date())
    
    results = query.all()
    
    data = {
        'labels': [f'Grade {r.grade}' for r in results],
        'amounts': [float(r.total) for r in results]
    }
    
    return jsonify(data)

@report_bp.route('/api/payment-by-method')
@login_required
def payment_by_method():
    """Get payment distribution by method"""
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    query = db.session.query(
        Payment.payment_method,
        func.count(Payment.id).label('count'),
        func.sum(Payment.amount).label('total')
    ).group_by(Payment.payment_method)
    
    if date_from:
        query = query.filter(Payment.payment_date >= datetime.strptime(date_from, '%Y-%m-%d').date())
    
    if date_to:
        query = query.filter(Payment.payment_date <= datetime.strptime(date_to, '%Y-%m-%d').date())
    
    results = query.all()
    
    data = {
        'labels': [r.payment_method for r in results],
        'counts': [r.count for r in results],
        'amounts': [float(r.total) for r in results]
    }
    
    return jsonify(data)

@report_bp.route('/api/summary')
@login_required
def summary():
    """Get report summary"""
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    # Total collected
    query = db.session.query(func.sum(Payment.amount))
    
    if date_from:
        query = query.filter(Payment.payment_date >= datetime.strptime(date_from, '%Y-%m-%d').date())
    
    if date_to:
        query = query.filter(Payment.payment_date <= datetime.strptime(date_to, '%Y-%m-%d').date())
    
    total_collected = query.scalar() or 0
    
    # Total outstanding
    total_outstanding = db.session.query(func.sum(Student.balance)).filter(Student.is_active == True).scalar() or 0
    
    # Collection rate
    total_expected = float(total_collected) + float(total_outstanding)
    collection_rate = (float(total_collected) / total_expected * 100) if total_expected > 0 else 0
    
    # Number of payments
    payment_count = db.session.query(func.count(Payment.id))
    if date_from:
        payment_count = payment_count.filter(Payment.payment_date >= datetime.strptime(date_from, '%Y-%m-%d').date())
    if date_to:
        payment_count = payment_count.filter(Payment.payment_date <= datetime.strptime(date_to, '%Y-%m-%d').date())
    
    return jsonify({
        'total_collected': float(total_collected),
        'total_outstanding': float(total_outstanding),
        'collection_rate': round(collection_rate, 1),
        'payment_count': payment_count.scalar()
    })

@report_bp.route('/api/defaulters')
@login_required
def defaulters():
    """Get list of students with outstanding balances"""
    threshold = request.args.get('threshold', 0, type=float)
    
    students = Student.query.filter(
        Student.is_active == True,
        Student.balance > threshold
    ).order_by(Student.balance.desc()).all()
    
    return jsonify([{
        'id': s.id,
        'student_number': s.student_number,
        'full_name': s.full_name,
        'grade': s.grade,
        'balance': float(s.balance),
        'guardian_contact': s.guardian_contact
    } for s in students])
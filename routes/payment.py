from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime
from extensions import db
from models.payment import Payment
from models.student import Student
from models.fee import SystemLog

payment_bp = Blueprint('payment', __name__)

@payment_bp.route('/')
@login_required
def index():
    """List all payments"""
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    search = request.args.get('search', '')
    method_filter = request.args.get('method', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    
    query = Payment.query.join(Student)
    
    if search:
        query = query.filter(
            db.or_(
                Student.full_name.ilike(f'%{search}%'),
                Payment.receipt_number.ilike(f'%{search}%'),
                Payment.transaction_reference.ilike(f'%{search}%')
            )
        )
    
    if method_filter:
        query = query.filter(Payment.payment_method == method_filter)
    
    if date_from:
        query = query.filter(Payment.payment_date >= datetime.strptime(date_from, '%Y-%m-%d').date())
    
    if date_to:
        query = query.filter(Payment.payment_date <= datetime.strptime(date_to, '%Y-%m-%d').date())
    
    payments = query.order_by(Payment.payment_date.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('payments/list.html', payments=payments, search=search, method_filter=method_filter)

@payment_bp.route('/api/list')
@login_required
def api_list():
    """API endpoint to get all payments"""
    payments = Payment.query.order_by(Payment.payment_date.desc()).limit(100).all()
    return jsonify([payment.to_dict() for payment in payments])

@payment_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create a new payment"""
    if not current_user.has_permission('create'):
        flash('You do not have permission to create payments', 'error')
        return redirect(url_for('payment.index'))
    
    if request.method == 'POST':
        try:
            student_id = int(request.form.get('student_id'))
            amount = float(request.form.get('amount'))
            
            student = Student.query.get_or_404(student_id)
            
            # Validate amount
            if amount <= 0:
                flash('Payment amount must be greater than 0', 'error')
                return redirect(url_for('payment.create'))
            
            # Create payment
            payment = Payment(
                student_id=student_id,
                amount=amount,
                fee_type=request.form.get('fee_type'),
                payment_method=request.form.get('payment_method'),
                payment_date=datetime.strptime(request.form.get('payment_date'), '%Y-%m-%d').date(),
                transaction_reference=request.form.get('transaction_reference'),
                receipt_number=Payment.generate_receipt_number(),
                notes=request.form.get('notes'),
                created_by=current_user.id
            )
            
            db.session.add(payment)
            
            # Update student balance (subtract payment)
            student.update_balance(
                amount=-amount,
                change_type='payment',
                description=f'Payment received: {payment.fee_type}',
                created_by=current_user.id,
                reference_id=payment.id
            )
            
            db.session.commit()
            
            # Log the action
            log = SystemLog(
                user_id=current_user.id,
                action='create_payment',
                entity_type='payment',
                entity_id=payment.id,
                details=f'Payment of {amount} from {student.full_name}',
                ip_address=request.remote_addr
            )
            db.session.add(log)
            db.session.commit()
            
            flash(f'Payment recorded successfully. Receipt #: {payment.receipt_number}', 'success')
            return jsonify({
                'success': True,
                'payment_id': payment.id,
                'receipt_number': payment.receipt_number
            })
        
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 500
    
    students = Student.query.filter_by(is_active=True).order_by(Student.full_name).all()
    return render_template('payments/form.html', students=students)

@payment_bp.route('/delete/<int:payment_id>', methods=['POST'])
@login_required
def delete(payment_id):
    """Delete a payment"""
    if not current_user.has_permission('delete'):
        return jsonify({'success': False, 'message': 'Permission denied'}), 403
    
    try:
        payment = Payment.query.get_or_404(payment_id)
        student = payment.student
        amount = float(payment.amount)
        
        # Restore balance to student
        student.update_balance(
            amount=amount,
            change_type='adjustment',
            description=f'Payment {payment.receipt_number} deleted',
            created_by=current_user.id
        )
        
        # Delete payment
        db.session.delete(payment)
        db.session.commit()
        
        # Log the action
        log = SystemLog(
            user_id=current_user.id,
            action='delete_payment',
            entity_type='payment',
            entity_id=payment_id,
            details=f'Deleted payment {payment.receipt_number}, restored balance',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Payment deleted and balance restored'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@payment_bp.route('/receipt/<int:payment_id>')
@login_required
def receipt(payment_id):
    """View payment receipt"""
    payment = Payment.query.get_or_404(payment_id)
    return render_template('payments/receipt.html', payment=payment)

@payment_bp.route('/api/receipt/<int:payment_id>')
@login_required
def api_receipt(payment_id):
    """API endpoint to get receipt data"""
    payment = Payment.query.get_or_404(payment_id)
    student = payment.student
    
    return jsonify({
        'receipt_number': payment.receipt_number,
        'payment_date': payment.payment_date.isoformat(),
        'student': {
            'id': student.id,
            'student_number': student.student_number,
            'full_name': student.full_name,
            'grade': student.grade,
            'guardian_contact': student.guardian_contact,
            'current_balance': float(student.balance)
        },
        'payment': {
            'amount': float(payment.amount),
            'fee_type': payment.fee_type,
            'payment_method': payment.payment_method,
            'transaction_reference': payment.transaction_reference
        }
    })
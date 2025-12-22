from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from extensions import db
from models.fee import FeeStructure, SystemLog

fee_bp = Blueprint('fee', __name__)

@fee_bp.route('/')
@login_required
def index():
    """List all fee structures"""
    grade_filter = request.args.get('grade', '')
    term_filter = request.args.get('term', '')
    
    query = FeeStructure.query.filter_by(is_active=True)
    
    if grade_filter:
        query = query.filter_by(grade=grade_filter)
    
    if term_filter:
        query = query.filter_by(term=term_filter)
    
    fees = query.order_by(FeeStructure.grade, FeeStructure.term).all()
    
    return render_template('fees/list.html', fees=fees, grade_filter=grade_filter, term_filter=term_filter)

@fee_bp.route('/api/list')
@login_required
def api_list():
    """API endpoint to get all fee structures"""
    fees = FeeStructure.query.filter_by(is_active=True).all()
    return jsonify([fee.to_dict() for fee in fees])

@fee_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create a new fee structure"""
    if not current_user.has_permission('create'):
        flash('You do not have permission to create fee structures', 'error')
        return redirect(url_for('fee.index'))
    
    if request.method == 'POST':
        try:
            fee = FeeStructure(
                grade=request.form.get('grade'),
                term=request.form.get('term'),
                fee_type=request.form.get('fee_type'),
                amount=float(request.form.get('amount')),
                description=request.form.get('description'),
                academic_year=request.form.get('academic_year')
            )
            
            db.session.add(fee)
            db.session.commit()
            
            # Log the action
            log = SystemLog(
                user_id=current_user.id,
                action='create_fee',
                entity_type='fee',
                entity_id=fee.id,
                details=f'Created fee: Grade {fee.grade} - {fee.fee_type}',
                ip_address=request.remote_addr
            )
            db.session.add(log)
            db.session.commit()
            
            flash('Fee structure created successfully', 'success')
            return redirect(url_for('fee.index'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating fee structure: {str(e)}', 'error')
    
    return render_template('fees/form.html', fee=None)

@fee_bp.route('/edit/<int:fee_id>', methods=['GET', 'POST'])
@login_required
def edit(fee_id):
    """Edit a fee structure"""
    if not current_user.has_permission('edit'):
        flash('You do not have permission to edit fee structures', 'error')
        return redirect(url_for('fee.index'))
    
    fee = FeeStructure.query.get_or_404(fee_id)
    
    if request.method == 'POST':
        try:
            fee.grade = request.form.get('grade')
            fee.term = request.form.get('term')
            fee.fee_type = request.form.get('fee_type')
            fee.amount = float(request.form.get('amount'))
            fee.description = request.form.get('description')
            fee.academic_year = request.form.get('academic_year')
            
            db.session.commit()
            
            # Log the action
            log = SystemLog(
                user_id=current_user.id,
                action='edit_fee',
                entity_type='fee',
                entity_id=fee.id,
                details=f'Updated fee: Grade {fee.grade} - {fee.fee_type}',
                ip_address=request.remote_addr
            )
            db.session.add(log)
            db.session.commit()
            
            flash('Fee structure updated successfully', 'success')
            return redirect(url_for('fee.index'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating fee structure: {str(e)}', 'error')
    
    return render_template('fees/form.html', fee=fee)

@fee_bp.route('/delete/<int:fee_id>', methods=['POST'])
@login_required
def delete(fee_id):
    """Delete a fee structure"""
    if not current_user.has_permission('delete'):
        return jsonify({'success': False, 'message': 'Permission denied'}), 403
    
    try:
        fee = FeeStructure.query.get_or_404(fee_id)
        
        # Soft delete
        fee.is_active = False
        db.session.commit()
        
        # Log the action
        log = SystemLog(
            user_id=current_user.id,
            action='delete_fee',
            entity_type='fee',
            entity_id=fee.id,
            details=f'Deleted fee: Grade {fee.grade} - {fee.fee_type}',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Fee structure deleted successfully'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
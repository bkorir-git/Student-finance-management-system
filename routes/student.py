from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime
from extensions import db
from models.student import Student
from models.fee import FeeStructure, SystemLog

student_bp = Blueprint('student', __name__)

@student_bp.route('/')
@login_required
def index():
    """List all students"""
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    search = request.args.get('search', '')
    grade_filter = request.args.get('grade', '')
    
    query = Student.query.filter_by(is_active=True)
    
    if search:
        query = query.filter(
            db.or_(
                Student.full_name.ilike(f'%{search}%'),
                Student.student_number.ilike(f'%{search}%'),
                Student.guardian_contact.ilike(f'%{search}%')
            )
        )
    
    if grade_filter:
        query = query.filter_by(grade=grade_filter)
    
    students = query.order_by(Student.full_name).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('students/list.html', students=students, search=search, grade_filter=grade_filter)

@student_bp.route('/api/list')
@login_required
def api_list():
    """API endpoint to get all students"""
    students = Student.query.filter_by(is_active=True).order_by(Student.full_name).all()
    return jsonify([student.to_dict() for student in students])

@student_bp.route('/api/<int:student_id>')
@login_required
def api_get(student_id):
    """API endpoint to get a single student"""
    student = Student.query.get_or_404(student_id)
    return jsonify(student.to_dict())

@student_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create a new student"""
    if not current_user.has_permission('create'):
        flash('You do not have permission to create students', 'error')
        return redirect(url_for('student.index'))
    
    if request.method == 'POST':
        try:
            # Generate student number
            last_student = Student.query.order_by(Student.id.desc()).first()
            if last_student and last_student.student_number.startswith('STU'):
                last_num = int(last_student.student_number[3:])
                student_number = f'STU{str(last_num + 1).zfill(3)}'
            else:
                student_number = 'STU001'
            
            student = Student(
                student_number=student_number,
                full_name=request.form.get('full_name'),
                grade=request.form.get('grade'),
                guardian_name=request.form.get('guardian_name'),
                guardian_contact=request.form.get('guardian_contact'),
                guardian_email=request.form.get('guardian_email'),
                address=request.form.get('address'),
                enrollment_date=datetime.strptime(request.form.get('enrollment_date'), '%Y-%m-%d').date() if request.form.get('enrollment_date') else datetime.now().date()
            )
            
            # Calculate initial balance from fee structure
            initial_balance = float(request.form.get('balance', 0))
            if initial_balance == 0:
                # Auto-calculate from fee structure
                grade = request.form.get('grade')
                total_fees = FeeStructure.get_total_fees_for_grade(grade)
                student.balance = total_fees
            else:
                student.balance = initial_balance
            
            db.session.add(student)
            db.session.commit()
            
            # Log the action
            log = SystemLog(
                user_id=current_user.id,
                action='create_student',
                entity_type='student',
                entity_id=student.id,
                details=f'Created student: {student.full_name}',
                ip_address=request.remote_addr
            )
            db.session.add(log)
            db.session.commit()
            
            flash(f'Student {student.full_name} created successfully', 'success')
            return redirect(url_for('student.index'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating student: {str(e)}', 'error')
    
    return render_template('students/form.html', student=None)

@student_bp.route('/edit/<int:student_id>', methods=['GET', 'POST'])
@login_required
def edit(student_id):
    """Edit a student"""
    if not current_user.has_permission('edit'):
        flash('You do not have permission to edit students', 'error')
        return redirect(url_for('student.index'))
    
    student = Student.query.get_or_404(student_id)
    
    if request.method == 'POST':
        try:
            student.full_name = request.form.get('full_name')
            student.grade = request.form.get('grade')
            student.guardian_name = request.form.get('guardian_name')
            student.guardian_contact = request.form.get('guardian_contact')
            student.guardian_email = request.form.get('guardian_email')
            student.address = request.form.get('address')
            
            if request.form.get('enrollment_date'):
                student.enrollment_date = datetime.strptime(request.form.get('enrollment_date'), '%Y-%m-%d').date()
            
            db.session.commit()
            
            # Log the action
            log = SystemLog(
                user_id=current_user.id,
                action='edit_student',
                entity_type='student',
                entity_id=student.id,
                details=f'Updated student: {student.full_name}',
                ip_address=request.remote_addr
            )
            db.session.add(log)
            db.session.commit()
            
            flash(f'Student {student.full_name} updated successfully', 'success')
            return redirect(url_for('student.index'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating student: {str(e)}', 'error')
    
    return render_template('students/form.html', student=student)

@student_bp.route('/delete/<int:student_id>', methods=['POST'])
@login_required
def delete(student_id):
    """Delete a student"""
    if not current_user.has_permission('delete'):
        return jsonify({'success': False, 'message': 'Permission denied'}), 403
    
    try:
        student = Student.query.get_or_404(student_id)
        student_name = student.full_name
        
        # Soft delete
        student.is_active = False
        db.session.commit()
        
        # Log the action
        log = SystemLog(
            user_id=current_user.id,
            action='delete_student',
            entity_type='student',
            entity_id=student.id,
            details=f'Deleted student: {student_name}',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({'success': True, 'message': f'Student {student_name} deleted successfully'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@student_bp.route('/apply-fees/<int:student_id>', methods=['POST'])
@login_required
def apply_fees(student_id):
    """Apply fee structure to a student"""
    if not current_user.has_permission('edit'):
        return jsonify({'success': False, 'message': 'Permission denied'}), 403
    
    try:
        student = Student.query.get_or_404(student_id)
        
        # Get fee structure for student's grade
        total_fees = FeeStructure.get_total_fees_for_grade(student.grade)
        
        if total_fees == 0:
            return jsonify({
                'success': False,
                'message': f'No fee structure defined for Grade {student.grade}'
            }), 400
        
        # Update balance
        new_balance = student.update_balance(
            amount=total_fees,
            change_type='fee_applied',
            description=f'Fee structure applied for Grade {student.grade}',
            created_by=current_user.id
        )
        
        db.session.commit()
        
        # Log the action
        log = SystemLog(
            user_id=current_user.id,
            action='apply_fees',
            entity_type='student',
            entity_id=student.id,
            details=f'Applied fees of {total_fees} to {student.full_name}',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Fee structure applied successfully',
            'new_balance': float(new_balance),
            'amount_applied': float(total_fees)
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
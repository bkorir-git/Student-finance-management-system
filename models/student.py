from datetime import datetime
from app import db

class Student(db.Model):
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    student_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(150), nullable=False, index=True)
    grade = db.Column(db.String(10), nullable=False, index=True)
    guardian_name = db.Column(db.String(150))
    guardian_contact = db.Column(db.String(20), nullable=False)
    guardian_email = db.Column(db.String(120))
    address = db.Column(db.Text)
    balance = db.Column(db.Numeric(15, 2), default=0.00, index=True)
    is_active = db.Column(db.Boolean, default=True)
    enrollment_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    payments = db.relationship('Payment', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    balance_history = db.relationship('BalanceHistory', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    
    def update_balance(self, amount, change_type, description=None, created_by=None, reference_id=None):
        """Update student balance and record history"""
        previous_balance = float(self.balance)
        self.balance = float(self.balance) + amount
        new_balance = float(self.balance)
        
        # Record history
        history = BalanceHistory(
            student_id=self.id,
            previous_balance=previous_balance,
            new_balance=new_balance,
            change_amount=amount,
            change_type=change_type,
            reference_id=reference_id,
            description=description,
            created_by=created_by
        )
        db.session.add(history)
        
        return new_balance
    
    def to_dict(self):
        """Convert student object to dictionary"""
        return {
            'id': self.id,
            'student_number': self.student_number,
            'full_name': self.full_name,
            'grade': self.grade,
            'guardian_name': self.guardian_name,
            'guardian_contact': self.guardian_contact,
            'guardian_email': self.guardian_email,
            'balance': float(self.balance),
            'is_active': self.is_active,
            'enrollment_date': self.enrollment_date.isoformat() if self.enrollment_date else None
        }
    
    def __repr__(self):
        return f'<Student {self.student_number}: {self.full_name}>'

class BalanceHistory(db.Model):
    __tablename__ = 'balance_history'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False, index=True)
    previous_balance = db.Column(db.Numeric(15, 2), nullable=False)
    new_balance = db.Column(db.Numeric(15, 2), nullable=False)
    change_amount = db.Column(db.Numeric(15, 2), nullable=False)
    change_type = db.Column(db.Enum('payment', 'fee_applied', 'adjustment', 'refund'), nullable=False)
    reference_id = db.Column(db.Integer)
    description = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f'<BalanceHistory {self.id}: {self.change_type}>'
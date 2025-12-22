from datetime import datetime
from app import db
import secrets

class Payment(db.Model):
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False, index=True)
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    fee_type = db.Column(db.String(50), nullable=False)
    payment_method = db.Column(db.Enum('Cash', 'M-Pesa', 'Bank Transfer', 'Cheque', 'Card'), nullable=False, index=True)
    payment_date = db.Column(db.Date, nullable=False, index=True)
    transaction_reference = db.Column(db.String(100))
    receipt_number = db.Column(db.String(50), unique=True, index=True)
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @staticmethod
    def generate_receipt_number():
        """Generate unique receipt number"""
        timestamp = datetime.now().strftime('%Y%m%d')
        random_suffix = secrets.token_hex(3).upper()
        return f'RCP-{timestamp}-{random_suffix}'
    
    def to_dict(self):
        """Convert payment object to dictionary"""
        return {
            'id': self.id,
            'student_id': self.student_id,
            'student_name': self.student.full_name if self.student else None,
            'amount': float(self.amount),
            'fee_type': self.fee_type,
            'payment_method': self.payment_method,
            'payment_date': self.payment_date.isoformat(),
            'receipt_number': self.receipt_number,
            'transaction_reference': self.transaction_reference
        }
    
    def __repr__(self):
        return f'<Payment {self.receipt_number}>'
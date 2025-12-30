from datetime import datetime
from app import db

class FeeStructure(db.Model):
    __tablename__ = 'fee_structures'
    
    id = db.Column(db.Integer, primary_key=True)
    grade = db.Column(db.String(10), nullable=False, index=True)
    term = db.Column(db.Enum('Term 1', 'Term 2', 'Term 3', 'Annual'), nullable=False, index=True)
    fee_type = db.Column(db.String(50), nullable=False, index=True)
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    description = db.Column(db.Text)
    academic_year = db.Column(db.String(10))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('grade', 'term', 'fee_type', 'academic_year', name='unique_fee'),
    )
    
    @staticmethod
    def get_total_fees_for_grade(grade, term=None, academic_year=None):
        """Calculate total fees for a grade"""
        query = FeeStructure.query.filter_by(grade=grade, is_active=True)
        
        if term:
            query = query.filter_by(term=term)
        if academic_year:
            query = query.filter_by(academic_year=academic_year)
        
        fees = query.all()
        return sum(float(fee.amount) for fee in fees)
    
    def to_dict(self):
        """Convert fee structure to dictionary"""
        return {
            'id': self.id,
            'grade': self.grade,
            'term': self.term,
            'fee_type': self.fee_type,
            'amount': float(self.amount),
            'description': self.description,
            'academic_year': self.academic_year,
            'is_active': self.is_active
        }
    
    def __repr__(self):
        return f'<FeeStructure Grade {self.grade} - {self.fee_type}>'

class SystemLog(db.Model):
    __tablename__ = 'system_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), index=True)
    action = db.Column(db.String(100), nullable=False, index=True)
    entity_type = db.Column(db.String(50))
    entity_id = db.Column(db.Integer)
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f'<SystemLog {self.action}>'
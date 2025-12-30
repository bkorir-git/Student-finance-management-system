from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(120), unique=True, index=True)
    full_name = db.Column(db.String(150))
    role = db.Column(db.Enum('admin', 'accountant', 'viewer'), default='viewer')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    payments_created = db.relationship('Payment', backref='creator', lazy='dynamic', foreign_keys='Payment.created_by')
    logs = db.relationship('SystemLog', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if provided password matches hash"""
        return check_password_hash(self.password_hash, password)
    
    def has_permission(self, permission):
        """Check if user has specific permission"""
        permissions = {
            'admin': ['view', 'create', 'edit', 'delete', 'manage_users'],
            'accountant': ['view', 'create', 'edit'],
            'viewer': ['view']
        }
        return permission in permissions.get(self.role, [])
    
    def __repr__(self):
        return f'<User {self.username}>'

from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import current_user
from config import config
from extensions import db, login_manager
import os

def create_app(config_name=None):
    """Application factory pattern"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # User loader
    from models.user import User
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register blueprints
    from routes.auth import auth_bp
    from routes.student import student_bp
    from routes.payment import payment_bp
    from routes.fee import fee_bp
    from routes.report import report_bp
    from routes.dashboard import dashboard_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(student_bp, url_prefix='/students')
    app.register_blueprint(payment_bp, url_prefix='/payments')
    app.register_blueprint(fee_bp, url_prefix='/fees')
    app.register_blueprint(report_bp, url_prefix='/reports')
    app.register_blueprint(dashboard_bp)
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    # Template filters
    @app.template_filter('currency')
    def currency_filter(value):
        """Format value as currency"""
        try:
            return f"{app.config['CURRENCY']} {value:,.2f}"
        except (ValueError, TypeError):
            return f"{app.config['CURRENCY']} 0.00"
    
    @app.template_filter('date')
    def date_filter(value, format='%Y-%m-%d'):
        """Format date"""
        if value is None:
            return ""
        return value.strftime(format)
    
    # Context processors
    @app.context_processor
    def inject_config():
        return {
            'SCHOOL_NAME': app.config['SCHOOL_NAME'],
            'SCHOOL_ADDRESS': app.config['SCHOOL_ADDRESS'],
            'SCHOOL_PHONE': app.config['SCHOOL_PHONE'],
            'CURRENCY': app.config['CURRENCY']
        }
    
    # Index route
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard.index'))
        return redirect(url_for('auth.login'))
    
    return app

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
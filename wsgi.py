from app import app, db  # or however you import your app

# Only create tables if they don't exist (safe):
with app.app_context():
    db.create_all()  # This is safe - only creates missing tables

if __name__ == "__main__":
    app.run()

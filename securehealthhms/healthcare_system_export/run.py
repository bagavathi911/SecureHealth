"""
SecureHealth HMS - Launcher
Run this file to start the application.
"""
from app import app
from database import init_db
from sample_data import generate_sample_data

if __name__ == '__main__':
    with app.app_context():
        init_db()
        generate_sample_data()
    print("\n" + "="*55)
    print("  SecureHealth HMS is running!")
    print("  Open: http://127.0.0.1:5000")
    print("="*55)
    print("  Admin:  admin     / Admin@1234!")
    print("  Doctor: dr.mehta  / Doctor@1234!")
    print("  Nurse:  nurse01   / Nurse@1234!")
    print("="*55 + "\n")
    app.run(debug=False, host='127.0.0.1', port=5000)

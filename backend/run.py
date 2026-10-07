from app import create_app, db
import webbrowser
import threading
import time

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    # Auto-open browser after 3 seconds
    def open_browser():
        time.sleep(3)
        try:
            webbrowser.open('http://localhost:3000')
        except:
            print("\n📌 Open http://localhost:3000 in your browser")
    
    threading.Thread(target=open_browser, daemon=True).start()
    app.run(host='0.0.0.0', port=5000, debug=True)

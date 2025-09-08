# Tooltopia
An E-commerce Web app where various different tools are sold.

**Live Demo Working web app link:**https://tooltopia.onrender.com (the Website may take about 30 seconds to initialize which is normal) 
**Report (PDF):** docs/Tooltopia-Report.pdf

Small e-commerce Web app built with **Flask + SQLAlchemy + Flask-Login**: browse products, view details, register/login, add to cart (AJAX), update quantities, and checkout with stock checks.

## Features
- Product catalogue with live search suggestions
- Authentication (register/login/logout)
- AJAX “Add to cart” with toast
- Cart: update/remove items; totals with `Decimal` (no float tails)
- Checkout: validates stock, decrements stock, clears cart
- Simple admin page to update stock
- 
## Tech
**Backend**:**Python, Flask, SQLAlchemy, Flask-Login, Flask-WTF/WTForms  
**Frontend:** Jinja, HTML/CSS/JS, Bootstrap 4  
**Data:** SQLite for dev (ready for Postgres on hosting)  
**Hosting:** Render (Web Service)

## Run locally
Requires Python 3.11+.

```bash
cd TOOLTOPIA_code
python -m venv venv
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
# set a dev secret key
# Windows: set SECRET_KEY=dev-not-secret
# macOS/Linux: export SECRET_KEY=dev-not-secret
python app.py
Visit http://127.0.0.1:5000

# Rescue Bite

Rescue Bite is a Django MVT social-business platform for reducing restaurant food waste. Restaurants can publish safe surplus meals near closing time, and customers—especially students—can reserve them at 40–60% off and pay at collection.

Tagline: **Rescue Good Food. Reduce Waste. Save More.**

## Features

- Customer and restaurant-owner registration with role-based permissions
- Restaurant profiles and owner dashboards
- Food listing creation, image upload/URL, pricing, discount validation, quantity, and pickup windows
- Search, category/location/price/discount filters, sorting, food details, and countdown timers
- Atomic reservations using `transaction.atomic()` and `select_for_update()` to protect inventory
- Pay-at-collection confirmation codes, cancellation, collection status, and reservation history
- Database-backed notifications and unread counts
- Reviews limited to customers with collected reservations
- Impact tracker for meals served, estimated food saved, estimated CO₂ avoided, savings, and participating restaurants
- Screenshot-inspired navy/amber restaurant homepage with About, How It Works, food categories, impact, and testimonials
- Responsive customer, restaurant-owner, and staff-admin workspace shells with navy sidebars, food cards, notification/impact rails, inventory management, and listing creation
- Django Admin, realistic Malaysian demo data, responsive Tailwind UI, and Vanilla JavaScript interactions

## Technology

- Python 3.11+
- Django 5.2
- Django ORM and templates (MVT)
- SQLite locally; PostgreSQL-ready through `DATABASE_URL`
- Tailwind CSS CDN and custom CSS
- Vanilla JavaScript
- Pillow for uploaded images
- WhiteNoise for static files

No React, Vue, Angular, jQuery, Node.js backend, or Django REST Framework is used.

## Local installation

```bash
python -m venv .venv
source .venv/bin/activate                 # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
# Export values from .env.example as needed in your shell or hosting platform.
python manage.py migrate
python manage.py seed_demo --clear
python manage.py createsuperuser
python manage.py runserver
```

Open `http://127.0.0.1:8000/`.

The demo command creates these non-production accounts:

| Role | Email | Password |
| --- | --- | --- |
| Customer | `student@rescuebite.test` | `RescueBiteDemo123!` |
| Restaurant owner | `campusbites@rescuebite.test` | `RescueBiteDemo123!` |
| Admin dashboard | `admin@rescuebite.test` | `admin` |

Open `/admin-dashboard/` after signing in with the admin account. Use `python manage.py seed_demo --clear` to remove only the named demo users and recreate the demo dataset. Do not use demo passwords in production.

## Tests and checks

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test -v 2
```

The test suite covers authentication, role permissions, discount validation, listing expiry, atomic inventory reduction, reservation ownership, cancellation, collection, notifications, review eligibility, impact calculations, seed data, and end-to-end customer flows.

## Environment variables

`.env.example` is a reference file. Export these variables in your shell or configure them as secrets/environment variables in your hosting platform:

- `SECRET_KEY`: Django secret key
- `DEBUG`: `True` locally; `False` in production
- `ALLOWED_HOSTS`: comma-separated hostnames
- `DATABASE_URL`: optional PostgreSQL connection URL; SQLite is used when omitted
- `FOOD_WEIGHT_KG`: estimated average food weight per collected meal
- `CO2_KG_PER_KG_FOOD`: estimated CO₂ factor used by the prototype

The impact page labels CO₂ as estimated because these constants are assumptions for a university prototype, not a scientific measurement.

## Production deployment

This is a traditional server-rendered Django application. Vercel is suitable for a static frontend or serverless functions, but it is not the simplest or most reliable host for this complete Django session/database/media workflow. Use a Django-compatible service such as Render, Railway, Fly.io, or a managed VPS.

A production deployment should:

1. Set `DEBUG=False`, a strong `SECRET_KEY`, `ALLOWED_HOSTS`, and a PostgreSQL `DATABASE_URL`.
2. Install dependencies with `pip install -r requirements.txt`.
3. Run `python manage.py migrate`.
4. Run `python manage.py collectstatic --noinput`.
5. Create an administrator with `python manage.py createsuperuser`.
6. Start Gunicorn with `gunicorn rescue_bite.wsgi:application`.
7. Configure persistent media storage for uploaded images.
8. Serve HTTPS and configure the production domain/CSRF settings.

Do not commit `.env`, production credentials, the local SQLite database, or user-uploaded media.

## Project structure

```text
rescue_bite/
├── manage.py
├── rescue_bite/
├── accounts/
├── restaurants/
├── food/
├── reservations/
├── reviews/
├── notifications/
├── impact/
├── admin_dashboard/
├── templates/
├── static/
├── media/
└── tests/
```

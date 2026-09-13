# Rescue Bite Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a complete, responsive Django MVT MVP for Rescue Bite with role-based accounts, food listings, race-safe reservations, reviews, notifications, and database-backed impact tracking.

**Architecture:** A server-rendered Django project uses a custom email-based user model and focused apps for accounts, restaurants, food, reservations, reviews, notifications, and impact. Business-critical calculations and inventory updates live in models/forms/services on the backend; Tailwind templates and Vanilla JavaScript provide the responsive interface and non-critical interactions.

**Tech Stack:** Python 3.11+, Django 5.2+, SQLite for local development, PostgreSQL-ready configuration, Django templates, Tailwind CSS CDN, Vanilla JavaScript, Pillow for image uploads, and Django’s built-in test runner.

**Spec:** `docs/superpowers/specs/2026-09-11-rescue-bite-design.md`

## Global Constraints

- Product name must be **Rescue Bite**, never “Resquebit”.
- Tagline must be **Rescue Good Food. Reduce Waste. Save More.**
- Use Python, Django ORM/MVT, HTML5, Tailwind CSS, and Vanilla JavaScript.
- Do not use React, Vue, Angular, jQuery, Next.js, a Node.js backend, or DRF unless an explicitly tested requirement appears.
- Use SQLite locally and environment variables for production PostgreSQL configuration.
- Use the `Asia/Kuala_Lumpur` timezone.
- Restaurant discounts must be server-validated between 40% and 60%.
- Core inventory updates must use `transaction.atomic()` and `select_for_update()`.
- Payment is **Pay at Collection**; no real payment gateway is included.
- Impact CO₂ values must be labelled as estimates and calculated from configurable constants.
- Demo food photos must be real photographs from stable Unsplash URLs and identified as demo content.
- Every new behavior requires a failing test before implementation, followed by a passing test run.
- Use CSRF protection, authentication, role checks, server-side validation, and accessible semantic templates.

## File Map

```text
manage.py
requirements.txt
.env.example
.gitignore
README.md
rescue_bite/
  __init__.py
  settings.py
  urls.py
  asgi.py
  wsgi.py
accounts/
  admin.py apps.py forms.py models.py urls.py views.py tests.py
restaurants/
  admin.py apps.py forms.py models.py urls.py views.py tests.py
food/
  admin.py apps.py forms.py models.py urls.py views.py tests.py
reservations/
  admin.py apps.py forms.py models.py services.py urls.py views.py tests.py
reviews/
  admin.py apps.py forms.py models.py urls.py views.py tests.py
notifications/
  admin.py apps.py models.py urls.py views.py tests.py
impact/
  admin.py apps.py services.py urls.py views.py tests.py
templates/
  base.html
  includes/{navbar.html,footer.html,alerts.html,food_card.html,empty_state.html}
  accounts/{login.html,register.html,profile.html}
  food/{home.html,discover.html,detail.html}
  reservations/{confirmation.html,customer_list.html}
  restaurants/{dashboard.html,food_form.html,reservation_list.html,profile_form.html}
  impact/dashboard.html
static/
  css/app.css
  js/app.js
media/.gitkeep
tests/
  __init__.py
  helpers.py
  test_smoke.py
```

## Task 1: Scaffold the Django project and configuration

**Files:**
- Create: `manage.py`, `rescue_bite/{__init__.py,settings.py,urls.py,asgi.py,wsgi.py}`
- Create: `requirements.txt`, `.env.example`, `.gitignore`, `README.md`
- Create: app directories and minimal `apps.py`, `__init__.py` files
- Create: `templates/base.html`, `static/css/app.css`, `static/js/app.js`, `media/.gitkeep`
- Test: `tests/test_smoke.py`

**Interfaces:**
- Produces a runnable Django project with `DJANGO_SETTINGS_MODULE=rescue_bite.settings`.
- Settings expose `FOOD_WEIGHT_KG` and `CO2_KG_PER_KG_FOOD` as configurable impact constants.
- URL root includes `accounts.urls`, `food.urls`, `reservations.urls`, `restaurants.urls`, `reviews.urls`, `notifications.urls`, and `impact.urls`.

- [ ] **Step 1: Write the failing project smoke test.**

```python
# tests/test_smoke.py
from django.test import SimpleTestCase
from django.urls import reverse


class ProjectSmokeTests(SimpleTestCase):
    def test_homepage_is_reachable(self):
        response = self.client.get(reverse("food:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Rescue Bite")
```

- [ ] **Step 2: Run the test and confirm it fails because the project does not exist.**

Run: `python manage.py test tests.test_smoke.ProjectSmokeTests.test_homepage_is_reachable`

Expected: failure because `manage.py`, settings, and the `food:home` URL are not yet defined.

- [ ] **Step 3: Add the minimum Django project and placeholder home view.**

Use `django-admin startproject rescue_bite .` and create the seven apps. Configure `INSTALLED_APPS`, templates, static/media paths, `LOGIN_URL`, `LOGIN_REDIRECT_URL`, `LOGOUT_REDIRECT_URL`, `TIME_ZONE = "Asia/Kuala_Lumpur"`, `USE_TZ = True`, and environment-driven `SECRET_KEY`, `DEBUG`, and `ALLOWED_HOSTS`. Add this temporary view until Task 2 replaces it:

```python
# food/views.py
from django.shortcuts import render


def home(request):
    return render(request, "food/home.html", {"featured_listings": []})
```

- [ ] **Step 4: Add the base layout and minimal home template.**

`base.html` must include the viewport meta tag, Tailwind CDN, `{% csrf_token %}` support through forms, navigation include, messages include, `{% block content %}`, and footer include. `food/home.html` must show the Rescue Bite name, tagline, and a link to `food:discover`.

- [ ] **Step 5: Run the smoke test and Django checks.**

Run: `python manage.py test tests.test_smoke -v 2 && python manage.py check`

Expected: one passing test and no system-check errors.

- [ ] **Step 6: Commit the scaffold.**

```bash
git add .
git commit -m "chore: scaffold Rescue Bite Django project"
```

## Task 2: Implement accounts, profiles, registration, and role protection

**Files:**
- Create/modify: `accounts/models.py`, `accounts/forms.py`, `accounts/views.py`, `accounts/urls.py`, `accounts/admin.py`, `accounts/tests.py`
- Create: `templates/accounts/{login.html,register.html,profile.html}`
- Modify: `rescue_bite/settings.py`, `rescue_bite/urls.py`, `templates/includes/navbar.html`
- Test: `accounts/tests.py`

**Interfaces:**
- `User.objects.create_user(email, password, name, role)` creates a normalized email user.
- `accounts.views.role_required(role)` returns a decorator that redirects unauthenticated users to login and wrong-role users to a safe dashboard.
- `accounts.forms.RegisterForm` accepts `email`, `name`, `password1`, `password2`, and `role`.
- `accounts.models.CustomerProfile` is one-to-one with a customer user.

- [ ] **Step 1: Write failing tests for user creation, registration, login, and role restrictions.**

```python
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class AccountTests(TestCase):
    def test_create_user_normalizes_email_and_sets_role(self):
        user = get_user_model().objects.create_user(
            email=" Student@Example.com ", password="StrongPass123!", name="Aiman", role="CUSTOMER"
        )
        self.assertEqual(user.email, "student@example.com")
        self.assertEqual(user.role, "CUSTOMER")
        self.assertTrue(user.check_password("StrongPass123!"))

    def test_customer_registration_creates_profile(self):
        response = self.client.post(reverse("accounts:register"), {
            "email": "customer@example.com", "name": "Sarah", "role": "CUSTOMER",
            "password1": "StrongPass123!", "password2": "StrongPass123!",
        })
        self.assertRedirects(response, reverse("food:discover"))
        self.assertTrue(get_user_model().objects.get(email="customer@example.com").customer_profile)

    def test_restaurant_owner_cannot_open_customer_dashboard(self):
        owner = get_user_model().objects.create_user(
            email="owner@example.com", password="StrongPass123!", name="Owner", role="RESTAURANT_OWNER"
        )
        self.client.force_login(owner)
        response = self.client.get(reverse("accounts:customer_dashboard"))
        self.assertRedirects(response, reverse("restaurants:dashboard"))
```

- [ ] **Step 2: Run the tests and confirm they fail for missing models, forms, and URLs.**

Run: `python manage.py test accounts -v 2`

Expected: failures caused by the absent custom user model and account routes, not test syntax errors.

- [ ] **Step 3: Implement the custom user and customer profile.**

Use `AbstractBaseUser` and `PermissionsMixin`; set `USERNAME_FIELD = "email"`; add `is_staff`, `is_active`, `created_at`, and a manager with `create_user` and `create_superuser`. Add role choices `CUSTOMER` and `RESTAURANT_OWNER`. Set `AUTH_USER_MODEL = "accounts.User"` before the first migration. Use a post-save signal or registration transaction to create `CustomerProfile` only for customers.

- [ ] **Step 4: Implement forms, views, URLs, and templates.**

Use Django `AuthenticationForm` for login and `login()`/`logout()` for sessions. On registration, save the user and profile in `transaction.atomic()`. Redirect customers to `accounts:customer_dashboard`/discover and owners to `restaurants:dashboard`. Add `customer_dashboard`, `customer_reservations`, and `profile` routes with `@login_required` and role guards. Never expose another user’s profile or reservations.

- [ ] **Step 5: Run migrations, tests, and checks.**

Run: `python manage.py makemigrations accounts && python manage.py migrate && python manage.py test accounts tests.test_smoke -v 2 && python manage.py check`

Expected: all account and smoke tests pass.

- [ ] **Step 6: Commit the account foundation.**

```bash
git add accounts rescue_bite templates .
git commit -m "feat: add role-based accounts and authentication"
```

## Task 3: Implement restaurants and food listings

**Files:**
- Create/modify: `restaurants/models.py`, `restaurants/forms.py`, `restaurants/views.py`, `restaurants/urls.py`, `restaurants/admin.py`, `restaurants/tests.py`
- Create/modify: `food/models.py`, `food/forms.py`, `food/views.py`, `food/urls.py`, `food/admin.py`, `food/tests.py`
- Create: `templates/food/{discover.html,detail.html}`, `templates/restaurants/{dashboard.html,food_form.html,profile_form.html}`
- Create: `templates/includes/{food_card.html,empty_state.html}`

**Interfaces:**
- `Restaurant` has one owner and fields for name, description, address, location, phone, image, and timestamps.
- `FoodListing.calculate_discounted_price()` returns a `Decimal` rounded to two places.
- `FoodListing.is_expired(at=None)` checks the configured pickup date/end time in the project timezone.
- `FoodListing.refresh_status(at=None)` changes active listings to `EXPIRED` or `SOLD_OUT` and saves only when needed.
- `food.views.discover` accepts `q`, `category`, `max_price`, `min_discount`, `sort`, and `location` query parameters.

- [ ] **Step 1: Write failing model and form tests.**

```python
from datetime import date, time, timedelta
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone


class FoodListingTests(TestCase):
    def test_discounted_price_is_calculated_from_original_price(self):
        listing = FoodListing(original_price=Decimal("12.00"), discount_percentage=50)
        self.assertEqual(listing.calculate_discounted_price(), Decimal("6.00"))

    def test_discount_outside_forty_to_sixty_is_rejected(self):
        listing = FoodListing(original_price=Decimal("10.00"), discount_percentage=35)
        with self.assertRaises(ValidationError):
            listing.full_clean()

    def test_expired_listing_cannot_remain_active(self):
        yesterday = timezone.localdate() - timedelta(days=1)
        listing = make_listing(pickup_date=yesterday, pickup_end=time(23, 0))
        listing.refresh_status()
        self.assertEqual(listing.status, FoodListing.Status.EXPIRED)
```

- [ ] **Step 2: Run the tests and confirm they fail because the models do not exist.**

Run: `python manage.py test food restaurants -v 2`

Expected: failures caused by missing `Restaurant`/`FoodListing` implementations.

- [ ] **Step 3: Implement `Restaurant` and `FoodListing`.**

Use `DecimalField(max_digits=8, decimal_places=2)` for prices, `PositiveIntegerField` for quantity, `PositiveSmallIntegerField` for discount, `DateField` for `pickup_date`, and `TimeField` for pickup times. Add model validation for price, discount, quantity, and time order. Make `discounted_price` a stored field recalculated in `clean()`/`save()`. Add indexes for active status, pickup date, category, and restaurant.

- [ ] **Step 4: Implement owner forms and listing CRUD.**

`RestaurantForm` creates or edits only the authenticated owner’s restaurant. `FoodListingForm` accepts image upload, computes a client preview through JavaScript, and trusts only the server-side model calculation. Owner views must filter by `restaurant__owner=request.user` for edit/delete/dashboard actions.

- [ ] **Step 5: Implement discovery, detail, search, filters, sorting, and homepage featured listings.**

Only active, non-expired listings appear. Use `select_related("restaurant")`. Detail pages include restaurant information, current price, discount, quantity, pickup window, countdown data attributes, and review summary placeholders for Task 6. Homepage shows up to six active featured listings and dynamic platform counters from the impact service when available.

- [ ] **Step 6: Add listing templates and responsive food cards.**

The card must show a real/demo image with descriptive alt text, restaurant, location, original price with a strikethrough, final price, discount badge, pickup window, remaining quantity, status, and an accessible Reserve Now link/button. Use a mobile grid that collapses from four columns to one.

- [ ] **Step 7: Run migrations, tests, and checks.**

Run: `python manage.py makemigrations restaurants food && python manage.py migrate && python manage.py test food restaurants tests.test_smoke -v 2 && python manage.py check`

- [ ] **Step 8: Commit restaurant and listing functionality.**

```bash
git add restaurants food templates
git commit -m "feat: add restaurants and surplus food listings"
```

## Task 4: Implement race-safe reservations and customer booking flows

**Files:**
- Create/modify: `reservations/models.py`, `reservations/forms.py`, `reservations/services.py`, `reservations/views.py`, `reservations/urls.py`, `reservations/admin.py`, `reservations/tests.py`
- Create: `templates/reservations/{confirmation.html,customer_list.html}`
- Modify: `food/templates` detail context and `templates/includes/navbar.html`

**Interfaces:**
- `ReservationServiceError` carries a user-safe message and error code.
- `create_reservation(*, customer, listing_id, quantity) -> Reservation` performs all validation and inventory mutation inside one atomic transaction.
- `cancel_reservation(*, reservation, actor) -> Reservation` enforces customer ownership and permitted statuses.
- `mark_collected(*, reservation, actor) -> Reservation` enforces restaurant ownership and changes `RESERVED` to `COLLECTED`.

- [ ] **Step 1: Write failing tests for reservation totals, inventory reduction, expiry, sold-out behavior, and ownership.**

```python
class ReservationServiceTests(TestCase):
    def test_create_reservation_reduces_inventory_and_uses_server_price(self):
        listing = make_listing(original_price=Decimal("10.00"), discount_percentage=50, quantity=5)
        reservation = create_reservation(customer=self.customer, listing_id=listing.pk, quantity=2)
        listing.refresh_from_db()
        self.assertEqual(reservation.total_price, Decimal("10.00"))
        self.assertEqual(listing.quantity, 3)

    def test_create_reservation_rejects_more_than_available(self):
        listing = make_listing(quantity=1)
        with self.assertRaises(ReservationServiceError):
            create_reservation(customer=self.customer, listing_id=listing.pk, quantity=2)

    def test_create_reservation_rejects_expired_listing(self):
        listing = make_expired_listing()
        with self.assertRaises(ReservationServiceError):
            create_reservation(customer=self.customer, listing_id=listing.pk, quantity=1)

    def test_owner_can_mark_only_own_reservation_collected(self):
        reservation = make_reservation()
        mark_collected(reservation=reservation, actor=reservation.food_listing.restaurant.owner)
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, Reservation.Status.COLLECTED)
```

- [ ] **Step 2: Run the tests and confirm they fail for missing service/model behavior.**

Run: `python manage.py test reservations -v 2`

Expected: failures because the reservation model and service do not yet exist.

- [ ] **Step 3: Implement `Reservation` and reservation codes.**

Add customer, food listing, quantity, total price, status, unique `reservation_code`, created/updated timestamps, and optional cancellation/collection timestamps. Use a readable `RB-` code generated in model save or a helper, with a uniqueness retry strategy. Add indexes for customer/status and listing/status.

- [ ] **Step 4: Implement the atomic reservation service.**

Inside `transaction.atomic()`, query the listing using `select_for_update()`, call `refresh_status()`, validate customer role, quantity, expiry, status, and available quantity, calculate `discounted_price * quantity`, create the reservation, decrement inventory, set sold out when zero, and create a notification record. Raise `ReservationServiceError` for all expected user-facing failures.

- [ ] **Step 5: Implement reservation forms, views, and URLs.**

The detail page posts to `reservations:create`. The form limits quantity client-side but the service validates again. The confirmation view retrieves by code and customer. Customer reservation history filters by `customer=request.user`. Cancellation is POST-only and cannot cancel collected, cancelled, or expired reservations. Owner collection uses a POST-only route with role and ownership checks.

- [ ] **Step 6: Run focused tests, then the full suite.**

Run: `python manage.py test reservations -v 2 && python manage.py test -v 2`

Expected: reservation tests and all previous tests pass with no warnings from Django checks.

- [ ] **Step 7: Commit reservation functionality.**

```bash
git add reservations templates food
git commit -m "feat: add atomic food reservations and inventory safety"
```

## Task 5: Implement restaurant dashboards and reservation management

**Files:**
- Modify: `restaurants/views.py`, `restaurants/urls.py`, `restaurants/forms.py`, `templates/restaurants/{dashboard.html,reservation_list.html,profile_form.html}`
- Modify: `reservations/views.py`, `reservations/urls.py`, `reservations/tests.py`

**Interfaces:**
- `restaurants.views.dashboard` returns active listing count, reservation count, collected meal count, and recovered revenue.
- `restaurants.views.reservation_list` returns only reservations for the owner’s restaurant.
- Dashboard cards and listing rows display Active, Low Stock, Sold Out, and Expired status.

- [ ] **Step 1: Write failing dashboard and permission tests.**

```python
def test_owner_dashboard_excludes_other_restaurants(self):
    owner = make_owner()
    other_owner = make_owner()
    make_listing(restaurant=make_restaurant(owner=other_owner))
    self.client.force_login(owner)
    response = self.client.get(reverse("restaurants:dashboard"))
    self.assertNotContains(response, "Other Restaurant")


def test_customer_cannot_open_restaurant_dashboard(self):
    customer = make_customer()
    self.client.force_login(customer)
    response = self.client.get(reverse("restaurants:dashboard"))
    self.assertRedirects(response, reverse("accounts:customer_dashboard"))
```

- [ ] **Step 2: Run the tests and confirm they fail.**

Run: `python manage.py test restaurants reservations -v 2`

- [ ] **Step 3: Implement owner dashboard queries and reservation status actions.**

Use `select_related`/`prefetch_related`; calculate recovered revenue from collected reservations; expose status labels and counts. Restrict collection and cancellation operations through the service layer and owner/customer checks.

- [ ] **Step 4: Build responsive dashboard templates.**

Use summary cards, a desktop table, and mobile listing cards. Provide an obvious “Add Surplus Food” CTA, edit/delete controls, reservation status badges, and an empty state when no listings exist.

- [ ] **Step 5: Run tests and commit.**

Run: `python manage.py test -v 2 && python manage.py check`

```bash
git add restaurants reservations templates
git commit -m "feat: add restaurant dashboards and collection workflow"
```

## Task 6: Implement notifications, reviews, and impact tracking

**Files:**
- Create/modify: `notifications/models.py`, `notifications/views.py`, `notifications/urls.py`, `notifications/admin.py`, `notifications/tests.py`
- Create/modify: `reviews/models.py`, `reviews/forms.py`, `reviews/views.py`, `reviews/urls.py`, `reviews/admin.py`, `reviews/tests.py`
- Create/modify: `impact/services.py`, `impact/views.py`, `impact/urls.py`, `impact/admin.py`, `impact/tests.py`
- Modify: `reservations/services.py`, `food/views.py`, `templates/food/detail.html`, `templates/impact/dashboard.html`, `templates/includes/navbar.html`, `static/js/app.js`

**Interfaces:**
- `Notification.objects.for_customer(user)` returns newest notifications for the customer.
- `create_reservation()` creates a reservation notification.
- `ReviewForm` accepts only `rating` and `comment`; customer, restaurant, listing, and reservation come from the server.
- `get_platform_impact()` returns a dictionary with `meals_served`, `food_saved_kg`, `co2_avoided_kg`, `restaurants`, `reservations`, `monthly_meals`, and `customer_savings`.
- `get_customer_impact(user)` and `get_restaurant_impact(restaurant)` return the same metric shape scoped to the owner.

- [ ] **Step 1: Write failing tests for notification creation, review eligibility, and impact calculations.**

```python
def test_reservation_creates_customer_notification(self):
    reservation = create_reservation(customer=self.customer, listing_id=self.listing.pk, quantity=1)
    self.assertTrue(Notification.objects.filter(customer=self.customer, notification_type="RESERVATION").exists())


def test_customer_can_review_only_collected_reservation(self):
    reservation = make_reservation(customer=self.customer, status=Reservation.Status.COLLECTED)
    response = self.client.post(reverse("reviews:create", kwargs={"reservation_id": reservation.pk}), {
        "rating": 5, "comment": "Fresh and affordable.",
    })
    self.assertEqual(response.status_code, 302)
    self.assertEqual(Review.objects.count(), 1)


def test_impact_counts_collected_meals_only(self):
    make_reservation(quantity=2, status=Reservation.Status.COLLECTED)
    make_reservation(quantity=3, status=Reservation.Status.RESERVED)
    impact = get_platform_impact()
    self.assertEqual(impact["meals_served"], 2)
    self.assertEqual(impact["food_saved_kg"], Decimal("1.00"))
```

- [ ] **Step 2: Run the tests and confirm the new behaviors fail.**

Run: `python manage.py test notifications reviews impact -v 2`

- [ ] **Step 3: Implement notifications and notification UI.**

Create notification records for reservation confirmation, collection/status changes, new listings, and ending-soon messages where the request path makes the event available. Add unread count and a POST mark-read endpoint protected by customer ownership. Render a dropdown and dismissible toast using Vanilla JavaScript.

- [ ] **Step 4: Implement review eligibility and rating aggregation.**

Require a collected reservation belonging to the logged-in customer, enforce one review per reservation with a database constraint, and calculate restaurant/listing average ratings from actual reviews. Render review cards and a review form only when eligible.

- [ ] **Step 5: Implement impact services and page.**

Use `settings.FOOD_WEIGHT_KG` and `settings.CO2_KG_PER_KG_FOOD`; count collected reservation quantities as meals served; calculate food saved and estimated CO₂; calculate savings from original minus discounted prices. Add a clean impact story, metric cards, monthly values, and a CSS/Vanilla JS bar chart without Chart.js.

- [ ] **Step 6: Run all tests and commit.**

Run: `python manage.py test -v 2 && python manage.py check`

```bash
git add notifications reviews impact reservations food templates static
git commit -m "feat: add notifications reviews and impact tracking"
```

## Task 7: Add demo data, admin configuration, and frontend polish

**Files:**
- Create: `food/management/commands/seed_demo.py`
- Modify: all app `admin.py` files, `templates/base.html`, `templates/includes/*`, `static/css/app.css`, `static/js/app.js`
- Create/modify: `templates/food/home.html`, `templates/accounts/profile.html`, `templates/restaurants/*`, `templates/impact/dashboard.html`

**Interfaces:**
- `python manage.py seed_demo --clear` creates repeatable demo users, restaurants, listings, reservations, reviews, and notifications.
- Demo credentials are documented in README and use non-production passwords.
- All admin list pages have useful `list_display`, `search_fields`, filters, and safe relationship fields.

- [ ] **Step 1: Write a failing seed-command test.**

```python
from io import StringIO
from django.core.management import call_command


def test_seed_demo_creates_populated_platform(self):
    output = StringIO()
    call_command("seed_demo", stdout=output)
    self.assertGreaterEqual(FoodListing.objects.count(), 5)
    self.assertGreaterEqual(Restaurant.objects.count(), 3)
    self.assertIn("Demo data created", output.getvalue())
```

- [ ] **Step 2: Run the test and confirm the command is missing.**

Run: `python manage.py test food -v 2`

- [ ] **Step 3: Implement deterministic demo data.**

Create `demo.customer@rescuebite.test` and `demo.owner@rescuebite.test`, five Malaysian restaurants, realistic RM prices, food categories, pickup windows, stable Unsplash image URLs matching each food, collected/reserved reservations, reviews, and notifications. Make the command idempotent by using `get_or_create` and support `--clear` only for the explicitly named demo records.

- [ ] **Step 4: Configure admin.**

Register all models with readable displays, filters for status/role/date, search for names/emails/codes, and readonly calculated fields where appropriate. Do not expose passwords.

- [ ] **Step 5: Polish shared UI and JavaScript.**

Add responsive navbar and mobile menu, flash alerts, focus styles, card/button/status classes, quantity controls, discount preview, modal close/Escape behavior, countdown timers based on ISO data attributes, search/filter form preservation, confirmation dialogs, notification toast, and accessible `aria-expanded`/`aria-live` attributes.

- [ ] **Step 6: Run seed data, inspect pages, and commit.**

Run: `python manage.py seed_demo --clear && python manage.py test -v 2 && python manage.py check`

```bash
git add .
git commit -m "feat: add demo data admin and polished responsive UI"
```

## Task 8: Complete documentation, deployment configuration, and final verification

**Files:**
- Modify: `README.md`, `.env.example`, `requirements.txt`, `rescue_bite/settings.py`
- Create: `Procfile` or deployment command documentation, `render.yaml` only if a supported host is selected, and `tests/test_final_flows.py`

**Interfaces:**
- A new user can follow README commands from an empty checkout through migration, seed data, superuser creation, and server start.
- Production settings never require a committed secret and document a Django-compatible host; Vercel limitations are explained rather than hidden.

- [ ] **Step 1: Write failing end-to-end flow tests.**

```python
def test_customer_can_discover_reserve_and_view_confirmation(self):
    response = self.client.get(reverse("food:discover"))
    self.assertEqual(response.status_code, 200)
    response = self.client.post(reverse("reservations:create", kwargs={"listing_id": self.listing.pk}), {"quantity": 1})
    self.assertEqual(response.status_code, 302)
    confirmation = self.client.get(response.url)
    self.assertContains(confirmation, "Reservation Confirmed")


def test_owner_can_publish_and_customer_cannot_publish(self):
    self.client.force_login(self.customer)
    response = self.client.get(reverse("restaurants:food_create"))
    self.assertEqual(response.status_code, 302)
```

- [ ] **Step 2: Run the test and confirm any missing integration is visible.**

Run: `python manage.py test tests.test_final_flows -v 2`

- [ ] **Step 3: Complete README and environment configuration.**

Document virtual environment setup, `pip install -r requirements.txt`, `.env` creation, migrations, `seed_demo`, `createsuperuser`, local media/static behavior, demo credentials, test commands, production static/media handling, PostgreSQL environment variables, and why a traditional Django deployment is preferable to Vercel for this server-rendered MVP.

- [ ] **Step 4: Run the complete verification suite.**

Run:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test -v 2
python manage.py seed_demo --clear
python manage.py test -v 2
```

Expected: system checks pass, no model changes are missing, all tests pass before and after demo seeding, and no secrets are committed.

- [ ] **Step 5: Perform a manual browser smoke check.**

Start `python manage.py runserver`, then verify home, discovery/search/filter, food details, registration, customer reservation/confirmation/history, owner listing creation/edit/delete, owner collection, notifications, reviews, impact metrics, mobile navigation, and expired/sold-out states at desktop and mobile widths.

- [ ] **Step 6: Commit the completed project.**

```bash
git add .
git commit -m "docs: finalize Rescue Bite setup and deployment guidance"
```

## Plan self-review

- Spec coverage: accounts, roles, restaurant profiles, listings, discounts, discovery, reservations, locking, expiry, dashboards, notifications, reviews, impact, demo data, admin, accessibility, responsive UI, tests, README, and deployment are covered by Tasks 1–8.
- Placeholder scan: no implementation step is delegated with “similar”, “later”, “TBD”, or “TODO”; each task names files, interfaces, tests, commands, and expected outcomes.
- Type consistency: reservation services return `Reservation`; impact services return dictionaries; listing methods use `Decimal`, timezone-aware date/time handling, and the same status choices throughout.
- Scope: excluded payment, chat, delivery tracking, complex maps, AI recommendations, microservices, and unnecessary APIs remain excluded.

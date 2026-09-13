# Rescue Bite Design Specification

## Goal

Build a complete Django MVT social-business MVP that connects restaurants with customers seeking discounted surplus food before closing time.

## Product identity

- Product name: Rescue Bite
- Tagline: Rescue Good Food. Reduce Waste. Save More.
- Primary audience: students and budget-conscious customers in Malaysia
- Core customer flow: Discover → Check → Reserve → Collect → Review
- Core restaurant flow: Post → Discount → Sell → Reduce Waste → Track impact
- Visual direction: premium, clean, modern, friendly, trustworthy, and mobile-first
- Colors: emerald green for action/impact and midnight blue for structure/headings
- Demo photography: real food photographs from stable Unsplash image URLs; demo images will be labelled as demo content where appropriate

## Scope

The MVP includes:

1. Customer and restaurant-owner registration, login, logout, and role-based access.
2. Restaurant profiles and owner dashboards.
3. Food listings with images, categories, prices, 40–60% discounts, quantities, locations, and pickup windows.
4. Customer discovery with search, filtering, sorting, food details, and countdowns.
5. Reservations using pay-at-collection, quantity selection, confirmation codes, and reservation history.
6. Race-safe inventory updates using database transactions and row locking.
7. Restaurant reservation management and collected/cancelled status updates.
8. Notifications for reservations, newly listed food, status changes, and ending-soon listings.
9. Eligible customer reviews with ratings and comments.
10. Database-backed impact statistics for meals served, food saved, estimated CO₂ avoided, restaurant participation, and customer savings.
11. Responsive Tailwind templates, accessible controls, Vanilla JavaScript interactions, Django Admin configuration, seed data, tests, README, and deployment guidance.

The MVP deliberately excludes online payments, delivery tracking, live chat, complex maps, AI recommendations, microservices, and unnecessary APIs.

## Architecture

The project uses Django’s Model–View–Template architecture with server-rendered pages and small Vanilla JavaScript enhancements. The local database is SQLite; settings use environment variables so PostgreSQL can be used in production. The project is configured for the `Asia/Kuala_Lumpur` timezone.

### Django apps

- `accounts`: custom email-based user, role selection, customer profile, authentication, and role guards.
- `restaurants`: restaurant profile, owner dashboard queries, and restaurant administration.
- `food`: food listing model, forms, publishing/editing, discovery, expiry, filtering, and price validation.
- `reservations`: reservation model, reservation service, confirmation pages, status transitions, and inventory locking.
- `reviews`: review model, eligibility checks, review form, and rating aggregation.
- `notifications`: notification model, unread counts, dropdown data, and toast messages.
- `impact`: reusable impact calculations and customer/restaurant/platform summaries.

Shared templates use `base.html`, reusable partials, accessible form components, cards, badges, alerts, empty states, and responsive navigation. Tailwind is loaded through a CDN for easy university-project setup, with a small custom stylesheet for tokens and components; no Node or frontend framework is required.

## Data model and business rules

- `User` has `email`, `name`, `role`, and timestamps.
- `CustomerProfile` is one-to-one with a customer user.
- `Restaurant` is one-to-one with an owner and stores contact/location data.
- `FoodListing` belongs to a restaurant and stores the original price, discount, calculated discounted price, quantity, pickup times, image, and status.
- `Reservation` belongs to a customer and food listing and stores quantity, total price, code, status, and timestamps.
- `Review` links a customer, restaurant, food listing, and reservation.
- `Notification` belongs to a customer and stores type, message, read state, and timestamp.

Server-side rules are authoritative: discount must be 40–60%; prices and quantities cannot be negative; pickup end must follow pickup start; expired/sold-out listings cannot be reserved; users can access only their own records; only eligible customers can review; and owners can modify only their own listings.

## Reservation data flow

1. Customer submits a reservation quantity.
2. The reservation service enters `transaction.atomic()` and locks the selected `FoodListing` with `select_for_update()`.
3. The service refreshes expiry/status, validates quantity and availability, calculates the total from the server-side discounted price, creates the reservation, and decrements inventory.
4. It marks the listing sold out when quantity reaches zero and creates a confirmation notification.
5. The confirmation page displays the reservation code, pickup window, quantity, amount, and pay-at-collection instruction.

Restaurant collection updates drive the impact metrics. Food weight and CO₂ values are configurable constants in the impact utility and are explicitly labelled as estimates.

## Error handling and accessibility

Forms display friendly validation messages. Expired, unavailable, unauthorized, and invalid operations return user-facing error states rather than raw exceptions. Pages use semantic headings, labels, alt text, visible focus states, keyboard-friendly controls, sufficient contrast, and non-colour status indicators.

## Testing strategy

Django tests cover registration/login, role protection, model/form validation, discount calculation, listing ownership, reservation creation, concurrent-safe inventory reduction, expiry, sold-out handling, reservation status changes, review eligibility, notifications, and impact aggregation. Core reservation and calculation behavior is written test-first.

## Delivery structure

Implementation proceeds in independently testable phases:

1. Project foundation, settings, custom user, profiles, and authentication.
2. Restaurant and food-listing models, forms, views, discovery, and responsive templates.
3. Reservation service, inventory safety, confirmation pages, and dashboards.
4. Notifications, reviews, impact calculations, and admin.
5. Seed data, frontend polish, tests, README, environment configuration, and deployment instructions.

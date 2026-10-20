# FreshBite — Django Food Ordering Starter

Responsive Django web app starter for a small food shop. Customers can order from phones or desktop browsers, choose delivery or pickup, select cash or Razorpay online payment, and track order status with a private token URL. Shop owners manage menu items and order status in Django Admin.

> This is a starter, not a fully audited production payment platform. Test in Razorpay test mode first. Before taking real payments, configure and test gateway webhooks/idempotency, backups, privacy notices, delivery policies, and operational support.

## Included
- Responsive Bootstrap menu, cart, checkout, confirmation, tracking timeline
- Menu and orders in Django database
- Private random tracking token (do not publish customer links)
- Delivery fee default ₹30; pickup fee ₹0
- Cash payment and optional Razorpay checkout with signature verification and server-side payment fetch
- Django Admin for food/menu and order status management
- PostgreSQL support through `DATABASE_URL`; SQLite local development
- Production static assets via WhiteNoise

## Local setup (Windows PowerShell)
1. Install Python 3.11+.
2. Extract the ZIP and open PowerShell in the `food_ordering_django` folder.
3. Create and activate a virtual environment:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

4. Set a strong `DJANGO_SECRET_KEY` in your environment before deploying. The sample app reads environment variables directly; PowerShell example for local run:

```powershell
$env:DJANGO_DEBUG="True"
$env:DJANGO_SECRET_KEY="local-only-change-this-secret"
$env:DJANGO_ALLOWED_HOSTS="127.0.0.1,localhost"
python manage.py makemigrations orders
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

5. Open http://127.0.0.1:8000/admin/ and sign in. Add `Food items`, then open http://127.0.0.1:8000/ to place a test order. In the admin, open the order and change `status` to test tracking updates.

### macOS/Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export DJANGO_DEBUG=True
export DJANGO_SECRET_KEY='local-only-change-this-secret'
python manage.py makemigrations orders
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Razorpay test setup
1. Create a Razorpay account and use test-mode API credentials.
2. Set `RAZORPAY_KEY_ID` and `RAZORPAY_KEY_SECRET` as server environment variables. Never commit them or expose the secret in HTML/JavaScript.
3. Set `PUBLIC_BASE_URL` to your deployed HTTPS URL.
4. Test successful, failed, abandoned, duplicate, and delayed payments. Verify captured payment amount/currency and implement configured Razorpay webhooks before production use. For production, handle webhook signatures and idempotency, and reconcile payment state from the gateway.
5. Online payment checkout requires a public HTTPS site in normal deployment. If credentials are absent, the app tells the customer online payments are not configured.

## Deployment outline
Choose a Django-compatible host (for example Render, Railway, Fly.io, or a VPS) with persistent PostgreSQL. The exact dashboard labels vary by provider.

1. Push this project to a private Git repository (do not commit `.env`, database files, API keys, or secrets).
2. Create a web service with build command `pip install -r requirements.txt` and start command `gunicorn config.wsgi:application`.
3. Provision PostgreSQL and set `DATABASE_URL` to its connection URL.
4. Set environment variables: `DJANGO_SECRET_KEY` (random secret), `DJANGO_DEBUG=False`, `DJANGO_ALLOWED_HOSTS=your-domain.example`, `CSRF_TRUSTED_ORIGINS=https://your-domain.example`, `PUBLIC_BASE_URL=https://your-domain.example`, and Razorpay credentials if enabled.
5. Run `python manage.py migrate` and `python manage.py createsuperuser` as release/one-off commands.
6. Ensure the host runs `python manage.py collectstatic --noinput` during build/release; WhiteNoise serves the collected static files.
7. Configure HTTPS, a custom domain, database backups, uptime/exception monitoring, and a tested restore process.
8. Visit `/admin/`, add menu items, test a full cash order and payment in gateway test mode, then launch.

## Important configuration
- Delivery fee: set environment variable `DELIVERY_FEE` (default `30.00`).
- `DEBUG` must be false in production. Use a long, unique `DJANGO_SECRET_KEY`.
- `ALLOWED_HOSTS` is a comma-separated list of hostnames (no scheme).
- `CSRF_TRUSTED_ORIGINS` is comma-separated full origins including `https://`.
- For PostgreSQL, set `DATABASE_URL` to the provider's PostgreSQL connection URL.

## Security and production checklist
- [ ] Set a unique secret key and keep all credentials in hosting environment secrets.
- [ ] Set `DEBUG=False`, exact `ALLOWED_HOSTS`, trusted HTTPS origins, and force HTTPS.
- [ ] Use PostgreSQL, automated backups, and verify restoration.
- [ ] Use a private admin account, strong password, MFA at the hosting/provider level where available, and restrict admin access if possible.
- [ ] Add rate limiting/bot protection to checkout and payment endpoints; monitor errors and abuse.
- [ ] Keep Django and dependencies patched; run `python manage.py check --deploy` before launch.
- [ ] Configure gateway webhooks, signature validation, idempotency, and payment reconciliation. Do not trust browser redirects as proof of payment.
- [ ] Decide whether `authorized` payments should be captured immediately; this starter attempts capture and should be tested against your gateway account settings.
- [ ] Protect customer personal data; publish a privacy policy and retention/deletion policy. Do not collect card details directly.
- [ ] Add cancellation/refund workflows, stock management, delivery zones/fees, and customer support contacts as needed.
- [ ] Use a messaging provider for real WhatsApp/SMS notifications; the current tracking page refreshes status every 10 seconds while open.
- [ ] Consider replacing public order UUID confirmation URLs with a token-protected confirmation page before launch; tracking pages use random tokens.
- [ ] Set up logs, monitoring, alerting, and a process for responding to failed orders or payment discrepancies.

## Current limitations / next improvements
- The cart is browser-side and validated against current database item prices at checkout; add stock checks and transactional inventory for inventory-sensitive shops.
- Customer checkout does not require an account. The tracking token acts as a bearer secret: share it only with the intended customer.
- No email/SMS/WhatsApp notifications, maps, coupons, tax invoice, refund workflow, or automatic delivery assignment are included.
- Online payment code is a basic integration example. A production system should add a signed webhook endpoint with idempotent event processing and compare payment amount/currency against the order before marking paid.
- Admin order status changes are managed through Django Admin. Staff roles and a purpose-built operations dashboard can be added next.

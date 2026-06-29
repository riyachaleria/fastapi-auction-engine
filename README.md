# 🏷️ BidBazaar Live Auction API

A production-ready, high-performance RESTful API for a real-time auction platform. Built with FastAPI and PostgreSQL, this system handles secure live bidding, automated Stripe checkout workflows, and scheduled background jobs to process expired auctions seamlessly.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-00a393.svg)
![SQLModel](https://img.shields.io/badge/SQLModel-Database-black.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-336791.svg)
![Stripe](https://img.shields.io/badge/Stripe-Payments-blueviolet.svg)

## 🎯 Overview

BidBazaar is engineered to solve the complex concurrency and synchronization problems inherent in live auction platforms. It serves as a scalable backend enabling users to list items, securely bid in real-time without refreshing, and seamlessly transition into an automated checkout flow when they win.

### Business Problem Solved
When facilitating peer-to-peer live auctions, platforms require a robust infrastructure to:
- Handle high-frequency concurrent bids in real-time via WebSockets.
- Guarantee transaction integrity and prevent race conditions on item prices.
- Autonomously detect when auctions expire and correctly identify the winning bidder.
- Facilitate split-payments, ensuring the platform takes a fee while routing funds directly to the seller via Stripe Connect.
- Automatically email buyers and sellers at every step of the transaction lifecycle.

## 🚀 Features

- **⚡ Real-Time Bidding Engine:** WebSockets stream the highest bid live to all connected clients ensuring nobody has stale data.
- **🕒 Background Task Automation:** Integrated `APScheduler` scans for expired auctions natively via background threads, closes them, and mints secure one-time checkout tokens.
- **💳 Stripe Connect Integration:** End-to-end checkout automation capturing a 5% platform fee and transferring 95% of the funds securely to the seller. Webhooks automatically finalize the transaction.
- **🔐 Secure Authentication Layer:** JWT-based stateless authentication with strict password complexity requirements and bcrypt hashing.
- **📧 Transactional SMTP Emails:** Automated notifications for welcome messages, winning bids, payment receipts, and automated refund processing (with elegant HTML fallbacks).
- **💸 Refund Automation:** Seamless API integration allowing verified buyers to initiate full refunds, which automatically reverses Stripe payment intents, updates the database, and notifies all parties.
- **🗄️ Enterprise Database Models:** Backed by `PostgreSQL` and `SQLModel` with strong foreign-key enforcement and strict `Pydantic` payload sanitization.

## 🛠️ Tech Stack

- **Framework**: FastAPI (Python 3.10+)
- **Database**: PostgreSQL
- **ORM**: SQLModel / SQLAlchemy
- **Payment Processing**: Stripe API & Webhooks
- **Job Scheduling**: APScheduler
- **Testing**: `pytest`, `pytest-cov`, and `TestClient`
- **Environment Management**: python-dotenv
- **Containerization**: Docker & Docker Compose

## 📁 Architecture

The codebase follows a strictly modular separation of concerns:
```text
BidBazaar/
│
├── config.py                  # Global Configuration Loader
├── database.py                # Database Engine & Session Generator
├── .env                       # Secret Database & API Credentials (Git Ignored)
├── .gitignore                 # Excludes caches and environments from Git
├── requirements.txt           # Python Dependencies (UTF-8)
├── Dockerfile                 # Container Blueprint for the API
├── docker-compose.yml         # Container Orchestration (API + PostgreSQL)
│
├── models.py                  # SQLModel Database Entities (User, Item, Bid)
├── schema.py                  # Pydantic Schemas for Strict Input Validation
├── scheduler.py               # APScheduler Background Automation
├── security.py                # JWT & Password Cryptography
├── exceptions.py              # Global Exception Handlers
│
├── routes/                    # HTTP & WebSocket Endpoint Definitions
│   ├── auth.py
│   ├── items.py
│   ├── payment.py
│   └── websockets.py
│
├── services/                  # Core Business Logic & Database Transactions
│   ├── auth_services.py
│   ├── email_services.py
│   ├── items_services.py
│   ├── payment_services.py
│   └── websockets_services.py
│
└── tests/                     # Automated Test Suite (100% Coverage)
    ├── conftest.py            # Fixtures & Fake SQLite Setup
    ├── test_auth.py           # Registration & Login endpoints
    ├── test_database.py       # SQLModel engine behavior
    ├── test_email.py          # SMTP mock verifications
    ├── test_items.py          # Auction listing integrity
    ├── test_main.py           # Lifespan events
    ├── test_payment.py        # Stripe webhooks & token generation
    ├── test_scheduler.py      # Background APScheduler closures
    └── test_websockets.py     # Live bidding broadcasts
```

---

## 🔧 Installation & Setup

### 🐳 Quick Start (Using Docker - Recommended)
The fastest way to run this API without configuring your local machine.

1. Clone the repository
```bash
git clone <your-repo-url>
cd BidBazaar
```

2. Configure Environment
Create a `.env` file from the example:
```bash
cp .env.example .env
```
*(Fill in your `STRIPE_SECRET_KEY` and `SMTP_PASSWORD`)*

3. Run the application
```bash
docker-compose up --build
```
*Docker will provision a fresh PostgreSQL database, run migrations, and start the FastAPI server at `http://localhost:8000`.*

---

### 💻 Manual Setup (Without Docker)

**Prerequisites**
- Python 3.10+
- PostgreSQL installed and running locally
- Stripe CLI (for webhook testing)

**1. Clone and Create Virtual Environment**
```bash
git clone <your-repo-url>
cd BidBazaar
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

**2. Setup Database & Credentials**
Create a `.env` file and insert your PostgreSQL `DATABASE_URL`.
```bash
alembic upgrade head
```

**3. Run the Server**
```bash
uvicorn main:app --reload
```
*The API interactive docs will be available at `http://localhost:8000/docs`*

**4. Stripe Webhooks (Local Testing)**
In a separate terminal, use the Stripe CLI to forward events to your local server:
```bash
stripe listen --forward-to localhost:8000/payment/webhook
```

---

## 📋 API Endpoints

### Authentication & Users
| Method | Endpoint | Description |
|--------|----------|-------------|
| **POST** | `/auth/signup` | Register a new user account |
| **POST** | `/auth/login` | Authenticate user and receive JWT token |

### Auction Items
| Method | Endpoint | Description |
|--------|----------|-------------|
| **POST** | `/items/` | Create a new auction item listing |
| **GET** | `/items/` | Retrieve all active items (Supports `?search=` and `?sort_by=` filters) |
| **GET** | `/items/seller/{username}` | Retrieve items listed by a specific seller |

### Live Bidding
| Method | Endpoint | Description |
|--------|----------|-------------|
| **WS** | `/bids/{item_id}?token=` | Connect to the WebSocket room for an item to place live bids |

### Stripe Payments
| Method | Endpoint | Description |
|--------|----------|-------------|
| **POST** | `/payment/onboard` | Generate a Stripe Express onboarding link for sellers |
| **GET** | `/payment/checkout/{item_id}?token=` | Validate secure token and redirect to Stripe Checkout |
| **POST** | `/payment/webhook` | Listen for Stripe asynchronous events |
| **POST** | `/payment/refund/{item_id}` | Initiate an automated refund for a purchased item |

---

## 📊 Error Handling

The API employs standardized JSON exception handling to prevent server crashes:
- **`400 Bad Request`**: Validation errors, business logic violations, or invalid Stripe signatures.
- **`401 Unauthorized`**: Expired/invalid JWT or wrong password.
- **`403 Forbidden`**: Invalid or expired one-time checkout links.
- **`404 Not Found`**: The requested item does not exist.
- **`422 Unprocessable Entity`**: Payload format is incorrect.

---

## 👨‍💻 About This Project

### Key Learnings
- **Strict Typing:** Transitioning a rapid prototype to an enterprise-grade API by implementing rigorous Google-style docstrings and type hinting across 100% of the codebase.
- **Database Dependency Injection:** Implementing `get_session()` dependency overrides in `pytest` to force the test suite to use an in-memory `SQLite` database while production uses `PostgreSQL`.
- **Payment Lifecycle Security:** Securing the checkout flow by minting URL-safe cryptographic tokens when an auction ends, ensuring malicious actors cannot manually navigate to a checkout page.
- **Asynchronous Webhooks:** Designing robust webhook handlers to securely ingest and verify Stripe crypto-signatures for backend processing.

## 📄 License
MIT License - feel free to use for learning purposes.

## 🔗 Connect With Me

**Author**: Riya Chaleria  
**LinkedIn**: [Riya Chaleria](https://www.linkedin.com/in/riya-chaleria-1b8712248/)  
**Email**: riyachaleria@gmail.com
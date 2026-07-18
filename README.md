# 🏷️ BidBazaar Live Auction API

A production-ready, high-performance RESTful API for a real-time auction platform. Built with FastAPI and PostgreSQL, this system handles secure live bidding, enterprise-grade multi-device authentication with sliding-window token rotation, automated Stripe checkout workflows, transactional Brevo OTP email verification, and scheduled background jobs to process expired auctions seamlessly.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-00a393.svg)
![SQLModel](https://img.shields.io/badge/SQLModel-Database-black.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-336791.svg)
![Stripe](https://img.shields.io/badge/Stripe-Payments-blueviolet.svg)
![Brevo](https://img.shields.io/badge/Brevo-Email%20API-0092FF.svg)
![Coverage](https://img.shields.io/badge/Test%20Coverage-100%25-brightgreen.svg)

---

## 🎯 Overview

BidBazaar is engineered to solve the complex concurrency, security, and synchronization problems inherent in live auction platforms. It serves as a robust, scalable backend enabling users to list items, securely bid in real-time without refreshing, and seamlessly transition into an automated checkout flow when they win.

Whether viewed by non-technical business stakeholders evaluating enterprise reliability or senior engineers reviewing architectural patterns, BidBazaar demonstrates how modern high-frequency web applications maintain zero-trust security while delivering instantaneous user experiences.

### Business Problem Solved
When facilitating peer-to-peer live auctions, platforms require an impenetrable, high-concurrency infrastructure to:
- **Handle High-Frequency Bidding:** Stream live, concurrent bids in real-time via WebSockets without data collisions or race conditions on item prices.
- **Guarantee Account & Session Security:** Protect user accounts against token theft using sliding-window JWT refresh token rotation, unique token IDs (`jti`), and multi-device session revocation.
- **Automate Password Recovery:** Provide self-service account recovery via secure 6-digit One-Time Password (OTP) verification delivered reliably through the Brevo Email API.
- **Manage Lifecycle Automation:** Autonomously detect when auctions expire, correctly identify winning bidders, and prune expired authentication artifacts from the database without human intervention.
- **Facilitate Split-Payments:** Ensure transaction integrity by capturing a 5% platform fee while routing 95% of funds directly to sellers via Stripe Connect Express.
- **Maintain Communication:** Automatically email buyers and sellers at every critical step of the transaction lifecycle (welcome emails, winning notifications, receipts, and refund alerts).

---

## 🚀 Features

- **⚡ Real-Time Bidding Engine:** WebSockets stream the highest bid live to all connected clients instantly, ensuring zero latency and eliminating stale price data.
- **🔐 Enterprise Authentication & Token Rotation:** Stateless JWT access tokens paired with stateful, sliding-window refresh tokens. Supports single-session logout (`/auth/logout`), universal multi-device sign-out (`/auth/logout-all`), and strict bcrypt password complexity hashing.
- **📩 Brevo OTP Password Recovery:** Integrated with the Brevo HTTP API to deliver secure, time-sensitive 6-digit verification codes (`/auth/forget-password`). Verified OTPs issue short-lived cryptographic authorization tokens (`/auth/verify-password`) required to finalize password resets (`/auth/reset-password`).
- **🕒 Background Task Automation:** Integrated `APScheduler` runs dedicated background jobs that natively scan for and close expired auctions, mint secure one-time Stripe checkout tokens, and automatically purge revoked or expired refresh tokens and OTP records (`clean_expired_auth_data`).
- **💳 Stripe Connect Express Integration:** End-to-end automated checkout capturing a 5% platform fee and transferring 95% of funds securely to the seller. Asynchronous webhooks automatically verify cryptographic signatures and finalize transactions.
- **💸 Refund Automation:** Seamless API integration allowing verified buyers to initiate full refunds, automatically reversing Stripe payment intents, updating database records, and notifying all stakeholders.
- **📧 Transactional SMTP & Brevo Emails:** Automated, beautifully styled HTML email notifications with clean text fallbacks for welcome messages, winning bids, payment receipts, and password resets.
- **🗄️ Strict Data Validation & ORM:** Backed by `PostgreSQL` and `SQLModel` (`SQLAlchemy`) with enforced foreign-key constraints, comprehensive table indexing, and strict `Pydantic` input sanitization.
- **🧪 100% Automated Test Coverage:** A comprehensive suite of 82 automated unit and integration tests spanning every route, service, utility, and scheduler job, verified without coverage shortcuts (`# pragma: no cover`).

---

## 🛠️ Tech Stack

- **Framework**: FastAPI (Python 3.10+)
- **Database**: PostgreSQL
- **ORM & Data Layer**: SQLModel / SQLAlchemy 2.0+
- **Payment Processing**: Stripe API & Webhooks
- **Email Delivery Engines**: Brevo API (HTTP REST) & Transactional SMTP (`httpx`, `smtplib`)
- **Job Scheduling**: APScheduler (`AsyncIOScheduler`)
- **Authentication & Security**: Python-JOSE (`JWT`), Passlib (`bcrypt`), UUIDv4 Token Tracking
- **Testing & Quality Assurance**: `pytest`, `pytest-cov`, `FastAPI TestClient`, `SQLite` In-Memory Fixtures
- **Environment Management**: `python-dotenv`
- **Containerization**: Docker & Docker Compose

---

## 📁 Architecture

The codebase strictly adheres to modular separation of concerns, dividing presentation routes, core business services, database models, and security layers:

```text
BidBazaar/
│
├── config.py                  # Global Configuration & Environment Variable Loader
├── database.py                # PostgreSQL Engine & Session Dependency Generator
├── exceptions.py              # Standardized Global & Request Validation Exception Handlers
├── scheduler.py               # APScheduler Background Jobs (Auction Closures & Auth Cleanup)
├── security.py                # JWT Cryptography, Token Revocation Checks & Password Hashing
├── models.py                  # SQLModel Database Entities (User, RefreshToken, OTP_Table, Item, Bid)
├── schema.py                  # Pydantic Schemas for Request Payload Sanitization
├── main.py                    # Application Entry Point, Lifespan Events & Router Registrations
│
├── .env.example               # Template of Required Environment Variables
├── .gitignore                 # Excludes Virtual Environments, Cache, and Secrets from Git
├── requirements.txt           # Complete UTF-8 Pinned Dependencies
├── Dockerfile                 # Multi-Stage Container Blueprint for the API Server
├── docker-compose.yml         # Container Orchestration (FastAPI Server + PostgreSQL Database)
├── alembic.ini                # Alembic Migration Configuration
│
├── alembic/                   # Database Migration Scripts & Metadata
│   ├── env.py                 # Dynamic Connection & SQLModel Metadata Binding
│   └── versions/              # Chronological Version Control for Database Schema Changes
│
├── routes/                    # HTTP & WebSocket API Endpoint Definitions
│   ├── auth.py                # Signup, Login, Refresh, Logout, Logout-All, & OTP Recovery Routes
│   ├── items.py               # Auction Listing Creation & Filtered Search Endpoints
│   ├── payment.py             # Stripe Onboarding, Checkout Links, Webhooks & Refunds
│   └── websockets.py          # Real-Time WebSocket Rooms for Live Item Bidding
│
├── services/                  # Core Business Logic & Database Transaction Isolation
│   ├── auth_services.py       # Authentication Workflow & Token State Management Logic
│   ├── auth_email_services.py # Brevo API Email Client for OTP Delivery
│   ├── email_services.py      # Transactional SMTP Notification Templates & Sending Logic
│   ├── items_services.py      # Item Creation, Queries & Seller Filters
│   ├── payment_services.py    # Stripe API Checkout & Webhook Processing
│   └── websockets_services.py # WebSocket Connection Manager & Broadcast Synchronization
│
└── tests/                     # Automated Test Suite (100% Statement Coverage)
    ├── conftest.py            # Fixtures & Isolated In-Memory SQLite Setup
    ├── test_auth.py           # Core Registration & Login Verification
    ├── test_advanced_auth.py  # Token Rotation, Multi-Device Logout & Brevo OTP Recovery Tests
    ├── test_database.py       # SQLModel Engine & Session Behavior
    ├── test_email.py          # SMTP & Mocked Brevo Email Verification
    ├── test_items.py          # Auction Listing Integrity & Query Filtering
    ├── test_main.py           # Lifespan Events & Exception Handler Verification
    ├── test_payment.py        # Stripe Webhook Crypto-Signature & Token Generation Tests
    ├── test_scheduler.py      # Background APScheduler Automated Closures & Pruning
    └── test_websockets.py     # Live Bidding Broadcasts & Concurrency Checks
```

---

## 🔧 Installation & Setup

### 🐳 Quick Start (Using Docker - Recommended)
The fastest and most reliable way to run the platform locally without installing PostgreSQL directly on your host machine.

1. **Clone the Repository**
```bash
git clone <your-repo-url>
cd BidBazaar
```

2. **Configure Environment Variables**
Copy the example configuration file and input your credentials:
```bash
cp .env.example .env
```
*(Ensure `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `SMTP_PASSWORD`, and `BREVO_API` are filled in)*

3. **Launch Container Suite**
```bash
docker-compose up --build
```
*Docker automatically provisions a dedicated PostgreSQL database (`db`), runs all Alembic migrations (`alembic upgrade head`), and starts the FastAPI server (`api`) at `http://localhost:8000`.*

---

### 💻 Manual Setup (Without Docker)

**Prerequisites**
- Python 3.10+
- PostgreSQL server installed and running locally
- Stripe CLI (for testing local payment webhooks)

**1. Clone and Create Virtual Environment**
```bash
git clone <your-repo-url>
cd BidBazaar
python -m venv venv
venv\Scripts\activate      # On Windows
# source venv/bin/activate # On macOS / Linux
pip install -r requirements.txt
```

**2. Setup Database & Credentials**
Create your `.env` file and configure your local PostgreSQL connection string:
```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/bidbazaar_db
```
Run database migrations to build all tables (`users`, `refresh_tokens`, `otp_codes`, `items`, `bids`):
```bash
alembic upgrade head
```

**3. Run the Development Server**
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
*Interactive Swagger API documentation will be immediately accessible at `http://localhost:8000/docs`.*

**4. Stripe Webhook Forwarding (Local Testing)**
In a separate terminal, use the Stripe CLI to forward events directly to your local application:
```bash
stripe listen --forward-to localhost:8000/payment/webhook
```

---

## 📋 API Endpoints

### 🔐 Authentication & Account Management (`/auth`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| **POST** | `/auth/signup` | Register a new user account with strict password complexity enforcement |
| **POST** | `/auth/login` | Authenticate with username/password to receive access and refresh tokens |
| **POST** | `/auth/refresh` | Exchange a valid sliding-window refresh token for a new access token |
| **POST** | `/auth/logout` | Revoke the provided refresh token (`is_revoked = True`) to end session |
| **POST** | `/auth/logout-all` | Universal sign-out: revokes all active refresh tokens across all user devices |
| **POST** | `/auth/forget-password` | Dispatch a time-sensitive 6-digit verification code to registered email via Brevo |
| **POST** | `/auth/verify-password` | Verify the 6-digit code and obtain a short-lived password reset authorization token |
| **POST** | `/auth/reset-password` | Finalize password change using the reset token and revoke all existing sessions |

### 🏷️ Auction Items (`/items`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| **POST** | `/items/` | Create a new auction item listing (requires valid JWT access token) |
| **GET** | `/items/` | Retrieve all active items (Supports `?search=` and `?sort_by=` query filters) |
| **GET** | `/items/seller/{username}` | Retrieve public listings published by a specific seller |

### ⚡ Live Real-Time Bidding (`/bids`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| **WS** | `/bids/{item_id}?token=` | Connect to the WebSocket room for a specific item to broadcast and receive live bids |

### 💳 Stripe Connect & Payments (`/payment`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| **POST** | `/payment/onboard` | Generate an automated Stripe Connect Express onboarding link for sellers |
| **GET** | `/payment/checkout/{item_id}?token=` | Validate one-time cryptographic token and redirect winning bidder to Stripe Checkout |
| **POST** | `/payment/webhook` | Asynchronous webhook ingest verifying Stripe crypto-signatures and settling item status |
| **POST** | `/payment/refund/{item_id}` | Initiate an automated refund reversing Stripe payment intents and notifying buyers |

---

## 📊 Error Handling

BidBazaar enforces uniform, standardized JSON error payloads (`{"error": true, "message": "...", "path": "..."}`) across all endpoints, ensuring seamless frontend integration without unhandled server stack traces:

- **`400 Bad Request`**: Business logic violations, duplicate registrations, invalid OTP verification codes, or malformed Stripe signatures.
- **`401 Unauthorized`**: Expired/invalid JWTs, incorrect credentials, revoked refresh tokens, or expired password reset tokens.
- **`403 Forbidden`**: Unauthorized item modifications or expired one-time checkout links.
- **`404 Not Found`**: The requested auction item, user profile, or resource does not exist.
- **`422 Unprocessable Entity`**: Request validation failures (e.g., missing required fields, password format non-compliance, invalid types).
- **`500 Internal Server Error`**: Standardized fallback catching unexpected server exceptions securely without leaking internal architecture.

---

## 👨‍💻 About This Project

### Key Learnings & Engineering Highlights
- **Enterprise Security Architecture:** Designing zero-trust authentication workflows where stateless JWT access tokens are protected by stateful database-tracked refresh tokens (`jti`), allowing instant session termination (`/auth/logout` and `/auth/logout-all`) while maintaining high performance.
- **Transactional API Integration:** Combining `httpx` asynchronous REST calls with Brevo API to guarantee high-deliverability 6-digit OTP delivery for self-service account recovery.
- **Automated Memory & DB Hygiene:** Using `APScheduler` background threads (`clean_expired_auth_data`) to prevent database bloat by continuously pruning expired OTP records and revoked tokens without impacting API request response times.
- **Strict Typing & Documentation:** Enforcing comprehensive Google-style docstrings and precise Python type hints across 100% of routes, services, schemas, and models.
- **Test-Driven Reliability:** Building an exhaustive, deterministic suite of 82 automated tests (`100% total statement coverage`) using `pytest` and `SQLModel` in-memory SQLite dependency injection, guaranteeing confidence in production deployments.

---

## 📄 License
MIT License - feel free to use and adapt this architecture for educational or commercial purposes.

## 🔗 Connect With Me

**Author**: Riya Chaleria  
**LinkedIn**: [Riya Chaleria](https://www.linkedin.com/in/riya-chaleria-1b8712248/)  
**Email**: riyachaleria@gmail.com
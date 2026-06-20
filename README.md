# 🏷️ BidBazaar API

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-00a393.svg)
![SQLModel](https://img.shields.io/badge/SQLModel-Database-black.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-336791.svg)
![pytest](https://img.shields.io/badge/Pytest-Testing-yellow.svg)

**BidBazaar** is a high-performance, real-time auction platform backend built with FastAPI. It supports live bidding via WebSockets, secure JWT authentication, automated background job scheduling for auction expirations, and transactional email notifications.

---

## ✨ Features

- **🔐 Secure Authentication:** JWT-based login and registration with bcrypt password hashing.
- **⚡ Real-Time Bidding:** Live WebSocket connections ensuring users see the highest bid updates instantly without refreshing.
- **🕒 Automated Auctions:** Integrated `APScheduler` background tasks automatically close expired auctions.
- **📧 Transactional Emails:** Automated SMTP email notifications for welcome messages, winning bids, and sold items (with plain-text and HTML fallbacks).
- **🗄️ Robust Database:** Powered by `SQLModel` and `PostgreSQL` (with seamless SQLite support for testing).
- **✅ Comprehensive Testing:** Heavily tested utilizing `pytest`, `TestClient`, and dependency injection overriding.

---

## 🏗️ Architecture & Directory Structure

```text
BidBazaar/
├── .env                  # Environment variables (not tracked by git)
├── config.py             # Global configuration loader
├── database.py           # Database engine & session management
├── exceptions.py         # Global and HTTP exception handlers
├── main.py               # FastAPI application entry point & lifespan events
├── models.py             # SQLModel database tables (User, Item, Bid)
├── schema.py             # Pydantic schemas for request validation
├── scheduler.py          # APScheduler background tasks
├── security.py           # JWT & password hashing utilities
│
├── routes/               # API Endpoints
│   ├── auth.py           # Registration & Login endpoints
│   ├── items.py          # Auction item creation & retrieval
│   └── websockets.py     # Real-time bidding connections
│
├── services/             # Core Business Logic
│   ├── auth_services.py  # User validation & DB inserts
│   ├── email_services.py # SMTP email sending logic
│   ├── items_services.py # Item CRUD operations
│   └── websockets_services.py # Active connection management
│
└── tests/                # Pytest Suite
    ├── conftest.py       # Fixtures & in-memory SQLite DB setup
    ├── test_auth.py
    ├── test_email.py
    ├── test_items.py
    ├── test_main.py
    ├── test_scheduler.py
    └── test_websockets.py
```

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10+
- PostgreSQL server (running locally or remote)

### 2. Installation
Clone the repository and install the dependencies in a virtual environment:

```bash
git clone <your-repo-url>
cd BidBazaar
python -m venv venv
venv\Scripts\activate  # On Windows
pip install -r requirements.txt
```

### 3. Environment Variables
Create a `.env` file in the root directory and configure the following variables:

```env
SECRET_KEY=your_super_secret_jwt_key
DATABASE_URL=postgresql://postgres:password@localhost:5432/bidbazaar_db
SMTP_EMAIL=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

### 4. Running the Application
Start the FastAPI server using Uvicorn:

```bash
uvicorn main:app --reload
```
The API documentation will be available at: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🧪 Running Tests

The test suite uses an isolated in-memory SQLite database to ensure tests are fast, repeatable, and do not affect your production database. It also automatically mocks outbound emails.

```bash
pytest
```

---

## 📋 API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| **POST** | `/auth/signup` | Register a new user account |
| **POST** | `/auth/login` | Authenticate user and receive JWT token |

### Auction Items
| Method | Endpoint | Description |
|--------|----------|-------------|
| **POST** | `/items/` | Create a new auction item listing |
| **GET** | `/items/` | Retrieve all items (Supports `?search=` and `?sort_by=` filters) |
| **GET** | `/items/seller/{username}` | Retrieve items listed by a specific seller |

### Real-time Bidding
| Method | Endpoint | Description |
|--------|----------|-------------|
| **WS** | `/bids/{item_id}?token=` | Establish a WebSocket connection for live bidding on an item |

---

## 📊 Error Handling

The API returns descriptive JSON errors with standardized HTTP status codes:
- **`400 Bad Request`**: Validation failures (e.g., "Username already exists", "Email already exists").
- **`401 Unauthorized`**: Missing, invalid, or expired JWT token, or incorrect login credentials.
- **`422 Unprocessable Entity`**: Invalid JSON payload.
- **`500 Internal Server Error`**: Unexpected database transaction failures or server crashes (handled cleanly via global exception handlers).

---

## 👨‍💻 About This Project

### Key Learnings & Implementations
- **Database Migrations:** Transitioning from an in-memory SQLite prototype to a robust PostgreSQL production database using SQLModel.
- **Separation of Concerns:** Abstracting business logic away from the routing layer into dedicated service modules (e.g., `auth_services.py`, `items_services.py`).
- **Automated Testing:** Implemented a robust automated testing pipeline using `pytest` and `TestClient` to act as a gatekeeper against regression bugs.
- **Real-Time Architectures:** Managing stateful, asynchronous WebSocket connections to handle high-frequency concurrent bidding.
- **Background Tasks:** Using `APScheduler` alongside FastAPI lifespan events to reliably close expired auctions and trigger events.

---

## 🤝 Contributing

This is a professional portfolio project, but suggestions are always welcome! Feel free to:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

---

## 📄 License

MIT License - feel free to use for learning purposes.

---

## 🔗 Connect With Me

**Author**: Riya Chaleria  
**LinkedIn**: [Riya Chaleria](https://www.linkedin.com/in/riya-chaleria-1b8712248/)  
**Email**: riyachaleria@gmail.com  

*Built with ❤️ by Riya Chaleria as an independent open-source project*

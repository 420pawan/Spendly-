# 💰 Spendly - Personal Expense Tracker

Spendly is a modern expense tracking web application built with **Flask** and **SQLite** that helps users manage their daily expenses, monitor spending habits, and gain insights through an intuitive dashboard.

---

## 🚀 Features

- 🔐 User Authentication
  - Secure Registration & Login
  - Password hashing using Werkzeug
  - Session-based authentication

- 💸 Expense Management
  - Add new expenses
  - Edit existing expenses
  - Delete expenses
  - Categorize expenses

- 📊 Dashboard & Analytics
  - Total expenses
  - Category-wise spending
  - Recent transactions
  - Spending summary

- 📅 Date Filtering
  - This Month
  - Last 3 Months
  - Last 6 Months
  - All Time
  - Custom Date Range

- 🎨 Responsive UI
  - Clean and modern interface
  - Mobile-friendly design
  - User-friendly navigation

---

## 🛠️ Tech Stack

### Backend
- Python
- Flask
- SQLite
- Werkzeug

### Frontend
- HTML5
- CSS3
- Jinja2 Templates

### Database
- SQLite

### Deployment
- Railway
- Gunicorn

---

## 📂 Project Structure

```
Spendly/
│
├── app.py
├── database/
│   ├── db.py
│   └── queries.py
│
├── templates/
│   ├── landing.html
│   ├── login.html
│   ├── register.html
│   ├── profile.html
│   ├── add_expense.html
│   └── edit_expense.html
│
├── static/
│   ├── css/
│   └── images/
│
├── requirements.txt
├── Procfile
└── README.md
```

---

## ⚙️ Installation

### 1. Clone the repository

```bash
git clone https://github.com/420pawan/Spendly-.git
cd Spendly-
```

### 2. Create a virtual environment

**Windows**

```bash
python -m venv venv
venv\Scripts\activate
```

**Linux / macOS**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set environment variable

**Windows**

```bash
set SECRET_KEY=your_secret_key
```

**Linux / macOS**

```bash
export SECRET_KEY=your_secret_key
```

### 5. Run the application

```bash
python app.py
```

Open your browser and visit:

```
[http://127.0.0.1:5001](https://spendly-production-1da2.up.railway.app/)
```

---

## ✨ Screens

- Landing Page
- Login & Registration
- User Dashboard
- Add Expense
- Edit Expense
- Expense Analytics
- Category Breakdown

---

## 🔒 Security Features

- Password hashing
- Parameterized SQL queries
- Session management
- Ownership validation for expenses
- Input validation

---

## 📈 Future Improvements

- Income tracking
- Budget planning
- Monthly reports
- Export to CSV/PDF
- Charts with Chart.js
- Email verification
- Password reset
- Dark mode

---

## 📌 Learning Outcomes

This project demonstrates:

- Flask Web Development
- Authentication & Authorization
- CRUD Operations
- SQLite Database Design
- Session Management
- Jinja2 Templates
- Responsive Frontend Development
- Railway Deployment
- Git & GitHub Workflow

---

## 👨‍💻 Author

**Pawan Kumar Mishra**

- GitHub: https://github.com/420pawan

---

## ⭐ If you found this project helpful, consider giving it a Star!

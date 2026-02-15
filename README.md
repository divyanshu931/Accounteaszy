
# 📊  Accounting & Ledger Management System

A fully functional Accounting & Ledger Management System built using **Django** with customized **Django Admin**, dynamic ledger calculations, and PDF export functionality.

This project demonstrates financial logic implementation, admin customization, and backend architecture design.

---

## ✨ Features

* 👤 Party Management (Customers / Vendors)
* 💳 Debit & Credit Transaction Recording
* 📒 Automatic Ledger Generation
* 📆 Date-wise Ledger Filtering
* 📊 Opening & Running Balance Calculation
* 🧮 Monthly Transaction Summary
* 📄 PDF Ledger Export (ReportLab)
* 🔐 Django Admin Custom Interface
* ⚡ Optimized ORM Queries using Aggregations

---

## 🛠 Tech Stack

| Technology          | Purpose          |
| ------------------- | ---------------- |
| Python              | Core Programming |
| Django              | Web Framework    |
| SQLite / PostgreSQL | Database         |
| ReportLab           | PDF Generation   |
| Django Admin        | UI & Management  |

---

## 🧠 Core Concepts Implemented

* Custom Django Admin Views
* Financial Ledger Logic (Debit/Credit system)
* Running Balance Calculation
* Date Range Filtering
* Django ORM Aggregation (`Sum`)
* Custom Admin URLs
* PDF Report Generation
* Template Overriding in Django Admin

---

## 📂 Project Structure

```
accounting_project/
│
├── accounting_app/
│   ├── models.py
│   ├── admin.py
│   ├── views.py
│   ├── templates/
│   │    └── admin/
│   │         └── ledger.html
│
├── manage.py
└── requirements.txt
```

---

## ⚙️ Setup Instructions

### 1️⃣ Clone Repository

```bash
git clone https://github.com/yourusername/django-accounting-app.git
cd django-accounting-app
```

### 2️⃣ Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
```

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 4️⃣ Apply Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5️⃣ Create Superuser

```bash
python manage.py createsuperuser
```

### 6️⃣ Run Server

```bash
python manage.py runserver
```

Access Admin Panel:

```
http://127.0.0.1:8000/admin/
```

---

## 📊 Ledger Calculation Logic

* Each Party has an Opening Balance.
* Debit → Increases Balance.
* Credit → Decreases Balance.
* Running Balance calculated dynamically.
* Date filtering recalculates opening before selected range.
* Closing Balance derived from transaction history.

---

## 📄 PDF Report

The system generates structured ledger statements including:

* Party Information
* Opening Balance
* Transaction Table
* Running Balance
* Closing Balance

---

## 📌 Future Enhancements

* Role-Based Access Control (RBAC)
* GST / Tax Module
* Invoice Management
* Excel Export
* Dashboard Analytics
* Multi-Company Support
* REST API Integration

---

## 👨‍💻 Author

**Divyanshu Tomar**
Backend Developer | Django | REST APIs | System Design

---

If you want, I can also give:

* 🔥 A minimal clean README
* 💼 Resume-focused project description (for recruiters)
* 🏢 Production-grade SaaS style README
* 📷 Version with screenshot section
* 📦 Requirements.txt template

Tell me what level you want 🚀

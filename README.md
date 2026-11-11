# SmartSpend – Personal Finance Management System

SmartSpend is a personal finance management web application designed to help users track their income, manage expenses, set monthly budgets, and monitor savings goals.

The application provides a simple dashboard and financial analytics to help users understand their spending habits and manage their money more effectively.

## Features

- **User Authentication:** Secure registration, login, logout, and account management.
- **Dashboard:** View financial summaries and recent transactions.
- **Transaction Management:** Add, edit, delete, and track income and expenses.
- **Budget Management:** Set monthly budgets and monitor spending.
- **Savings Goals:** Set monthly savings targets and track progress.
- **Financial Analytics:** Visualize income, expenses, and category-wise spending.
- **Monthly Filtering:** View financial reports for selected months.
- **Database Management:** Store and manage financial records using SQLite.

## Technologies Used

- **Backend:** Python, Flask
- **Database:** SQLite, SQL
- **Frontend:** HTML, CSS, JavaScript
- **Data Visualization:** Chart.js
- **Other Tools:** Git, GitHub

## Project Structure

```text
smartspend/
│
├── app.py
├── init_db.py
├── requirements.txt
│
├── database/
│   ├── db.py
│   └── models.py
│
├── pages/
│
├── templates/
│
├── static/
│   ├── css/
│   └── js/
│
├── utils/
│
└── README.md
```

## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/Kauraamrit/smartspend.git
```

### 2. Navigate to the project directory

```bash
cd smartspend
```

### 3. Create a virtual environment

```bash
python -m venv venv
```

### 4. Activate the virtual environment

**Windows:**

```bash
venv\Scripts\activate
```

### 5. Install dependencies

```bash
pip install -r requirements.txt
```

### 6. Configure the secret key

Set a secure environment variable before running the application.

**PowerShell:**

```powershell
$env:SECRET_KEY="your-generated-secret-key"
```

### 7. Initialize the database

```bash
python init_db.py
```

### 8. Run the application

```bash
python app.py
```

Open the local URL displayed in your terminal to access SmartSpend.

## Project Objective

The main objective of SmartSpend is to make personal financial management easier through a centralized platform for tracking transactions, managing budgets, monitoring savings, and analyzing financial activities.

## Future Enhancements

- Export financial reports.
- Advanced spending insights.
- Improved financial visualization.
- Recurring transaction management.

## Author

**Amrit Kaur**

B.Tech – Artificial Intelligence and Data Science

GitHub: [Kauraamrit](https://github.com/Kauraamrit)

---

⭐ If you find this project interesting, consider giving the repository a star!
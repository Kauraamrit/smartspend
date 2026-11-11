from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import sqlite3
import os

app = Flask(__name__)

# --------------------------------------------------
# FLASK CONFIGURATION
# --------------------------------------------------

app.secret_key = "smartspend-secret-key-change-later"

# Database location
DATABASE = os.path.join(
    os.path.dirname(__file__),
    "smartspend.db"
)


# --------------------------------------------------
# DATABASE CONNECTION
# --------------------------------------------------

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# --------------------------------------------------
# LOGIN CHECK
# --------------------------------------------------

def is_logged_in():
    return "user_id" in session


# --------------------------------------------------
# HOME
# --------------------------------------------------

@app.route("/")
def home():

    if is_logged_in():
        return redirect(url_for("dashboard"))

    return redirect(url_for("login"))


# --------------------------------------------------
# LOGIN
# --------------------------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        # Basic validation
        if not email or not password:

            flash(
                "Please enter your email and password.",
                "error"
            )

            return render_template("login.html")

        conn = get_db()

        user = conn.execute(
            """
            SELECT *
            FROM users
            WHERE email = ?
            """,
            (email,)
        ).fetchone()

        conn.close()

        # Check user and password
        if user and check_password_hash(
            user["password_hash"],
            password
        ):

            # Store login information
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["user_email"] = user["email"]


            return redirect(url_for("dashboard"))

        else:

            flash(
                "Invalid email or password.",
                "error"
            )

    return render_template("login.html")


# --------------------------------------------------
# REGISTER
# --------------------------------------------------

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get(
            "confirm_password",
            ""
        )

        # Check empty fields
        if not name or not email or not password:

            flash(
                "Please fill in all fields.",
                "error"
            )

            return render_template("register.html")

        # Check password confirmation
        if password != confirm_password:

            flash(
                "Passwords do not match.",
                "error"
            )

            return render_template("register.html")

        # Check password length
        if len(password) < 8:

            flash(
                "Password must contain at least 8 characters.",
                "error"
            )

            return render_template("register.html")

        conn = get_db()

        # Check if email already exists
        existing_user = conn.execute(
            """
            SELECT id
            FROM users
            WHERE email = ?
            """,
            (email,)
        ).fetchone()

        if existing_user:

            conn.close()

            flash(
                "An account with this email already exists.",
                "error"
            )

            return render_template("register.html")

        # Hash password
        password_hash = generate_password_hash(password)

        # Insert user
        conn.execute(
            """
            INSERT INTO users
            (name, email, password_hash)
            VALUES (?, ?, ?)
            """,
            (
                name,
                email,
                password_hash
            )
        )

        conn.commit()
        conn.close()

        flash(
            "Account created successfully! You can now log in.",
            "success"
        )

        return redirect(url_for("login"))

    return render_template("register.html")


# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------

@app.route("/dashboard")
def dashboard():

    # Check login
    if not is_logged_in():
        return redirect(url_for("login"))

    conn = get_db()

    # -----------------------------
    # CURRENT MONTH
    # -----------------------------

    current_month = datetime.now().month
    current_year = datetime.now().year
    current_month_name = datetime.now().strftime("%B")


    # -----------------------------
    # RECENT TRANSACTIONS
    # -----------------------------

    transactions = conn.execute(
        """
        SELECT
            *,
            strftime('%d', transaction_date) AS day,
            strftime('%m', transaction_date) AS month,
            strftime('%Y', transaction_date) AS year
        FROM transactions
        WHERE user_id = ?
        AND strftime('%m', transaction_date) = ?
        AND strftime('%Y', transaction_date) = ?
        ORDER BY transaction_date DESC
        LIMIT 5
        """,
        (
            session["user_id"],
            f"{current_month:02d}",
            str(current_year)
        )
    ).fetchall()


    # -----------------------------
    # MONTHLY BUDGET
    # -----------------------------

    budget_row = conn.execute(
        """
        SELECT amount
        FROM budgets
        WHERE user_id = ?
        AND month = ?
        AND year = ?
        """,
        (
            session["user_id"],
            current_month,
            current_year
        )
    ).fetchone()


    # -----------------------------
    # MONTHLY SPENDING
    # -----------------------------

    spent_row = conn.execute(
        """
        SELECT COALESCE(SUM(amount), 0) AS total
        FROM transactions
        WHERE user_id = ?
        AND transaction_type = 'expense'
        AND strftime('%m', transaction_date) = ?
        AND strftime('%Y', transaction_date) = ?
        """,
        (
            session["user_id"],
            f"{current_month:02d}",
            str(current_year)
        )
    ).fetchone()
    # -----------------------------
    # FINANCIAL SUMMARY
    # -----------------------------

    income_row = conn.execute(
        """
        SELECT COALESCE(SUM(amount), 0) AS total
        FROM transactions
        WHERE user_id = ?
        AND transaction_type = 'income'
        """,
        (session["user_id"],)
    ).fetchone()


    expense_row = conn.execute(
        """
        SELECT COALESCE(SUM(amount), 0) AS total
        FROM transactions
        WHERE user_id = ?
        AND transaction_type = 'expense'
        """,
        (session["user_id"],)
    ).fetchone()


    total_income = float(income_row["total"])

    total_expenses = float(expense_row["total"])

    total_balance = total_income - total_expenses


    # Get the current month's savings goal
    savings_goal_row = conn.execute(
        """
        SELECT amount
        FROM monthly_savings_goals
        WHERE user_id = ?
          AND month = ?
          AND year = ?
        """,
        (
            session["user_id"],
            current_month,
            current_year
        )
    ).fetchone()

    savings_goal = (
        float(savings_goal_row["amount"])
        if savings_goal_row
        else 0
    )


    conn.close()


    # -----------------------------
    # CALCULATE BUDGET VALUES
    # -----------------------------

    monthly_budget = (
        float(budget_row["amount"])
        if budget_row
        else 0
    )

    total_spent = float(spent_row["total"])

    remaining = monthly_budget - total_spent

    if monthly_budget > 0:

        percentage_used = (
            total_spent / monthly_budget
        ) * 100

    else:

        percentage_used = 0


    return render_template(
        "dashboard.html",
        transactions=transactions,
        monthly_budget=monthly_budget,
        total_spent=total_spent,
        remaining=remaining,
        percentage_used=percentage_used,
        current_month_name=current_month_name,
        current_year=current_year,
        total_balance=total_balance,
        total_income=total_income,
        total_expenses=total_expenses,
        savings_goal=savings_goal
    )
# --------------------------------------------------
# TRANSACTIONS
# --------------------------------------------------

@app.route("/transactions")
def transactions():

    # Check login
    if not is_logged_in():
        return redirect(url_for("login"))

    conn = get_db()

    transactions = conn.execute(
        """
        SELECT *
        FROM transactions
        WHERE user_id = ?
        ORDER BY transaction_date DESC
        LIMIT 5
        """,
        (session["user_id"],)
    ).fetchall()

    conn.close()

    return render_template(
        "transaction.html",
        transactions=transactions
    )
# --------------------------------------------------
# ADD TRANSACTION
# --------------------------------------------------

@app.route("/add-transaction", methods=["GET", "POST"])
def add_transaction():

    if not is_logged_in():
        return redirect(url_for("login"))

    if request.method == "POST":

        transaction_type = request.form.get(
            "transaction_type",
            ""
        )

        amount = request.form.get(
            "amount",
            ""
        )

        category = request.form.get(
            "category",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        transaction_date = request.form.get(
            "transaction_date",
            ""
        )

        # -----------------------------
        # VALIDATION
        # -----------------------------

        if not transaction_type or not amount or not category or not transaction_date:

            flash(
                "Please fill in all required fields.",
                "error"
            )

            return render_template(
                "add_transaction.html"
            )

        try:
            amount = float(amount)
            print("DEBUG - FORM AMOUNT:", request.form.get("amount"))
            print("DEBUG - CONVERTED AMOUNT:", amount)

            if amount <= 0:
                raise ValueError

        except ValueError:

            flash(
                "Please enter a valid amount.",
                "error"
            )

            return render_template(
                "add_transaction.html"
            )

        if transaction_type not in ["income", "expense"]:

            flash(
                "Invalid transaction type.",
                "error"
            )

            return render_template(
                "add_transaction.html"
            )

        # -----------------------------
        # SAVE TRANSACTION
        # -----------------------------

        conn = get_db()

        conn.execute(
            """
            INSERT INTO transactions
            (
                user_id,
                amount,
                transaction_type,
                category,
                description,
                transaction_date
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                session["user_id"],
                amount,
                transaction_type,
                category,
                description,
                transaction_date
            )
        )

        conn.commit()
        conn.close()

        flash(
            "Transaction added successfully!",
            "success"
        )

        return redirect(
            url_for("transactions")
        )

    return render_template(
        "add_transaction.html"
    )
# --------------------------------------------------
# EDIT TRANSACTION
# --------------------------------------------------

@app.route("/edit-transaction/<int:transaction_id>", methods=["GET", "POST"])
def edit_transaction(transaction_id):

    if not is_logged_in():
        return redirect(url_for("login"))

    conn = get_db()

    # Get the transaction belonging to the logged-in user
    transaction = conn.execute(
        """
        SELECT *
        FROM transactions
        WHERE id = ? AND user_id = ?
        """,
        (
            transaction_id,
            session["user_id"]
        )
    ).fetchone()

    # Transaction doesn't exist
    if transaction is None:

        conn.close()

        flash(
            "Transaction not found.",
            "error"
        )

        return redirect(
            url_for("transactions")
        )

    # --------------------------------------------------
    # UPDATE TRANSACTION
    # --------------------------------------------------

    if request.method == "POST":

        transaction_type = request.form.get(
            "transaction_type",
            ""
        )

        amount = request.form.get(
            "amount",
            ""
        )

        category = request.form.get(
            "category",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        transaction_date = request.form.get(
            "transaction_date",
            ""
        )

        # --------------------------------------------------
        # VALIDATION
        # --------------------------------------------------

        if (
            not transaction_type
            or not amount
            or not category
            or not transaction_date
        ):

            flash(
                "Please fill in all required fields.",
                "error"
            )

            conn.close()

            return render_template(
                "edit_transaction.html",
                transaction=transaction
            )

        try:

            amount = float(amount)

            if amount <= 0:
                raise ValueError

        except ValueError:

            flash(
                "Please enter a valid amount.",
                "error"
            )

            conn.close()

            return render_template(
                "edit_transaction.html",
                transaction=transaction
            )

        if transaction_type not in ["income", "expense"]:

            flash(
                "Invalid transaction type.",
                "error"
            )

            conn.close()

            return render_template(
                "edit_transaction.html",
                transaction=transaction
            )

        # --------------------------------------------------
        # UPDATE DATABASE
        # --------------------------------------------------

        conn.execute(
            """
            UPDATE transactions
            SET
                amount = ?,
                transaction_type = ?,
                category = ?,
                description = ?,
                transaction_date = ?
            WHERE id = ?
            AND user_id = ?
            """,
            (
                amount,
                transaction_type,
                category,
                description,
                transaction_date,
                transaction_id,
                session["user_id"]
            )
        )

        conn.commit()
        conn.close()

        flash(
            "Transaction updated successfully!",
            "success"
        )

        return redirect(
            url_for("transactions")
        )

    # --------------------------------------------------
    # GET REQUEST
    # Show edit form
    # --------------------------------------------------

    conn.close()

    return render_template(
        "edit_transaction.html",
        transaction=transaction
    )

# --------------------------------------------------
# DELETE TRANSACTION
# --------------------------------------------------

@app.route("/delete-transaction/<int:transaction_id>", methods=["POST"])
def delete_transaction(transaction_id):

    if not is_logged_in():
        return redirect(url_for("login"))

    conn = get_db()

    transaction = conn.execute(
        """
        SELECT id
        FROM transactions
        WHERE id = ? AND user_id = ?
        """,
        (
            transaction_id,
            session["user_id"]
        )
    ).fetchone()

    if transaction is None:

        conn.close()

        flash(
            "Transaction not found.",
            "error"
        )

        return redirect(
            url_for("transactions")
        )

    conn.execute(
        """
        DELETE FROM transactions
        WHERE id = ? AND user_id = ?
        """,
        (
            transaction_id,
            session["user_id"]
        )
    )

    conn.commit()
    conn.close()

    flash(
        "Transaction deleted successfully!",
        "success"
    )

    return redirect(
        url_for("transactions")
    )

    # ----------------------------------------------
    # UPDATE TRANSACTION
    # ----------------------------------------------

    if request.method == "POST":

        transaction_type = request.form.get(
            "transaction_type",
            ""
        )

        amount = request.form.get(
            "amount",
            ""
        )

        category = request.form.get(
            "category",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        transaction_date = request.form.get(
            "transaction_date",
            ""
        )

        # ------------------------------------------
        # VALIDATION
        # ------------------------------------------

        if not transaction_type or not amount or not category or not transaction_date:

            flash(
                "Please fill in all required fields.",
                "error"
            )

            conn.close()

            return render_template(
                "edit_transaction.html",
                transaction=transaction
            )

        try:

            amount = float(amount)

            if amount <= 0:
                raise ValueError

        except ValueError:

            flash(
                "Please enter a valid amount.",
                "error"
            )

            conn.close()

            return render_template(
                "edit_transaction.html",
                transaction=transaction
            )

        if transaction_type not in ["income", "expense"]:

            flash(
                "Invalid transaction type.",
                "error"
            )

            conn.close()

            return render_template(
                "edit_transaction.html",
                transaction=transaction
            )

        # ------------------------------------------
        # UPDATE DATABASE
        # ------------------------------------------

        conn.execute(
            """
            UPDATE transactions
            SET
                amount = ?,
                transaction_type = ?,
                category = ?,
                description = ?,
                transaction_date = ?
            WHERE id = ?
            AND user_id = ?
            """,
            (
                amount,
                transaction_type,
                category,
                description,
                transaction_date,
                transaction_id,
                session["user_id"]
            )
        )

        conn.commit()
        conn.close()

        flash(
            "Transaction updated successfully!",
            "success"
        )

        return redirect(
            url_for("transactions")
        )

    conn.close()

    return render_template(
        "edit_transaction.html",
        transaction=transaction
    )

# --------------------------------------------------
# ANALYTICS
# --------------------------------------------------

@app.route("/analytics")
def analytics():

    if not is_logged_in():
        return redirect(url_for("login"))

    conn = get_db()
    user_id = session["user_id"]

    # ----------------------------------------------
    # SELECT MONTH
    # ----------------------------------------------

    today = datetime.now()
    current_month = today.strftime("%Y-%m")

    selected_month = request.args.get(
        "month",
        current_month
    )

    # Validate the selected month
    try:
        selected_date = datetime.strptime(
            selected_month,
            "%Y-%m"
        )
        selected_month = selected_date.strftime("%Y-%m")

    except (ValueError, TypeError):
        selected_date = datetime.strptime(
            current_month,
            "%Y-%m"
        )
        selected_month = current_month

    month_number = selected_date.strftime("%m")
    year_number = selected_date.strftime("%Y")

    # Common parameters for month filtering
    date_params = (
        user_id,
        month_number,
        year_number
    )

    # ----------------------------------------------
    # TOTAL INCOME FOR SELECTED MONTH
    # ----------------------------------------------

    total_income = conn.execute(
        """
        SELECT COALESCE(SUM(amount), 0)
        FROM transactions
        WHERE user_id = ?
          AND transaction_type = 'income'
          AND strftime('%m', transaction_date) = ?
          AND strftime('%Y', transaction_date) = ?
        """,
        date_params
    ).fetchone()[0]

    total_income = float(total_income)

    # ----------------------------------------------
    # TOTAL EXPENSES FOR SELECTED MONTH
    # ----------------------------------------------

    total_expenses = conn.execute(
        """
        SELECT COALESCE(SUM(amount), 0)
        FROM transactions
        WHERE user_id = ?
          AND transaction_type = 'expense'
          AND strftime('%m', transaction_date) = ?
          AND strftime('%Y', transaction_date) = ?
        """,
        date_params
    ).fetchone()[0]

    total_expenses = float(total_expenses)

    # ----------------------------------------------
    # MONTHLY NET BALANCE
    # ----------------------------------------------

    balance = total_income - total_expenses

    # ----------------------------------------------
    # EXPENSES BY CATEGORY
    # ----------------------------------------------

    category_expenses_rows = conn.execute(
        """
        SELECT category, SUM(amount) AS total
        FROM transactions
        WHERE user_id = ?
          AND transaction_type = 'expense'
          AND strftime('%m', transaction_date) = ?
          AND strftime('%Y', transaction_date) = ?
        GROUP BY category
        ORDER BY total DESC
        """,
        date_params
    ).fetchall()

    category_expenses = [
        {
            "category": row["category"],
            "total": float(row["total"])
        }
        for row in category_expenses_rows
    ]

    # ----------------------------------------------
    # INCOME BY CATEGORY
    # ----------------------------------------------

    category_income_rows = conn.execute(
        """
        SELECT category, SUM(amount) AS total
        FROM transactions
        WHERE user_id = ?
          AND transaction_type = 'income'
          AND strftime('%m', transaction_date) = ?
          AND strftime('%Y', transaction_date) = ?
        GROUP BY category
        ORDER BY total DESC
        """,
        date_params
    ).fetchall()

    category_income = [
        {
            "category": row["category"],
            "total": float(row["total"])
        }
        for row in category_income_rows
    ]

    # ----------------------------------------------
    # TRANSACTION COUNT FOR SELECTED MONTH
    # ----------------------------------------------

    transaction_count = conn.execute(
        """
        SELECT COUNT(*)
        FROM transactions
        WHERE user_id = ?
          AND strftime('%m', transaction_date) = ?
          AND strftime('%Y', transaction_date) = ?
        """,
        date_params
    ).fetchone()[0]

    conn.close()

    # ----------------------------------------------
    # SEND DATA TO TEMPLATE
    # ----------------------------------------------

    return render_template(
        "analytics.html",
        total_income=total_income,
        total_expenses=total_expenses,
        balance=balance,
        category_expenses=category_expenses,
        category_income=category_income,
        transaction_count=transaction_count,
        selected_month=selected_month
    )

# --------------------------------------------------
# BUDGET
# --------------------------------------------------

@app.route("/budget", methods=["GET", "POST"])
def budget():

    if not is_logged_in():
        return redirect(url_for("login"))

    conn = get_db()

    # Current month and year
    current_month = datetime.now().month
    current_year = datetime.now().year

    if request.method == "POST":

        budget_amount = (
            request.form.get("budget")
            or request.form.get("amount")
            or ""
        )

        budget_amount = budget_amount.strip()

        if not budget_amount:

            flash(
                "Please enter a budget amount.",
                "error"
            )

            conn.close()
            return redirect(url_for("budget"))

        try:

            budget_amount = float(budget_amount)

        except ValueError:

            flash(
                "Please enter a valid budget amount.",
                "error"
            )

            conn.close()
            return redirect(url_for("budget"))

        if budget_amount <= 0:

            flash(
                "Budget must be greater than zero.",
                "error"
            )

            conn.close()
            return redirect(url_for("budget"))

        # Check if budget already exists
        existing_budget = conn.execute(
            """
            SELECT id
            FROM budgets
            WHERE user_id = ?
            AND month = ?
            AND year = ?
            """,
            (
                session["user_id"],
                current_month,
                current_year
            )
        ).fetchone()

        if existing_budget:

            conn.execute(
                """
                UPDATE budgets
                SET amount = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    budget_amount,
                    existing_budget["id"]
                )
            )

        else:

            conn.execute(
                """
                INSERT INTO budgets
                (user_id, amount, month, year)
                VALUES (?, ?, ?, ?)
                """,
                (
                    session["user_id"],
                    budget_amount,
                    current_month,
                    current_year
                )
            )

        conn.commit()

        conn.close()

        flash(
            "Monthly budget set successfully!",
            "success"
        )

        return redirect(url_for("budget"))

    # Get current month's budget
    budget_row = conn.execute(
        """
        SELECT amount
        FROM budgets
        WHERE user_id = ?
        AND month = ?
        AND year = ?
        """,
        (
            session["user_id"],
            current_month,
            current_year
        )
    ).fetchone()

    # Calculate spending for current month
    spent_row = conn.execute(
        """
        SELECT COALESCE(SUM(amount), 0) AS total
        FROM transactions
        WHERE user_id = ?
        AND transaction_type = 'expense'
        AND strftime('%m', transaction_date) = ?
        AND strftime('%Y', transaction_date) = ?
        """,
        (
            session["user_id"],
            f"{current_month:02d}",
            str(current_year)
        )
    ).fetchone()

    conn.close()

    monthly_budget = (
        float(budget_row["amount"])
        if budget_row
        else 0
    )

    total_spent = float(spent_row["total"])

    remaining = monthly_budget - total_spent

    if monthly_budget > 0:
        percentage_used = (
            total_spent / monthly_budget
        ) * 100
    else:
        percentage_used = 0

    return render_template(
        "budget.html",
        monthly_budget=monthly_budget,
        total_spent=total_spent,
        remaining=remaining,
        percentage_used=percentage_used,
        current_month=current_month,
        current_year=current_year
    )
# --------------------------------------------------
# SAVINGS GOAL
# --------------------------------------------------

@app.route("/savings-goal", methods=["GET", "POST"])
def savings_goal():

    if not is_logged_in():
        return redirect(url_for("login"))

    conn = get_db()
    user_id = session["user_id"]

    # Get the current month and year
    today = datetime.now()
    current_month = today.month
    current_year = today.year

    # Check whether this month already has a savings goal
    goal_row = conn.execute(
        """
        SELECT id, amount
        FROM monthly_savings_goals
        WHERE user_id = ? AND month = ? AND year = ?
        """,
        (user_id, current_month, current_year)
    ).fetchone()


    if request.method == "POST":

        target_input = request.form.get(
            "target_amount", ""
        ).strip()

        try:
            target_amount = float(target_input)
        except (ValueError, TypeError):
            flash("Please enter a valid savings target.", "error")
            conn.close()
            return redirect(url_for("savings_goal"))

        if not target_input or target_amount <= 0:
            flash(
                "Savings target must be greater than zero.",
                "error"
            )
            conn.close()
            return redirect(url_for("savings_goal"))

        if goal_row:
            conn.execute(
                """
                UPDATE monthly_savings_goals
                SET amount = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (target_amount, goal_row["id"])
            )
        else:
            conn.execute(
                """
                INSERT INTO monthly_savings_goals
                    (user_id, amount, month, year)
                VALUES (?, ?, ?, ?)
                """,
                (
                    user_id,
                    target_amount,
                    current_month,
                    current_year
                )
            )

        conn.commit()
        conn.close()

        flash(
            "Monthly savings goal updated successfully!",
            "success"
        )
        return redirect(url_for("savings_goal"))

    # Get this month's income
    income_row = conn.execute(
        """
        SELECT COALESCE(SUM(amount), 0) AS total
        FROM transactions
        WHERE user_id = ?
          AND transaction_type = 'income'
          AND strftime('%m', transaction_date) = ?
          AND strftime('%Y', transaction_date) = ?
        """,
        (
            user_id,
            f"{current_month:02d}",
            str(current_year)
        )
    ).fetchone()

    # Get this month's expenses
    expense_row = conn.execute(
        """
        SELECT COALESCE(SUM(amount), 0) AS total
        FROM transactions
        WHERE user_id = ?
          AND transaction_type = 'expense'
          AND strftime('%m', transaction_date) = ?
          AND strftime('%Y', transaction_date) = ?
        """,
        (
            user_id,
            f"{current_month:02d}",
            str(current_year)
        )
    ).fetchone()

    target_amount = (
        float(goal_row["amount"]) if goal_row else 0
    )

    # Monthly savings = this month's income - this month's expenses
    current_savings = (
        float(income_row["total"])
        - float(expense_row["total"])
    )

    progress_percentage = (
        min(max(current_savings / target_amount * 100, 0), 100)
        if target_amount > 0
        else 0
    )

    remaining_amount = max(
        target_amount - current_savings, 0
    )

    # Only congratulate the user on the final day of the month
    import calendar
    is_month_end = (
        today.day
        == calendar.monthrange(current_year, current_month)[1]
    )

    conn.close()

    return render_template(
        "savings_goal.html",
        target_amount=target_amount,
        current_savings=current_savings,
        progress_percentage=progress_percentage,
        remaining_amount=remaining_amount,
        current_month=current_month,
        current_year=current_year,
        is_month_end=is_month_end,
        month_name=today.strftime("%B"),
    )


# --------------------------------------------------
# ACCOUNT
# --------------------------------------------------

@app.route("/account")
def account():

    # Check login
    if not is_logged_in():
        return redirect(url_for("login"))

    conn = get_db()

    user = conn.execute(
        """
        SELECT id, name, email
        FROM users
        WHERE id = ?
        """,
        (session["user_id"],)
    ).fetchone()


    # ----------------------------------------------
    # TOTAL INCOME
    # ----------------------------------------------

    total_income = conn.execute(
        """
        SELECT COALESCE(SUM(amount), 0)
        FROM transactions
        WHERE user_id = ?
        AND transaction_type = 'income'
        """,
        (session["user_id"],)
    ).fetchone()[0]


    # ----------------------------------------------
    # TOTAL EXPENSES
    # ----------------------------------------------

    total_expenses = conn.execute(
        """
        SELECT COALESCE(SUM(amount), 0)
        FROM transactions
        WHERE user_id = ?
        AND transaction_type = 'expense'
        """,
        (session["user_id"],)
    ).fetchone()[0]


    # ----------------------------------------------
    # BALANCE
    # ----------------------------------------------

    balance = total_income - total_expenses


    # ----------------------------------------------
    # TRANSACTION COUNT
    # ----------------------------------------------

    transaction_count = conn.execute(
        """
        SELECT COUNT(*)
        FROM transactions
        WHERE user_id = ?
        """,
        (session["user_id"],)
    ).fetchone()[0]


    conn.close()


    return render_template(
        "account.html",

        user=user,

        total_income=total_income,

        total_expenses=total_expenses,

        balance=balance,

        transaction_count=transaction_count
    )


# --------------------------------------------------
# LOGOUT
# --------------------------------------------------

@app.route("/logout")
def logout():

    session.clear()

    flash(
        "You have been logged out.",
        "success"
    )

    return redirect(
        url_for("login")
    )

# --------------------------------------------------
# EDIT PROFILE
# --------------------------------------------------

@app.route("/edit-profile", methods=["GET", "POST"])
def edit_profile():

    # Check login
    if not is_logged_in():
        return redirect(url_for("login"))

    conn = get_db()

    # Get current user
    user = conn.execute(
        """
        SELECT id, name, email
        FROM users
        WHERE id = ?
        """,
        (session["user_id"],)
    ).fetchone()


    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()


        # ------------------------------------------
        # VALIDATION
        # ------------------------------------------

        if not name or not email:

            flash(
                "Name and email cannot be empty.",
                "error"
            )

            conn.close()

            return render_template(
                "edit_profile.html",
                user=user
            )


        # ------------------------------------------
        # CHECK EMAIL
        # ------------------------------------------

        existing_user = conn.execute(
            """
            SELECT id
            FROM users
            WHERE email = ?
            AND id != ?
            """,
            (
                email,
                session["user_id"]
            )
        ).fetchone()


        if existing_user:

            flash(
                "That email address is already in use.",
                "error"
            )

            conn.close()

            return render_template(
                "edit_profile.html",
                user=user
            )


        # ------------------------------------------
        # UPDATE USER
        # ------------------------------------------

        conn.execute(
            """
            UPDATE users
            SET name = ?, email = ?
            WHERE id = ?
            """,
            (
                name,
                email,
                session["user_id"]
            )
        )

        conn.commit()
        conn.close()


        flash(
            "Profile updated successfully!",
            "success"
        )

        return redirect(
            url_for("account")
        )


    conn.close()

    return render_template(
        "edit_profile.html",
        user=user
    )
# --------------------------------------------------
# CHANGE PASSWORD
# --------------------------------------------------

@app.route("/change-password", methods=["GET", "POST"])
def change_password():

    # Check login
    if not is_logged_in():
        return redirect(url_for("login"))


    if request.method == "POST":

        current_password = request.form.get(
            "current_password",
            ""
        )

        new_password = request.form.get(
            "new_password",
            ""
        )

        confirm_password = request.form.get(
            "confirm_password",
            ""
        )


        conn = get_db()


        # ------------------------------------------
        # GET CURRENT PASSWORD
        # ------------------------------------------

        user = conn.execute(
            """
            SELECT password_hash
            FROM users
            WHERE id = ?
            """,
            (session["user_id"],)
        ).fetchone()


        # ------------------------------------------
        # CHECK CURRENT PASSWORD
        # ------------------------------------------

        if not user or not check_password_hash(
            user["password_hash"],
            current_password
        ):

            conn.close()

            flash(
                "Your current password is incorrect.",
                "error"
            )

            return render_template(
                "change_password.html"
            )


        # ------------------------------------------
        # CHECK NEW PASSWORD LENGTH
        # ------------------------------------------

        if len(new_password) < 8:

            conn.close()

            flash(
                "New password must contain at least 8 characters.",
                "error"
            )

            return render_template(
                "change_password.html"
            )


        # ------------------------------------------
        # CONFIRM PASSWORD
        # ------------------------------------------

        if new_password != confirm_password:

            conn.close()

            flash(
                "New passwords do not match.",
                "error"
            )

            return render_template(
                "change_password.html"
            )


        # ------------------------------------------
        # HASH NEW PASSWORD
        # ------------------------------------------

        new_password_hash = generate_password_hash(
            new_password
        )


        # ------------------------------------------
        # UPDATE PASSWORD
        # ------------------------------------------

        conn.execute(
            """
            UPDATE users
            SET password_hash = ?
            WHERE id = ?
            """,
            (
                new_password_hash,
                session["user_id"]
            )
        )

        conn.commit()
        conn.close()


        flash(
            "Password changed successfully!",
            "success"
        )

        return redirect(
            url_for("account")
        )


    return render_template(
        "change_password.html"
    )
# --------------------------------------------------
# RUN APPLICATION
# --------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)
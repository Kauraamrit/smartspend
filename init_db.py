from database.db import engine, Base
from database.models import (
    User, 
    Transaction, 
    Budget, 
    SavingsGoal,
    MonthlySavingsGoal
)


# Create all database tables
Base.metadata.create_all(bind=engine)

print("SmartSpend database created successfully!")
print("Tables created:")
print("- users")
print("- transactions")
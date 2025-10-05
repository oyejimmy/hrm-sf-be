from app.database import SessionLocal, engine
from app.models.currency import Currency
from app.models import *

def init_currencies():
    db = SessionLocal()
    
    # Check if currencies already exist
    if db.query(Currency).count() > 0:
        print("Currencies already exist")
        db.close()
        return
    
    currencies = [
        {
            "country_name": "Pakistan",
            "currency_code": "PKR", 
            "currency_symbol": "₨",
            "currency_name": "Pakistani Rupee"
        },
        {
            "country_name": "United States",
            "currency_code": "USD",
            "currency_symbol": "$", 
            "currency_name": "US Dollar"
        },
        {
            "country_name": "United Kingdom",
            "currency_code": "GBP",
            "currency_symbol": "£",
            "currency_name": "British Pound"
        },
        {
            "country_name": "European Union", 
            "currency_code": "EUR",
            "currency_symbol": "€",
            "currency_name": "Euro"
        }
    ]
    
    for curr_data in currencies:
        currency = Currency(**curr_data)
        db.add(currency)
    
    db.commit()
    print("Currencies initialized successfully")
    db.close()

if __name__ == "__main__":
    init_currencies()
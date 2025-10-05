from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from ..database import Base

class Currency(Base):
    __tablename__ = "currencies"
    
    id = Column(Integer, primary_key=True, index=True)
    country_name = Column(String, nullable=False)
    currency_code = Column(String(3), nullable=False, unique=True)  # PKR, USD, EUR
    currency_symbol = Column(String(5), nullable=False)  # ₨, $, €
    currency_name = Column(String, nullable=False)  # Pakistani Rupee, US Dollar
    

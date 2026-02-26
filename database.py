from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

Base = declarative_base()

class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    url = Column(String, unique=True)
    custom_selector = Column(String, nullable=True) # Nouveau champ
    is_active = Column(Boolean, default=True)
    history = relationship("PriceHistory", back_populates="product")

class PriceHistory(Base):
    __tablename__ = 'price_history'
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'))
    price = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    in_stock = Column(Boolean)
    product = relationship("Product", back_populates="history")

class SystemState(Base):
    __tablename__ = 'system_state'
    id = Column(Integer, primary_key=True)
    last_update_requested = Column(DateTime, default=datetime.utcnow)

engine = create_engine('sqlite:///ecommerce_tracker.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

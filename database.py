from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
import streamlit as st
import os

Base = declarative_base()

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    url = Column(String, unique=True)
    custom_selector = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    history = relationship("PriceHistory", back_populates="product")

class PriceHistory(Base):
    __tablename__ = "price_history"
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    price = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    in_stock = Column(Boolean)
    product = relationship("Product", back_populates="history")

class SystemState(Base):
    __tablename__ = "system_state"
    id = Column(Integer, primary_key=True)
    last_update_requested = Column(DateTime, default=datetime.utcnow)

# ===== Connexion DB flexible (env var OU secrets) =====
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    db_conf = st.secrets["postgres"]  # section [postgres] dans secrets.toml
    DATABASE_URL = (
        f"postgresql+psycopg2://{db_conf['user']}:{db_conf['password']}"
        f"@{db_conf['host']}:{db_conf['port']}/{db_conf['dbname']}"
    )

engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

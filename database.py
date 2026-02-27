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

# ===== CONNEXION DB : 3 options prioritaires =====
URL = os.getenv("DATABASE_URL")  # 1. Variable d'environnement

if not URL and "postgres" in st.secrets:
    postgres_config = st.secrets["postgres"]
    if "url" in postgres_config:
        URL = postgres_config["url"]  # 2. secrets.toml avec URL complète
    elif all(key in postgres_config for key in ["user", "password", "host", "port", "dbname"]):
        URL = (
            f"postgresql+psycopg2://{postgres_config['user']}:{postgres_config['password']}"
            f"@{postgres_config['host']}:{postgres_config['port']}/{postgres_config['dbname']}?sslmode=require"
        )  # 3. secrets.toml avec config détaillée

# Fallback Supabase si rien d'autre
if not URL:
    url = "postgresql://neondb_owner:npg_pAOsiX75YqxT@ep-odd-dream-alwki9my-pooler.c-3.eu-central-1.aws.neon.tech/%22postgres%22?sslmode=require&channel_binding=require"


print(f"🔌 Using DB URL: {URL.split('@')[0]}@...")  # Debug partiel

engine = create_engine(URL, pool_pre_ping=True, pool_recycle=300)
try:
    Base.metadata.create_all(engine)
    print("✅ Tables créées / vérifiées")
except Exception as e:
    print(f"⚠️ Tables: {e}")

Session = sessionmaker(bind=engine)

from datetime import datetime
import streamlit as st
import pandas as pd
import plotly.express as px
from database import Session, Product, PriceHistory, SystemState
import time
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="EcoWatch Dashboard", layout="wide")
st_autorefresh(interval=30000, key="datarefresh")

# ✅ FONCTION load_data() CORRIGÉE
def load_data():
    session = Session()
    try:
        results = session.query(
            Product.name, 
            PriceHistory.price, 
            PriceHistory.timestamp, 
            PriceHistory.in_stock
        ).join(PriceHistory, Product.id == PriceHistory.product_id)\
         .order_by(PriceHistory.timestamp.asc()).all()
        
        data = [{'name': name, 'price': price, 'timestamp': timestamp, 'in_stock': in_stock}
                for name, price, timestamp, in_stock in results]
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Erreur chargement: {e}")
        return pd.DataFrame()
    finally:
        session.close()

df = load_data()  # ✅ Maintenant ça marche !

# Reste du code identique...
def trigger_worker_update():
    session = Session()
    try:
        session.query(SystemState).delete()
        new_state = SystemState(last_update_requested=datetime.utcnow())
        session.add(new_state)
        session.commit()
    except Exception as e:
        st.error(f"Erreur signal: {e}")
    finally:
        session.close()

def add_product(name, url):
    session = Session()
    try:
        clean_url = url.strip()
        if not clean_url.startswith(('http://', 'https://')):
            clean_url = 'https://' + clean_url
        
        existing = session.query(Product).filter(Product.url == clean_url).first()
        if existing:
            st.sidebar.warning("⚠️ Produit existe déjà !")
            return
        
        new_prod = Product(name=name, url=clean_url, is_active=True)
        session.add(new_prod)
        session.commit()
        trigger_worker_update()
        st.sidebar.success(f"✅ '{name}' enregistré !")
        time.sleep(0.5)
        st.rerun()
    except Exception as e:
        st.sidebar.error(f"❌ {e}")
    finally:
        session.close()

def delete_product(product_name):
    session = Session()
    try:
        prod = session.query(Product).filter(Product.name == product_name).first()
        if prod:
            session.query(PriceHistory).filter(PriceHistory.product_id == prod.id).delete()
            session.delete(prod)
            session.commit()
            st.sidebar.warning(f"🗑️ '{product_name}' supprimé")
            st.rerun()
    except Exception as e:
        st.sidebar.error(f"❌ {e}")
    finally:
        session.close()

# Interface (identique)
st.sidebar.header("➕ Ajouter un produit")
with st.sidebar.form("add_form", clear_on_submit=True):
    new_name = st.text_input("Nom du produit")
    new_url = st.text_input("URL de la page")
    if st.form_submit_button("Enregistrer"):
        if new_name and new_url:
            add_product(new_name, new_url)

if not df.empty:
    st.sidebar.markdown("---")
    st.sidebar.header("🗑️ Gérer les produits")
    list_to_manage = df['name'].unique()
    if len(list_to_manage) > 0:
        prod_to_del = st.sidebar.selectbox("Supprimer", list_to_manage)
        if st.sidebar.button("Supprimer définitivement"):
            delete_product(prod_to_del)

st.title("📈 EcoWatch : Intelligence de Prix")

# Status worker
session = Session()
state = session.query(SystemState).first()
if state and (datetime.utcnow() - state.last_update_requested).total_seconds() < 30:
    st.info("🔄 Worker scanne les prix...")
session.close()

if not df.empty:
    selected_product = st.sidebar.selectbox("Produit", df['name'].unique())
    filtered_df = df[df['name'] == selected_product]
    
    col1, col2, col3 = st.columns(3)
    current_price = filtered_df['price'].iloc[-1]
    if len(filtered_df) > 1:
        delta = round(current_price - filtered_df['price'].iloc[-2], 2)
        col1.metric("Prix", f"{current_price}€", f"{delta}€", delta_color="inverse")
    else:
        col1.metric("Prix", f"{current_price}€")
    
    col2.metric("Stock", "✅ Disponible" if filtered_df['in_stock'].iloc[-1] else "❌ Rupture")
    col3.metric("Relevés", len(filtered_df))
    
    st.subheader(f"Historique: {selected_product}")
    fig = px.line(filtered_df, x='timestamp', y='price', markers=True)
    st.plotly_chart(fig, use_container_width=True)
    
    with st.expander("Données brutes"):
        st.dataframe(filtered_df)
else:
    st.warning("👋 Ajoutez un produit !")


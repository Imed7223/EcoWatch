from datetime import datetime
import streamlit as st
import pandas as pd
import plotly.express as px
from database import Session, Product, PriceHistory, SystemState
import time
from streamlit_autorefresh import st_autorefresh

# 1. Configuration de la page
st.set_page_config(page_title="EcoWatch Dashboard", layout="wide")

# Actualise la page toutes les 30 secondes
st_autorefresh(interval=30000, key="datarefresh")

# --- FONCTION : CHARGEMENT DES DONNÉES (PostgreSQL) ---
def load_data():
    session = Session()
    try:
        # Requête SQLAlchemy équivalente à la version SQLite
        query = session.query(Product.name, PriceHistory.price, PriceHistory.timestamp, PriceHistory.in_stock)\
                      .join(PriceHistory, Product.id == PriceHistory.product_id)\
                      .order_by(PriceHistory.timestamp.asc()).all()
        
        # Conversion en DataFrame
        data = [{
            'name': p.name,
            'price': ph.price,
            'timestamp': ph.timestamp,
            'in_stock': ph.in_stock
        } for p, ph, _, _ in query]
        
        df = pd.DataFrame(data)
        return df
    except Exception as e:
        st.error(f"Erreur chargement données : {e}")
        return pd.DataFrame()
    finally:
        session.close()

# ⚠️ CHARGÉ AVANT TOUS LES if not df.empty !
df = load_data()

# --- SIGNAL POUR LE WORKER ---
def trigger_worker_update():
    session = Session()
    try:
        session.query(SystemState).delete() 
        new_state = SystemState(last_update_requested=datetime.utcnow())
        session.add(new_state)
        session.commit()
        print("🔔 Signal envoyé au Worker !")
    except Exception as e:
        st.error(f"Erreur de signal : {e}")
    finally:
        session.close()

# --- FONCTION : AJOUTER UN PRODUIT (PostgreSQL) ---
def add_product(name, url):
    session = Session()
    try:
        # Nettoyage URL
        clean_url = url.strip()
        if not clean_url.startswith(('http://', 'https://')):
            clean_url = 'https://' + clean_url
        
        # Vérifier si produit existe déjà
        existing = session.query(Product).filter(Product.url == clean_url).first()
        if existing:
            st.sidebar.warning("⚠️ Ce produit existe déjà !")
            return
        
        new_prod = Product(name=name, url=clean_url, is_active=True)
        session.add(new_prod)
        session.commit()
        
        trigger_worker_update()
        st.sidebar.success(f"✅ Produit '{name}' enregistré !")
        time.sleep(0.5)
        st.rerun()
    except Exception as e:
        st.sidebar.error(f"❌ Erreur : {e}")
    finally:
        session.close()

# --- FONCTION : SUPPRIMER UN PRODUIT (PostgreSQL) ---
def delete_product(product_name):
    session = Session()
    try:
        prod = session.query(Product).filter(Product.name == product_name).first()
        if prod:
            session.query(PriceHistory).filter(PriceHistory.product_id == prod.id).delete()
            session.delete(prod)
            session.commit()
            st.sidebar.warning(f"🗑️ '{product_name}' supprimé.")
            st.rerun()
    except Exception as e:
        st.sidebar.error(f"❌ Erreur suppression : {e}")
    finally:
        session.close()

# --- INTERFACE : BARRE LATÉRALE ---
st.sidebar.header("➕ Ajouter un produit")
with st.sidebar.form("add_form", clear_on_submit=True):
    new_name = st.text_input("Nom du produit")
    new_url = st.text_input("URL de la page")
    if st.form_submit_button("Enregistrer"):
        if new_name and new_url:
            add_product(new_name, new_url)

# Gestion suppression
if not df.empty:
    st.sidebar.markdown("---")
    st.sidebar.header("🗑️ Gérer les produits")
    list_to_manage = df['name'].unique()
    if len(list_to_manage) > 0:
        prod_to_del = st.sidebar.selectbox("Sélectionner pour supprimer", list_to_manage)
        if st.sidebar.button("Supprimer définitivement"):
            delete_product(prod_to_del)

st.sidebar.markdown("---")
st.sidebar.header("🔍 Options de filtrage")

# --- CONTENU PRINCIPAL ---
st.title("📈 EcoWatch : Intelligence de Prix")

# Indicateur de chargement
session = Session()
state = session.query(SystemState).first()
if state:
    diff = (datetime.utcnow() - state.last_update_requested).total_seconds()
    if diff < 30:
        st.info("🔄 Le Worker est en train de scanner les prix...")
session.close()

# Affichage des données
if not df.empty:
    selected_product = st.sidebar.selectbox("Produit à analyser", df['name'].unique())
    filtered_df = df[df['name'] == selected_product]

    if not filtered_df.empty:
        col1, col2, col3 = st.columns(3)
        current_price = filtered_df['price'].iloc[-1]
        
        if len(filtered_df) > 1:
            last_price = filtered_df['price'].iloc[-2]
            delta_val = round(current_price - last_price, 2)
            col1.metric("Prix Actuel", f"{current_price} €", delta=f"{delta_val} €", delta_color="inverse")
        else:
            col1.metric("Prix Actuel", f"{current_price} €", delta="Premier relevé")

        status_stock = "✅ En Stock" if filtered_df['in_stock'].iloc[-1] else "❌ Rupture"
        col2.metric("Disponibilité", status_stock)
        col3.metric("Suivis réalisés", len(filtered_df))
    
    # Graphique
    st.subheader(f"Historique des prix : {selected_product}")
    fig = px.line(filtered_df, x='timestamp', y='price', markers=True, line_shape="hv")
    st.plotly_chart(fig, width='stretch', use_container_width=True)

    with st.expander("Voir les données brutes"):
        st.dataframe(filtered_df.sort_values(by='timestamp', ascending=False))
else:
    st.warning("👋 Ajoutez un produit pour commencer le suivi.")

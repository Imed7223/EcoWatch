from datetime import datetime
import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from database import Session, Product, PriceHistory, SystemState
import time
from streamlit_autorefresh import st_autorefresh


# 1. Configuration de la page
st.set_page_config(page_title="EcoWatch Dashboard", layout="wide")

# Actualise la page toutes les 30 secondes pour voir les nouveaux prix
st_autorefresh(interval=30000, key="datarefresh")

# --- FONCTION : CHARGEMENT DES DONNÉES ---
def load_data():
    try:
        conn = sqlite3.connect('ecommerce_tracker.db')
        query = """
        SELECT p.name, ph.price, ph.timestamp, ph.in_stock 
        FROM price_history ph
        JOIN products p ON ph.product_id = p.id
        ORDER BY ph.timestamp ASC
        """
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception:
        return pd.DataFrame()

# --- SIGNAL POUR LE WORKER ---
def trigger_worker_update():
    session = Session()
    try:
        # On supprime l'ancien signal pour être sûr que le worker voit un changement
        session.query(SystemState).delete() 
        # On crée un signal tout neuf avec l'heure précise
        new_state = SystemState(last_update_requested=datetime.utcnow())
        session.add(new_state)
        session.commit()
        print("🔔 Signal envoyé au Worker !")
    except Exception as e:
        st.error(f"Erreur de signal : {e}")
    finally:
        session.close()

# --- FONCTION : AJOUTER UN PRODUIT ---
def add_product(name, url):
    session = Session()
    try:
        # --- NETTOYAGE AUTOMATIQUE DE L'URL ---
        clean_url = url.strip()
        if not clean_url.startswith(('http://', 'https://')):
            clean_url = 'https://' + clean_url
            
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

# --- FONCTION : SUPPRIMER UN PRODUIT ---
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

df = load_data()

if not df.empty:
    st.sidebar.markdown("---")
    st.sidebar.header("🗑️ Gérer les produits")
    list_to_manage = df['name'].unique()
    prod_to_del = st.sidebar.selectbox("Sélectionner pour supprimer", list_to_manage)
    if st.sidebar.button("Supprimer définitivement"):
        delete_product(prod_to_del)

st.sidebar.markdown("---")
st.sidebar.header("🔍 Options de filtrage")

# --- CONTENU PRINCIPAL ---
st.title("📈 EcoWatch : Intelligence de Prix")

# --- INDICATEUR DE CHARGEMENT (ASTUCE) ---
session = Session()
state = session.query(SystemState).first()
if state:
    # Si le dernier signal a moins de 30 secondes, on affiche un spinner
    diff = (datetime.utcnow() - state.last_update_requested).total_seconds()
    if diff < 30:
        st.info("🔄 Le Worker est en train de scanner les prix... Les données apparaîtront dans quelques instants.")
session.close()

if not df.empty:
    selected_product = st.sidebar.selectbox("Produit à analyser", df['name'].unique())
    filtered_df = df[df['name'] == selected_product]

    # --- Métriques ---
    if not filtered_df.empty:
        col1, col2, col3 = st.columns(3)
        current_price = filtered_df['price'].iloc[-1]
        
        # Calcul de la différence avec le prix précédent
        if len(filtered_df) > 1:
            last_price = filtered_df['price'].iloc[-2]
            delta_val = round(current_price - last_price, 2)
            # delta_color="inverse" : prix qui baisse = vert, prix qui monte = rouge
            col1.metric("Prix Actuel", f"{current_price} €", delta=f"{delta_val} €", delta_color="inverse")
        else:
            col1.metric("Prix Actuel", f"{current_price} €", delta="Premier relevé")

        status_stock = "✅ En Stock" if filtered_df['in_stock'].iloc[-1] else "❌ Rupture"
        col2.metric("Disponibilité", status_stock)
        col3.metric("Suivis réalisés", len(filtered_df))
    # --- Graphique ---
    st.subheader(f"Historique des prix : {selected_product}")
    fig = px.line(filtered_df, x='timestamp', y='price', markers=True, line_shape="hv")
    st.plotly_chart(fig, width='stretch')

    with st.expander("Voir les données brutes"):
        st.write(filtered_df.sort_values(by='timestamp', ascending=False))
else:
    st.warning("👋 Ajoutez un produit pour commencer le suivi.")

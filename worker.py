import time
import sys
from playwright.sync_api import sync_playwright
# Importation de SystemState ajoutée ici
from database import Session, Product, PriceHistory, SystemState 
from scraper_ecommerce import clean_price

def run_update_cycle():
    session = Session()
    try:
        # Récupération des produits actifs
        products = session.query(Product).filter(Product.is_active == True).all()
        
        if not products:
            print("Base vide : Aucun produit à scraper.")
            return

        with sync_playwright() as p:
            # Lancement du navigateur
            browser = p.chromium.launch(headless=True)
            for prod in products:
                try:
                    page = browser.new_page()
                    # User-Agent pour simuler un vrai navigateur
                    page.set_extra_http_headers({
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                    })
                    
                    print(f"Analyse en cours : {prod.name}...")
                    # On attend que le contenu soit chargé
                    page.goto(prod.url, wait_until="domcontentloaded", timeout=60000)
                    
                    # Pause de sécurité pour laisser le prix s'afficher (utile pour Amazon/Cdiscount)
                    time.sleep(2)

                    # Sélecteurs automatiques
                    sel = ".price, .a-price-whole, .current-price, .product-price, [data-price], .amount"
                    price_element = page.query_selector(sel)
                    
                    if price_element:
                        price_text = price_element.inner_text()
                        price_val = clean_price(price_text)
                    else:
                        print(f"⚠️ Prix non trouvé pour {prod.name}, valeur 0.0 par défaut.")
                        price_val = 0.0
                    
                    # Détection du stock
                    content = page.content()
                    in_stock = any(x in content for x in ["Ajouter au panier", "In stock", "En stock", "Disponible"])
                    
                    # Sauvegarde
                    new_history = PriceHistory(product_id=prod.id, price=price_val, in_stock=in_stock)
                    session.add(new_history)
                    print(f"✅ {prod.name} mis à jour : {price_val}€")
                    
                    page.close()
                except Exception as e:
                    print(f"❌ Erreur sur {prod.name} : {e}")
            
            session.commit()
            browser.close()
    except Exception as e:
        print(f"🔥 Erreur moteur : {e}")
    finally:
        session.close() # On ferme toujours la session pour libérer la base SQLite

def main_loop():
    print("🚀 Moteur EcoWatch en veille intelligente...")
    last_processed_signal = None 
    
    while True:
        session = Session()
        try:
            # On récupère le dernier signal envoyé par le Dashboard
            state = session.query(SystemState).first()
            current_signal = state.last_update_requested if state else None
            
            # Si un signal existe et qu'il est nouveau
            if current_signal is not None and current_signal != last_processed_signal:
                print(f"\n🔔 Signal détecté ! Lancement de la mise à jour...")
                run_update_cycle()
                last_processed_signal = current_signal
                print("--- Cycle terminé, retour en veille ---")
        except Exception as e:
            print(f"Erreur lecture signal : {e}")
        finally:
            session.close()
        
        time.sleep(5) # Vérification toutes les 5 secondes

if __name__ == "__main__":
    try:
        main_loop()
    except KeyboardInterrupt:
        print("\n🛑 Arrêt manuel du moteur.")

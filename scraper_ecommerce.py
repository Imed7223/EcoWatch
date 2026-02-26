import asyncio
from playwright.async_api import async_playwright

# --- ÉTAPE 1 : On place la fonction de nettoyage en haut ---
def clean_price(price_str):
    if not price_str or "Non trouvé" in price_str:
        return 0.0
    # On ne garde que les chiffres, les points et les virgules
    clean = "".join(filter(lambda x: x.isdigit() or x in ".,", price_str))
    # On remplace la virgule par un point pour le type float de Python
    clean = clean.replace(',', '.')
    try:
        return float(clean)
    except ValueError:
        return 0.0

async def get_product_data(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        await page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        })

        print(f"Analyse de : {url}...")
        try:
            await page.goto(url, wait_until="networkidle", timeout=60000)
            
            product_name = await page.title()
            
            # Extraction du texte du prix
            # On ajoute un maximum de sélecteurs communs rencontrés sur le web
            price_element = await page.query_selector(
                ".price, .a-price-whole, .current-price, .product-price, [data-price], .amount"
            )
            price_raw = await price_element.inner_text() if price_element else "Non trouvé"

            # --- ÉTAPE 2 : On utilise la fonction de nettoyage ici ---
            price_numeric = clean_price(price_raw)

            content = await page.content()
            in_stock = "Ajouter au panier" in content or "In stock" in content

            return {
                "nom": product_name,
                "prix": price_numeric, # Maintenant c'est un nombre (ex: 999.0)
                "disponible": in_stock
            }

        except Exception as e:
            return {"erreur": str(e)}
        finally:
            await browser.close()

async def main():
    # Test avec une URL réelle (ex: Amazon ou une boutique Shopify)
    test_url = "https://www.apple.com/fr/shop/buy-iphone/iphone-15" 
    resultat = await get_product_data(test_url)
    print("\n--- RÉSULTATS ---")
    print(resultat)

if __name__ == "__main__":
    asyncio.run(main())
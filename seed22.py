from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
# CORRECTION : On importe depuis 'database'
from database import Product, PriceHistory, Base, engine 

Session = sessionmaker(bind=engine)
session = Session()

# 1. Ajouter un produit
test_product = Product(name="iPhone 15 Pro", url="https://exemple.com/iphone")
session.add(test_product)
session.commit()

nouveau_produit = Product(
    name="iPhone 15 - Apple Store", 
    url="https://www.apple.com/fr/shop/buy-iphone/iphone-15",
    is_active=True
)

session.add(nouveau_produit)
session.commit()
session.close()
print("Produit ajouté avec succès !")

# 2. Ajouter un historique de prix
p1 = PriceHistory(product_id=test_product.id, price=999.0, in_stock=True)
p2 = PriceHistory(product_id=test_product.id, price=950.0, in_stock=True)
session.add_all([p1, p2])
session.commit()

print("Données de test insérées !")

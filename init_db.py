from sqlalchemy import create_engine
from database import Base # Importe la Base depuis ton fichier de modèles

# Créer le moteur (le même que dans ton dashboard)
engine = create_engine('sqlite:///ecommerce_tracker.db')

# Créer physiquement les tables dans le fichier .db
Base.metadata.create_all(engine)
print("Base de données initialisée et tables créées !")

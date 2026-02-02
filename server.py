import pandas as pd

# Charger les données
df = pd.read_excel("Dashboard_Securite.xlsx", sheet_name="Données")

# Nettoyage des noms de colonnes
df.columns = df.columns.str.strip()

# Renommer colonnes clés si besoin
df = df.rename(columns={
    "prix": "Prix"
})

# Conversion de la date
df["Date"] = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce")

# Affichage contrôle
print("Colonnes après nettoyage :")
print(df.columns.tolist())

print("\nTypes de données après conversion :")
print(df.dtypes)

print("\nAperçu des données nettoyées :")
print(df.head())

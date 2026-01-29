"""
Script de test pour vérifier que l'enrichissement des pays fonctionne
"""
import requests
import json

# URL de l'API
API_URL = "http://localhost:8000"

print("🔍 Test de l'enrichissement des pays\n")
print("=" * 60)

# 1. Test de santé
print("\n1️⃣ Test de santé du serveur...")
try:
    response = requests.get(f"{API_URL}/")
    print(f"✅ Serveur actif: {response.json()['message']}")
except Exception as e:
    print(f"❌ Erreur: {e}")
    exit(1)

# 2. Test de l'endpoint /transactions (nécessite authentification)
print("\n2️⃣ Test de l'endpoint /transactions...")
print("⚠️  Cet endpoint nécessite un token d'authentification")
print("   Pour tester, connectez-vous d'abord sur le frontend")
print("   et récupérez le token depuis les cookies")

# 3. Vérifier le schéma OpenAPI
print("\n3️⃣ Vérification du schéma OpenAPI...")
try:
    response = requests.get(f"{API_URL}/openapi.json")
    openapi = response.json()
    
    # Chercher le schéma TransactionResponseLite
    schemas = openapi.get("components", {}).get("schemas", {})
    if "TransactionResponseLite" in schemas:
        schema = schemas["TransactionResponseLite"]
        properties = schema.get("properties", {})
        
        print("✅ Schéma TransactionResponseLite trouvé")
        print("\n   Champs disponibles:")
        for field in properties.keys():
            print(f"      - {field}")
        
        # Vérifier les nouveaux champs
        new_fields = ["source_country", "destination_country", "recipient_email", "comment"]
        missing = [f for f in new_fields if f not in properties]
        
        if missing:
            print(f"\n   ❌ Champs manquants: {missing}")
            print("   ⚠️  Le serveur n'a peut-être pas redémarré")
        else:
            print(f"\n   ✅ Tous les nouveaux champs sont présents!")
    else:
        print("❌ Schéma TransactionResponseLite non trouvé")
        
except Exception as e:
    print(f"❌ Erreur: {e}")

print("\n" + "=" * 60)
print("\n💡 Instructions:")
print("   1. Si les champs sont manquants, redémarrez le serveur backend")
print("   2. Arrêtez le serveur (Ctrl+C dans le terminal backend)")
print("   3. Relancez: python -m uvicorn app.main:app --reload --port 8000")
print("   4. Rafraîchissez la page frontend (F5)")

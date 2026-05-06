import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from config import settings

print("=== Credenciales cargadas ===")
print(f"URI:      {settings.NEO4J_URI}")
print(f"USER:     {settings.NEO4J_USER}")
print(f"PASSWORD: {'*' * len(settings.NEO4J_PASSWORD)} (len={len(settings.NEO4J_PASSWORD)})")
print(f"DATABASE: {settings.NEO4J_DATABASE}")

if len(settings.NEO4J_PASSWORD) == 0:
    print("\n❌ PASSWORD ESTÁ VACÍO — el .env no se está leyendo")
    sys.exit(1)

print("\nIntentando conexión...")
from neo4j import GraphDatabase
try:
    driver = GraphDatabase.driver(settings.NEO4J_URI, auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD))
    driver.verify_connectivity()
    print("✅ Conexión exitosa!")
    driver.close()
except Exception as e:
    print(f"❌ Error: {e}")

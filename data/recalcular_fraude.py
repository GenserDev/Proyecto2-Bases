"""
Ejecuta el pipeline de detección de fraude después de load_csv.py.
Uso: python recalcular_fraude.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from services.fraud_engine import ejecutar_pipeline

print("=== Motor de Detección de Fraude ===\n")
resultados = ejecutar_pipeline()
for nombre, r in resultados.items():
    print(f"  [{nombre}]", r)
print("\n✅ Pipeline completado.")

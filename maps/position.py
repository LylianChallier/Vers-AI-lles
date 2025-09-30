import cv2
import numpy as np
import matplotlib.pyplot as plt
import json

# ============================
# 1. Charger le plan
# ============================
img = cv2.imread("plan_reconstruit.jpg")
h, w, _ = img.shape

# ============================
# 2. Associer POI -> pixels
# ============================
poi_positions = {
    # Château et abords immédiats (extension verticale : h/7)
    "Château": (w // 2, h - h // 14),  # Milieu vertical du château
    "Cour Royale": (w // 2, h - h // 7 + 10),
    "Galerie des Glaces": (w // 2, h - h // 7 + 20),
    "Chapelle Royale": (w // 2 + 20, h - h // 7 + 15),
    "Opéra Royal": (w // 2 + 40, h - h // 7 + 30),

    # Sud des jardins (proche du château)
    "Orangerie": (w // 2 - w // 4, h - h // 7 + 40),
    "Bassin du Miroir": (w // 2, h - h // 7 + 80),

    # Axes centraux (Fontaine de Latone et Bassin d’Apollon)
    "Fontaine de Latone": (w // 2, h - h // 7 - h // 10),
    "Bassin d’Apollon": (w // 2, h // 2),

    # Bosquets est (à droite de l'axe central)
    "Bosquet de la Colonnade": (w // 2 + w // 8, h // 2 + h // 20),
    "Bosquet des Bains d’Apollon": (w // 2 + w // 7, h // 2 + h // 15),
    "Bosquet du Théâtre d’Eau": (w // 2 + w // 6, h // 2 + h // 10),
    "Bassin de Neptune": (w // 2 + w // 5, h // 2 + h // 8),

    # Nord-est (près du Grand Canal)
    "Fontaine du Dragon": (w // 2 + w // 5, h // 2 + h // 6),
    "Grand Canal": (w // 2, h // 4),

    # Trianons (nord-est)
    "Bosquet de la Reine": (w // 2 + w // 4, h // 3 + h // 15),
    "Petit Trianon": (w - w // 3, h // 3),
    "Hameau de la Reine": (w - w // 3 + 30, h // 3 + 20),
    "Grand Trianon": (w - w // 3 - 40, h // 3 + 30),

    # Bosquets ouest (à gauche de l'axe central)
    "Bosquet de l’Étoile": (w // 2 - w // 5, h // 2 - h // 15),
    "Bosquet du Dauphin": (w // 2 - w // 4, h // 2 - h // 20),
    "Bosquet de l’Obélisque": (w // 2 - w // 6, h // 2 + h // 12),
    "Bosquet des Trois Fontaines": (w // 2 - w // 8, h // 2 + h // 9),
    "Fontaine de l’Encelade": (w // 2 - w // 6, h // 2 + h // 7),
    "Bassin de Flore": (w // 2 - w // 5, h // 2 + h // 10),
    "Salle de Bal": (w // 2 - w // 6, h // 2 - h // 10),
    "Bosquet des Dômes": (w // 2 - w // 8, h // 2 - h // 8),

    # Sud-ouest (proche de l'Orangerie)
    "Pièce d’eau des Suisses": (w // 2 - w // 5, h - h // 7 + 50),
    "Potager du Roi": (w // 5, h - h // 7 + 30),
}


# ============================
# 3. Références pixel <-> lat/lon
# ============================
pixel_points = np.array([
    [w//2, h - 200],       # Château
    [w//2, h//3],          # Grand Canal
    [w//2 + 200, h//2]     # Third reference point (example)
], dtype="float32")

geo_points = np.array([
    [48.804865, 2.120355],   # Château de Versailles
    [48.8085, 2.120355],     # Grand Canal
    [48.8065, 2.1210]        # Third reference point
], dtype="float32")

A, _ = cv2.estimateAffine2D(pixel_points, geo_points)

def pixel_to_geo(x, y):
    if A is None:
        raise ValueError("Affine transform could not be computed.")
    pt = np.array([[x, y, 1]], dtype="float32").T
    lat, lon = (A @ pt).flatten()
    return float(lat), float(lon)

# ============================
# 4. Charger l’itinéraire depuis input extérieur
# ============================
with open("itineraire.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Support both list of POIs or dict with "POIs"
if isinstance(data, list):
    itineraire = [poi["name"] for poi in data]
elif isinstance(data, dict) and "POIs" in data:
    itineraire = [poi["name"] for poi in data["POIs"]]
else:
    raise ValueError("JSON format not recognized")

# ============================
# 5. Tracer l’itinéraire
# ============================
plt.figure(figsize=(10, 14))
plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))

xs, ys = [], []
for name in itineraire:
    if name in poi_positions:
        x, y = poi_positions[name]
        xs.append(x)
        ys.append(y)
        plt.text(x + 5, y - 5, name, color="blue", fontsize=10)
    else:
        print(f"⚠️ POI '{name}' pas trouvé dans poi_positions")

plt.plot(xs, ys, color="red", linewidth=2, marker="o")
plt.title("Itinéraire importé")
plt.axis("off")
plt.tight_layout()

# Save figure if non-interactive environment
plt.savefig("itineraire_traced.png")
plt.close()  # Avoid UserWarning in non-interactive backends

# ============================
# 6. Export lat/lon des POIs visités
# ============================
print("\nPositions géographiques des POIs visités:")
for name in itineraire:
    if name in poi_positions:
        x, y = poi_positions[name]
        lat, lon = pixel_to_geo(x, y)
        print(f"{name}: pixel=({x},{y}), geo=({lat:.6f}, {lon:.6f})")

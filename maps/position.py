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
    # Château et abords immédiats
    "Château": (w // 2, h - (h // 3.5)),
    "Cour Royale": (w // 2, h - (h // 3.5) + 10),
    "Galerie des Glaces": (w // 2, h - (h // 3.5) + 20),
    "Chapelle Royale": (w // 2 + 40, h - (h // 3.5) + 10),
    "Opéra Royal": (w // 2 + 60, h - (h // 3.5) + 30),

    # Orangerie et bassins proches
    "Orangerie": (w // 2 - (w // 4), h - (h // 3.5) + 50),
    "Bassin du Miroir": (w // 2, h - (h // 3.5) + 100),

    # Fontaines et bassins principaux
    "Fontaine de Latone": (w // 2, h - (h // 3.5) - (h // 7)),
    "Bassin d’Apollon": (w // 2, h // 2),

    # Bosquets
    "Bosquet de la Colonnade": (w // 2 + (w // 8), h // 2 + 20),
    "Bosquet des Bains d’Apollon": (w // 2 - (w // 8), h // 2 + 20),
    "Bosquet du Théâtre d’Eau": (w // 2 + (w // 6), h // 2 + 60),
    "Bassin de Neptune": (w // 2 + (w // 6), h // 2 + 100),
    "Bassin de Flore": (w // 2 - (w // 6), h // 2 + 100),
    "Fontaine du Dragon": (w // 2 + (w // 7), h // 2 + 150),
    "Fontaine de l’Encelade": (w // 2 - (w // 7), h // 2 + 150),
    "Bosquet de l’Encélade": (w // 2 - (w // 6), h // 2 + 80),
    "Bosquet des Trois Fontaines": (w // 2, h // 2 + 120),
    "Bosquet de la Reine": (w // 2 + (w // 5), h // 2 - 50),
    "Bosquet de l’Étoile": (w // 2 - (w // 5), h // 2 - 50),
    "Bosquet du Dauphin": (w // 2 - (w // 4), h // 2 - 30),
    "Bosquet de l’Obélisque": (w // 2 - (w // 7), h // 2 + 120),
    "Salle de Bal": (w // 2 - (w // 6), h // 2 - 80),
    "Bosquet des Dômes": (w // 2 + (w // 10), h // 2 - 100),

    # Grands éléments des jardins
    "Grand Canal": (w // 2, h // 5),

    # Trianons
    "Petit Trianon": (w - (w // 3), h // 3),
    "Hameau de la Reine": (w - (w // 3) + 40, h // 3 + 30),
    "Grand Trianon": (w - (w // 3) - 50, h // 3 + 50),
    "Domaine de Marie-Antoinette": (w - (w // 3) + 60, h // 3 + 40),

    # Autres
    "Pièce d’eau des Suisses": (w // 2 + (w // 5), h - (h // 3.5) + 60),
    "Potager du Roi": (w // 5, h - (h // 3.5) + 40),
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

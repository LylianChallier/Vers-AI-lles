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
# ⚠️ Tu remplis ce dictionnaire une fois avec les bonnes coordonnées en pixels
poi_positions = {
    # Château et abords immédiats
    "Château": (w//2, h - 150),
    "Cour Royale": (w//2, h - 120),
    "Cour des Ministres": (w//2 - 100, h - 140),
    "Chapelle Royale": (w//2 + 120, h - 160),
    "Opéra Royal": (w//2 + 200, h - 180),
    "Galerie des Glaces": (w//2, h - 140),
    "Petit Trianon": (w//2 + 500, h - 300),
    "Hameau de la Reine": (w//2 + 600, h - 250),
    "Grand Trianon": (w//2 + 300, h - 400),

    # Jardins et bosquets
    "Fontaine de Latone": (w//2, h - 350),
    "Bosquet de la Reine": (w//2 + 400, h//2 - 100),
    "Bosquet du Dauphin": (w//2 - 400, h//2 - 100),
    "Bosquet de la Colonnade": (w//2 + 200, h//2 + 50),
    "Bosquet des Bains d’Apollon": (w//2 - 250, h//2 + 100),
    "Bosquet du Théâtre d’Eau": (w//2 + 350, h//2 + 150),
    "Bosquet de l’Étoile": (w//2 - 300, h//2 - 50),
    "Bosquet du Labyrinthe": (w//2 + 100, h//2 + 200),
    "Bosquet de l’Obélisque": (w//2 - 150, h//2 + 250),
    "Bosquet des Dômes": (w//2 + 150, h//2 - 200),
    "Bosquet de l’Encélade": (w//2 - 350, h//2 + 100),
    "Bosquet des Trois Fontaines": (w//2 + 50, h//2 + 180),
    "Salle de Bal": (w//2 - 200, h//2 - 150),

    # Fontaines et bassins
    "Bassin d’Apollon": (w//2, h//2),
    "Bassin de Neptune": (w//2 + 200, h//2 + 100),
    "Bassin de Flore": (w//2 - 200, h//2 + 100),
    "Fontaine du Dragon": (w//2 + 100, h//2 + 300),
    "Fontaine de l’Encelade": (w//2 - 100, h//2 + 300),
    "Fontaine de la Pyramide": (w//2, h//2 + 200),
    "Bassin du Miroir": (w//2, h - 250),
    "Bassin de Cérès": (w//2 + 300, h//2 + 50),
    "Bassin de Bacchus": (w//2 - 300, h//2 + 50),
    "Bassin de Saturne": (w//2 + 400, h//2 + 200),
    "Bassin de Vénus": (w//2 - 400, h//2 + 200),
    "Bassin de Mars": (w//2 + 500, h//2 + 150),
    "Bassin de Mercure": (w//2 - 500, h//2 + 150),

    # Grands éléments des jardins
    "Grand Canal": (w//2, h//3),
    "Orangerie": (w//2 - 300, h - 200),
    "Pièce d’eau des Suisses": (w//2 + 300, h - 200),

    # Autres éléments
    "Potager du Roi": (w//2 - 600, h - 100),
    "Domaine de Marie-Antoinette": (w//2 + 600, h - 200),
}

# ============================
# 3. Références pixel <-> lat/lon
# ============================
pixel_points = np.array([
    [w//2, h-200],   # Château
    [w//2, h//3]     # Grand Canal
], dtype="float32")

geo_points = np.array([
    [48.804865, 2.120355],   # Château de Versailles
    [48.8085, 2.120355]      # Grand Canal
], dtype="float32")

A, _ = cv2.estimateAffine2D(pixel_points, geo_points)

def pixel_to_geo(x, y):
    pt = np.array([[x, y, 1]], dtype="float32").T
    lat, lon = (A @ pt).flatten()
    return float(lat), float(lon)

# ============================
# 4. Charger l’itinéraire depuis input extérieur
# ============================
with open("itineraire.json", "r", encoding="utf-8") as f:
    data = json.load(f)

itineraire = [poi["name"] for poi in data["POIs"]]

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
        plt.text(x+5, y-5, name, color="blue", fontsize=10)
    else:
        print(f"⚠️ POI '{name}' pas trouvé dans poi_positions")

plt.plot(xs, ys, color="red", linewidth=2, marker="o")
plt.title("Itinéraire importé")
plt.axis("off")
plt.show()

# ============================
# 6. Export lat/lon des POIs visités
# ============================
for name in itineraire:
    if name in poi_positions:
        x, y = poi_positions[name]
        lat, lon = pixel_to_geo(x, y)
        print(f"{name}: pixel=({x},{y}), geo=({lat:.6f}, {lon:.6f})")

import cv2
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx

# ============================
# 1. Charger l'image
# ============================
img = cv2.imread("plan_reconstruit.jpg")
h, w, _ = img.shape

# ============================
# 2. Définir deux points de référence
# ============================
# Exemple : (x_pixel, y_pixel) -> (lat, lon)
# ⚠️ A remplacer par des valeurs réelles que tu choisis
pixel_points = np.array([
    [w//2, h-200],   # Château (centre en bas)
    [w//2, h//3]     # Bassin central (Grand Canal vertical)
], dtype="float32")

geo_points = np.array([
    [48.804865, 2.120355],   # Château de Versailles
    [48.8085, 2.120355]      # Bassin au nord
], dtype="float32")

# Transformation affine (2 points suffisent pour mise à l’échelle verticale)
A, _ = cv2.estimateAffine2D(pixel_points, geo_points)

def pixel_to_geo(x, y):
    pt = np.array([[x, y, 1]], dtype="float32").T
    lat, lon = (A @ pt).flatten()
    return float(lat), float(lon)

# ============================
# 3. Définir un itinéraire (POIs en pixels)
# ============================
POIs = {
    "Château": (w//2, h-200),
    "Fontaine Latone": (w//2, h-500),
    "Bassin d’Apollon": (w//2, h//2),
    "Grand Canal": (w//2, h//3)
}

itineraire = ["Château", "Fontaine Latone", "Bassin d’Apollon", "Grand Canal"]

# ============================
# 4. Créer un masque marchable
# ============================
# Ici : on fait un masque simplifié en considérant les pixels clairs comme "marchables"
# ⚠️ Remplacer par ton masque Mask R-CNN
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
_, mask = cv2.threshold(gray, 200, 1, cv2.THRESH_BINARY)  # 1 = marchable, 0 = obstacle

# ============================
# 5. Graphe de navigation
# ============================
def mask_to_graph(mask):
    G = nx.grid_2d_graph(mask.shape[0], mask.shape[1])
    # Retirer les zones non marchables
    for (i, j) in list(G.nodes):
        if mask[i, j] == 0:
            G.remove_node((i, j))
    return G

G = mask_to_graph(mask)

# ============================
# 6. Trouver chemin avec A*
# ============================
def find_path(mask, start, goal):
    G = mask_to_graph(mask)
    start = (start[1], start[0])  # (y, x)
    goal = (goal[1], goal[0])
    try:
        path = nx.astar_path(G, start, goal, heuristic=lambda a, b: abs(a[0]-b[0]) + abs(a[1]-b[1]))
        return [(x, y) for y, x in path]
    except nx.NetworkXNoPath:
        print("⚠️ Pas de chemin trouvé entre", start, goal)
        return []

# ============================
# 7. Calculer et tracer le trajet complet
# ============================
plt.figure(figsize=(10, 14))
plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))

trajet_pixels = []
for i in range(len(itineraire)-1):
    p1 = POIs[itineraire[i]]
    p2 = POIs[itineraire[i+1]]
    path = find_path(mask, p1, p2)
    trajet_pixels.extend(path)
    # tracer ce segment
    if path:
        xs, ys = zip(*path)
        plt.plot(xs, ys, color="red", linewidth=2)

# Ajouter les points d’intérêt
for name, (x, y) in POIs.items():
    plt.scatter(x, y, c="blue", s=80)
    plt.text(x+5, y-5, name, color="blue", fontsize=10)

plt.title("Itinéraire sur les zones marchables")
plt.axis("off")
plt.show()

# ============================
# 8. Sauvegarder les coordonnées lat/lon des POIs
# ============================
for name, (x, y) in POIs.items():
    lat, lon = pixel_to_geo(x, y)
    print(f"{name}: pixel=({x},{y}), geo=({lat:.6f}, {lon:.6f})")

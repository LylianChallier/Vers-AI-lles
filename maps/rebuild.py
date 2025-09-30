import os
from PIL import Image

# 📂 Dossier où sont les tuiles
input_dir = "tuiles"

# 🖼 Nom du fichier final
output_file = "plan_reconstruit.jpg"

# 🔍 Lister les fichiers
files = [f for f in os.listdir(input_dir) if f.endswith(".jpg")]

# Extraire les indices depuis le nom "plan_4_1_2.jpg" -> (row=1, col=2)
tiles = {}
max_row, max_col = 0, 0

for filename in files:
    parts = filename.replace(".jpg", "").split("_")
    # Exemple : plan_4_1_2 → [plan, 4, 1, 2]
    row = int(parts[-2])
    col = int(parts[-1])

    img = Image.open(os.path.join(input_dir, filename))
    tiles[(row, col)] = img

    max_row = max(max_row, row)
    max_col = max(max_col, col)

# Dimensions d’une tuile
tile_width, tile_height = next(iter(tiles.values())).size

# Créer l’image finale
full_width = tile_width * max_col
full_height = tile_height * max_row
result = Image.new("RGB", (full_width, full_height))

# Coller les tuiles
for (row, col), img in tiles.items():
    x = (col - 1) * tile_width
    y = (row - 1) * tile_height
    result.paste(img, (x, y))

# Sauver le résultat
result.save(output_file)
print(f"✅ Image reconstituée sauvegardée : {output_file}")

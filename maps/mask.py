import cv2
import numpy as np

# 1. Charger l'image
img = cv2.imread("plan_reconstruit.jpg")
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# 2. Détection de contours (repérer les allées rectilignes)
edges = cv2.Canny(gray, 80, 200)

# 3. Seuillage adaptatif (détecte les zones claires, mais localement)
thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                               cv2.THRESH_BINARY, 51, -10)

# 4. Combiner edges + seuil
mask = cv2.bitwise_and(thresh, thresh, mask=edges)

# 5. Morphologie pour connecter les chemins
kernel = np.ones((5, 5), np.uint8)
mask = cv2.dilate(mask, kernel, iterations=2)
mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)

# 6. Sauvegarde
cv2.imwrite("mask_marchable.png", mask)

print("✅ Masque marchable réaliste sauvegardé dans mask_marchable.png")

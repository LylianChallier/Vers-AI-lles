# tools/book_train.py
import requests
from langchain.tools import tool

# 5️⃣ Réservation train
@tool
def book_train(train_id: str) -> str:
    return f"Train {train_id} réservé !"

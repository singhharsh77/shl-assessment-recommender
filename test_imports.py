import fastapi
import sentence_transformers
import faiss
import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np

print("✅ All imports successful!")
print(f"Sentence Transformers version: {sentence_transformers.__version__}")

import requests
import os
from dotenv import load_dotenv

load_dotenv()
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")

def generate_product_image(prompt: str):
    url = "https://api.replicate.com/v1/predictions"
    headers = {
        "Authorization": f"Token {REPLICATE_API_TOKEN}",
        "Content-Type": "application/json",
    }

    data = {
        "version": "a9758cbf3c8d4c998b813da9a4f1b3175d31d507c9c6d0b21db52f8f2c3e1f3e",  # sdxl
        "input": {
            "prompt": f"{prompt}, product photo, professional e-commerce style, white background",
            "width": 512,
            "height": 512,
            "num_outputs": 1
        }
    }

    response = requests.post(url, headers=headers, json=data)
    prediction = response.json()
    status_url = prediction["urls"]["get"]

    # Bekle ve sonucu al
    for _ in range(20):
        result = requests.get(status_url, headers=headers).json()
        if result["status"] == "succeeded":
            return result["output"][0]
        elif result["status"] == "failed":
            raise Exception("Image generation failed")
    
    raise TimeoutError("Image generation timed out")

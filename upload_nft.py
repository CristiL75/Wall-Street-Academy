import requests
import json
import os

# === CONFIG ===
JWT = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySW5mb3JtYXRpb24iOnsiaWQiOiJjYzk1ZDRjMy0xNGVhLTQ1ZDMtODk1Zi1lNGI1ZjQ0NTUwZTciLCJlbWFpbCI6ImNyaXN0aWxhdGN1N0B5YWhvby5jb20iLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwicGluX3BvbGljeSI6eyJyZWdpb25zIjpbeyJkZXNpcmVkUmVwbGljYXRpb25Db3VudCI6MSwiaWQiOiJGUkExIn0seyJkZXNpcmVkUmVwbGljYXRpb25Db3VudCI6MSwiaWQiOiJOWUMxIn1dLCJ2ZXJzaW9uIjoxfSwibWZhX2VuYWJsZWQiOmZhbHNlLCJzdGF0dXMiOiJBQ1RJVkUifSwiYXV0aGVudGljYXRpb25UeXBlIjoic2NvcGVkS2V5Iiwic2NvcGVkS2V5S2V5IjoiNjI4ZjE3MzYwZjE0ZTIwYjY4NjAiLCJzY29wZWRLZXlTZWNyZXQiOiI2ZjI1NGVmMzNhYTEzYmNkYmQ1NTgwNTJiYmZhMWFkOTVkZDA1NTNiMDUyMWM1YTc1YjM1OWU2MmJhNmE4MDgwIiwiZXhwIjoxNzc3Mjk5OTQ2fQ.AgTp75M0QtAJMMzFeGvaD1519Wmlb4DiZrRTnQGeQrM"  # pune aici token-ul TĂU JWT complet
IMAGE_PATH = "bull.png"  # imaginea ta
NFT_NAME = "Wall Street Bull"
NFT_DESCRIPTION = "An exclusive NFT reward for active users of Wall Street Academy."

# === SETUP HEADERS ===
headers = {
    "Authorization": f"Bearer {JWT}",
}

# === UPLOAD IMAGE ===
print("🚀 Uploading image to Pinata...")
with open(IMAGE_PATH, "rb") as file_data:
    files = {"file": file_data}
    response = requests.post("https://api.pinata.cloud/pinning/pinFileToIPFS", headers=headers, files=files)

if response.status_code != 200:
    print(f"❌ Image upload failed: {response.text}")
    exit()

image_cid = response.json()["IpfsHash"]
image_uri = f"ipfs://{image_cid}"
print(f"✅ Image uploaded! IPFS URI: {image_uri}")

# === CREATE METADATA ===
metadata = {
    "name": NFT_NAME,
    "description": NFT_DESCRIPTION,
    "image": image_uri,
}

metadata_file = "metadata.json"
with open(metadata_file, "w") as f:
    json.dump(metadata, f)

# === UPLOAD METADATA ===
print("🚀 Uploading metadata to Pinata...")
with open(metadata_file, "rb") as meta_file:
    files = {"file": meta_file}
    response = requests.post("https://api.pinata.cloud/pinning/pinFileToIPFS", headers=headers, files=files)

if response.status_code != 200:
    print(f"❌ Metadata upload failed: {response.text}")
    exit()

metadata_cid = response.json()["IpfsHash"]
metadata_uri = f"ipfs://{metadata_cid}"
print(f"✅ Metadata uploaded! Metadata IPFS URI: {metadata_uri}")

# === CLEANUP ===
os.remove(metadata_file)

print("\n🎉 Gata! NFT-ul complet e la IPFS Metadata link:")
print(metadata_uri)

from datetime import datetime, timedelta
from decimal import Decimal
from models.user import User
from web3 import Web3
import os
import json
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from beanie import Document
from typing import Optional

from models.portfolio import Portfolio

from bson import ObjectId

# Nou model pentru a urmări achivements minate
class UserAchievement(Document):
    user_id: str
    achievement_type: str  # "10_days", "profit_positive", etc.
    wallet_address: str
    tx_hash: Optional[str] = None
    minted_at: Optional[datetime] = None
    token_uri: Optional[str] = None
    
    class Settings:
        name = "user_achievements"

async def get_user_total_profit(user_id: str) -> float:
    print("Calculating profit for user:", user_id)
    portfolio = await Portfolio.find_one(Portfolio.user_id == ObjectId(user_id))
    print("Portfolio found:", portfolio)
    if not portfolio or not portfolio.holdings:
        print("No portfolio or holdings")
        return 0.0
    total_profit = 0.0
    for h in portfolio.holdings:
        print("Holding:", h.symbol, h.current_price, h.avg_buy_price, h.quantity)
        total_profit += (h.current_price - h.avg_buy_price) * h.quantity
    print("Total profit:", total_profit)
    return total_profit
# Inițializează routerul pentru FastAPI
router = APIRouter()

# Încarcă variabilele din .env
load_dotenv()

NFT_CONTRACT_ADDRESS = Web3.to_checksum_address(os.getenv("NFT_CONTRACT_ADDRESS"))
BLOCKCHAIN_URL = os.getenv("BLOCKCHAIN_URL")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")

with open("blockchain/artifacts/contracts/UserAchievementNFT.sol/UserAchievementNFT.json") as f:
    abi = json.load(f)["abi"]

w3 = Web3(Web3.HTTPProvider(BLOCKCHAIN_URL))
contract = w3.eth.contract(address=NFT_CONTRACT_ADDRESS, abi=abi)
admin_address = w3.eth.account.from_key(PRIVATE_KEY).address

async def check_and_mint_10_days_nft(user_id: str):
    user = await User.get(user_id)
    if not user or not user.wallet_address:
        return {"error": "User not found or no wallet address"}
    
    # Verifică dacă userul deja are acest achievement
    existing_achievement = await UserAchievement.find_one(
        {"user_id": user_id, "achievement_type": "10_days"}
    )
    
    if existing_achievement:
        print("User already has 10 days achievement")
        return {"info": "Achievement already minted", "tx_hash": existing_achievement.tx_hash}
        
    if user.created_at <= datetime.utcnow() - timedelta(days=10):
        achievement = "10_days"
        # Folosește direct linkul IPFS generat de Pinata pentru acest achievement
        token_uri = "ipfs://QmP7vuFVH6jNfwU5sQP16AstYRUEvGwUjQu2wxwXz12E3Q"
        nonce = w3.eth.get_transaction_count(admin_address)
        wallet_address = w3.to_checksum_address(user.wallet_address)
        txn = contract.functions.mintNFT(wallet_address, token_uri).build_transaction({
            "from": admin_address,
            "nonce": nonce,
            "gas": 300000,
            "gasPrice": w3.to_wei("10", "gwei"),
        })
        # Adaugăm logging pentru a vedea ce atribute are signed_txn
        signed_txn = w3.eth.account.sign_transaction(txn, PRIVATE_KEY)
        print("Signed transaction attributes:", dir(signed_txn))
        # Încercăm cu raw_transaction (cu underscore)
        tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        
        # Salvează în baza de date
        new_achievement = UserAchievement(
            user_id=user_id,
            achievement_type="10_days",
            wallet_address=wallet_address,
            tx_hash=tx_hash.hex(),
            token_uri=token_uri,
            minted_at=datetime.utcnow()
        )
        await new_achievement.insert()
        
        return {"tx_hash": tx_hash.hex()}
    else:
        return {"error": "User does not qualify for 10 days NFT"}

async def check_and_mint_profit_nft(user_id: str):
    user = await User.get(user_id)
    if not user or not user.wallet_address:
        return {"error": "User not found or no wallet address"}
    
    # Verifică dacă userul deja are acest achievement
    existing_achievement = await UserAchievement.find_one(
        {"user_id": user_id, "achievement_type": "profit_positive"}
    )
    
    if existing_achievement:
        print("User already has profit achievement")
        return {"info": "Achievement already minted", "tx_hash": existing_achievement.tx_hash}
        
    profit = await get_user_total_profit(user_id)
    if profit is None:
        return {"error": "Profit data not available for user"}
    if Decimal(profit) > 0:
        achievement = "profit_positive"
       
        token_uri = "ipfs://QmP7vuFVH6jNfwU5sQP16AstYRUEvGwUjQu2wxwXz12E3Q"
        nonce = w3.eth.get_transaction_count(admin_address)
        wallet_address = w3.to_checksum_address(user.wallet_address)
        txn = contract.functions.mintNFT(wallet_address, token_uri).build_transaction({
            "from": admin_address,
            "nonce": nonce,
            "gas": 300000,
            "gasPrice": w3.to_wei("10", "gwei"),
        })
        signed_txn = w3.eth.account.sign_transaction(txn, PRIVATE_KEY)
        # Încercăm cu raw_transaction (cu underscore)
        tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        
        # Salvează în baza de date
        new_achievement = UserAchievement(
            user_id=user_id,
            achievement_type="profit_positive",
            wallet_address=wallet_address,
            tx_hash=tx_hash.hex(),
            token_uri=token_uri,
            minted_at=datetime.utcnow()
        )
        await new_achievement.insert()
        
        return {"tx_hash": tx_hash.hex()}
    else:
        return {"error": "User does not qualify for profit NFT"}
# Rute FastAPI pentru a declanșa mintarea achievement-urilor
@router.post("/check-10-days-nft/{user_id}")
async def check_10_days_nft(user_id: str):
    return await check_and_mint_10_days_nft(user_id)

@router.post("/check-profit-nft/{user_id}")
async def check_profit_nft(user_id: str):
    return await check_and_mint_profit_nft(user_id)


@router.get("/user-nfts/{wallet_address}")
async def get_user_nfts(wallet_address: str):
    """
    Returnează lista de NFT-uri deținute de un wallet, cu metadata (token_uri).
    """
    try:
        print(f"Fetching NFTs for wallet: {wallet_address}")
        wallet_checksum = Web3.to_checksum_address(wallet_address)
        print(f"Checksum address: {wallet_checksum}")
        
        # Verifică NFT-uri din baza de date ca fallback/backup
        db_achievements = await UserAchievement.find(
            {"wallet_address": wallet_address}
        ).to_list()
        
        print(f"Found {len(db_achievements)} NFTs in database")
        
        nfts_from_db = []
        for ach in db_achievements:
            nfts_from_db.append({
                "token_id": ach.tx_hash[:10],  # Un identificator unic bazat pe tx_hash
                "token_uri": ach.token_uri,
                "metadata": {
                    "name": f"Achievement: {ach.achievement_type}",
                    "description": f"Wall Street Academy Achievement: {ach.achievement_type}",
                    "image": ach.token_uri.replace("ipfs://", "https://ipfs.io/ipfs/")
                }
            })
        
        try:
            # Încearcă să obțină NFT-urile din blockchain
            print("Calling balanceOf...")
            balance = contract.functions.balanceOf(wallet_checksum).call()
            print(f"NFT balance from blockchain: {balance}")
            
            if balance == 0:
                print("No NFTs found in blockchain, returning database results")
                return nfts_from_db if nfts_from_db else []
            
            nfts = []
            
            # Folosim tokenOfOwnerByIndex în loc de scanare - mai eficient
            for i in range(balance):
                try:
                    token_id = contract.functions.tokenOfOwnerByIndex(wallet_checksum, i).call()
                    print(f"Token ID from index {i}: {token_id}")
                    
                    # Obține URL-ul de metadata
                    token_uri = contract.functions.tokenURI(token_id).call()
                    print(f"Token URI: {token_uri}")
                    
                    # Pregătește metadatele pentru frontend
                    nfts.append({
                        "token_id": token_id,
                        "token_uri": token_uri,
                        "metadata": {
                            "name": "Achievement NFT",
                            "description": "Wall Street Academy Achievement",
                            "image": token_uri.replace("ipfs://", "https://ipfs.io/ipfs/")
                        }
                    })
                except Exception as e:
                    print(f"Error getting token at index {i}: {e}")
                    continue
            
            if len(nfts) > 0:
                print(f"Returning {len(nfts)} NFTs from blockchain")
                return nfts
            else:
                print("Falling back to database NFTs")
                return nfts_from_db if nfts_from_db else []
                
        except Exception as e:
            # În cazul în care blockchain-ul nu răspunde, folosește NFT-urile din baza de date
            print(f"Error accessing blockchain: {e}")
            print("Falling back to database results")
            return nfts_from_db if nfts_from_db else []
            
    except Exception as e:
        print(f"ERROR in get_user_nfts: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching NFTs: {str(e)}")
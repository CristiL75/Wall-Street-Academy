from fastapi import APIRouter, HTTPException
from models.user import User
from web3 import Web3
import os, json
from dotenv import load_dotenv

router = APIRouter()
load_dotenv()

NFT_CONTRACT_ADDRESS = Web3.to_checksum_address(os.getenv("NFT_CONTRACT_ADDRESS"))
BLOCKCHAIN_URL = os.getenv("BLOCKCHAIN_URL")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")

with open("blockchain/artifacts/contracts/UserAchievementNFT.sol/UserAchievementNFT.json") as f:
    abi = json.load(f)["abi"]

w3 = Web3(Web3.HTTPProvider(BLOCKCHAIN_URL))
contract = w3.eth.contract(address=NFT_CONTRACT_ADDRESS, abi=abi)
admin_address = w3.eth.account.from_key(PRIVATE_KEY).address

@router.post("/mint-nft-for-user/{user_id}")
async def mint_nft_for_user(user_id: str, achievement: str):
    user = await User.get(user_id)
    if not user or not user.wallet_address:
        raise HTTPException(status_code=404, detail="User not found or no wallet address")
    token_uri = f"https://siteul-tau/metadata/{achievement}.json"
    nonce = w3.eth.get_transaction_count(admin_address)
    wallet_address = Web3.to_checksum_address(user.wallet_address)
    txn = contract.functions.mintNFT(wallet_address, token_uri).build_transaction({
        "from": admin_address,
        "nonce": nonce,
        "gas": 300000,
        "gasPrice": w3.to_wei("10", "gwei"),
    })
    signed_txn = w3.eth.account.sign_transaction(txn, PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
    return {"tx_hash": tx_hash.hex()}
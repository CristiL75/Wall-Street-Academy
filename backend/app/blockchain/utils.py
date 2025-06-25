from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv
import os
import time
from bson import ObjectId

load_dotenv()

# === Setup Web3 ===
w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))

# === ABIs ===
trade_abi = [
    {
        "inputs": [
            {"internalType": "address", "name": "user", "type": "address"},
            {"internalType": "string", "name": "symbol", "type": "string"},
            {"internalType": "uint256", "name": "amount", "type": "uint256"},
            {"internalType": "bool", "name": "isBuy", "type": "bool"}
        ],
        "name": "registerTrade",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "address", "name": "user", "type": "address"}
        ],
        "name": "getUserTrades",
        "outputs": [
            {
                "components": [
                    {"internalType": "string", "name": "symbol", "type": "string"},
                    {"internalType": "uint256", "name": "amount", "type": "uint256"},
                    {"internalType": "bool", "name": "isBuy", "type": "bool"},
                    {"internalType": "uint256", "name": "timestamp", "type": "uint256"}
                ],
                "internalType": "struct TradeSimulator.Trade[]",
                "name": "",
                "type": "tuple[]"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

nft_abi = [
    {
        "inputs": [
            {"internalType": "address", "name": "to", "type": "address"},
            {"internalType": "string", "name": "tokenURI", "type": "string"}
        ],
        "name": "mintNFT",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

# === Config ===
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
TRADE_CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")
NFT_CONTRACT_ADDRESS = os.getenv("NFT_CONTRACT_ADDRESS")

ACCOUNT = Account.from_key(PRIVATE_KEY)
trade_contract = w3.eth.contract(address=Web3.to_checksum_address(TRADE_CONTRACT_ADDRESS), abi=trade_abi)
nft_contract = w3.eth.contract(address=Web3.to_checksum_address(NFT_CONTRACT_ADDRESS), abi=nft_abi)

# === Functions ===
def register_trade_on_chain(trade_data):
    """
    Register trade data on the blockchain
    """
    try:
        # Convert MongoDB ObjectId to a hex string if needed
        user_id = trade_data.get('user_id')
        if isinstance(user_id, ObjectId):
            user_id = str(user_id)  # Convert ObjectId to string
        
        # For simulation/educational purposes only
        # In a real blockchain implementation, you would call a smart contract here
        print(f"BLOCKCHAIN: Registering trade for user {user_id}")
        print(f"BLOCKCHAIN: Symbol: {trade_data.get('symbol')}")
        print(f"BLOCKCHAIN: Quantity: {trade_data.get('quantity')}")
        print(f"BLOCKCHAIN: Price: {trade_data.get('execution_price')}")
        
        # Return a mock transaction hash
        import hashlib
        import time
        mock_hash = hashlib.sha256(f"{user_id}-{time.time()}".encode()).hexdigest()
        return {"tx_hash": f"0x{mock_hash[:40]}"}
        
    except Exception as e:
        # Log the error but don't fail the trade
        print(f"BLOCKCHAIN ERROR: {str(e)}")
        return {"error": str(e), "tx_hash": None}
def get_trades_from_chain(user_addr: str):
    user_addr = Web3.to_checksum_address(user_addr)
    trades = trade_contract.functions.getUserTrades(user_addr).call()

    result = []
    for trade in trades:
        result.append({
            "symbol": trade[0],
            "amount": trade[1],
            "is_buy": trade[2],
            "timestamp": trade[3]
        })

    return result

def mint_nft_to_user(user_wallet: str, token_uri: str) -> str:
    txn = nft_contract.functions.mintNFT(
        Web3.to_checksum_address(user_wallet),
        token_uri
    ).build_transaction({
        "from": ACCOUNT.address,
        "nonce": w3.eth.get_transaction_count(ACCOUNT.address),
        "gas": 300000,
        "gasPrice": w3.eth.gas_price
    })
    signed_txn = w3.eth.account.sign_transaction(txn, private_key=PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
    return tx_hash.hex()

# 🎯 Funcție bonus: Reward NFT pentru useri activi
def reward_active_user(wallet_address: str, metadata_uri: str) -> str:
    print(f"🎁 Mint NFT to {wallet_address}")
    return mint_nft_to_user(wallet_address, metadata_uri)
def get_user_nfts(wallet_address: str):
    """
    Returnează lista de tokenURI-uri pentru NFT-urile deținute de un wallet.
    """
    wallet_address = Web3.to_checksum_address(wallet_address)
    balance = nft_contract.functions.balanceOf(wallet_address).call()
    uris = []
    for i in range(balance):
        token_id = nft_contract.functions.tokenOfOwnerByIndex(wallet_address, i).call()
        uri = nft_contract.functions.tokenURI(token_id).call()
        uris.append(uri)
    return uris
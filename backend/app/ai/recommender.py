

import numpy as np
from sklearn.feature_extraction import DictVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from datetime import datetime
from blockchain.utils import get_trades_from_chain
from models.user import User


def build_user_trade_matrix(users, decay_weighting=True):
    user_trades = {}
    now = datetime.utcnow().timestamp()

    for user in users:
        if not user.wallet_address:
            continue
        try:
            trades = get_trades_from_chain(user.wallet_address)
        except:
            continue

        summary = {}
        for t in trades:
            symbol = t['symbol']
            amount = t['amount']
            timestamp = t['timestamp']

       
            weight = 1.0
            if decay_weighting:
                days_ago = (now - timestamp) / (60 * 60 * 24)
                weight = np.exp(-days_ago / 30)

            summary[symbol] = summary.get(symbol, 0) + amount * weight

        if summary:
            user_trades[str(user.id)] = summary

    return user_trades


def generate_recommendations(user_id, user_trades, top_n=5):
    if user_id not in user_trades:
        return []

    vectorizer = DictVectorizer(sparse=False)
    user_ids = list(user_trades.keys())
    X = vectorizer.fit_transform(user_trades.values())

    X = X / np.linalg.norm(X, axis=1, keepdims=True)

    similarities = cosine_similarity(X)
    index = user_ids.index(user_id)

    target_symbols = set(user_trades[user_id].keys())
    scores = {}

    for i, score in enumerate(similarities[index]):
        if i == index:
            continue
        other_id = user_ids[i]
        for symbol, amount in user_trades[other_id].items():
            if symbol not in target_symbols:
                scores[symbol] = scores.get(symbol, 0) + score * amount

    sorted_scores = sorted(scores.items(), key=lambda x: -x[1])
    return [symbol for symbol, _ in sorted_scores[:top_n]]


async def update_user_recommendations():
    users = await User.find_all().to_list()
    matrix = build_user_trade_matrix(users)

    for user in users:
        recs = generate_recommendations(str(user.id), matrix)
        user.recommendations = recs
        await user.save()

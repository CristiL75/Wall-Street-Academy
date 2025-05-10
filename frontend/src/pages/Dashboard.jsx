import { useEffect, useState } from "react";
import { getTokenPayload } from "../utils/auth";
import axios from "axios";

import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";
import { Bar } from "react-chartjs-2";

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

const Dashboard = () => {
  const [userId, setUserId] = useState(null);
  const [trades, setTrades] = useState([]);
  const [portfolio, setPortfolio] = useState(null);
  const [nfts, setNfts] = useState([]);

  useEffect(() => {
    const payload = getTokenPayload();
    if (payload?.sub) {
      setUserId(payload.sub);
      fetchTrades(payload.sub);
      fetchPortfolio(payload.sub);
      fetchNFTs(payload.sub);
    }
  }, []);

  const fetchTrades = async (uid) => {
    try {
      const res = await axios.get(`/trades/user/${uid}`);
      const data = Array.isArray(res.data) ? res.data : [];
      setTrades(data);
    } catch (err) {
      console.error("Error loading trades:", err);
      setTrades([]);
    }
  };

  const fetchPortfolio = async (uid) => {
    try {
      const res = await axios.get(`/portfolios/${uid}`);
      setPortfolio(res.data);
    } catch (err) {
      console.error("Error loading portfolio:", err);
    }
  };

  const fetchNFTs = async (uid) => {
    try {
      const res = await axios.get(`/nfts/${uid}`);
      const nftArray = Array.isArray(res.data) ? res.data : res.data.nfts || [];

      const nftData = await Promise.all(
        nftArray.map(async (nft) => {
          const ipfsUrl = nft.token_uri.replace("ipfs://", "https://ipfs.io/ipfs/");
          const metaRes = await axios.get(ipfsUrl);
          return {
            ...nft,
            name: metaRes.data.name,
            image: metaRes.data.image.replace("ipfs://", "https://ipfs.io/ipfs/"),
            description: metaRes.data.description,
          };
        })
      );
      setNfts(nftData);
    } catch (err) {
      console.error("Error loading NFTs:", err);
    }
  };

  const renderPortfolioChart = () => {
    if (!portfolio?.holdings?.length) return <p>No holdings to display.</p>;

    const data = {
      labels: portfolio.holdings.map((h) => h.symbol),
      datasets: [
        {
          label: "Market Value",
          data: portfolio.holdings.map((h) => h.market_value),
          backgroundColor: "rgba(75,192,192,0.6)",
        },
      ],
    };

    return <Bar data={data} />;
  };

  return (
    <div className="dashboard p-4">
      <h1 className="text-2xl font-bold mb-4">Welcome to your Dashboard</h1>

      <section className="mb-6">
        <h2 className="text-xl font-semibold">📈 Portfolio Overview</h2>
        {portfolio && (
          <div className="mb-4 text-sm text-gray-700">
            <p><strong>Cash:</strong> ${portfolio.cash}</p>
            <p><strong>Total Invested:</strong> ${portfolio.total_invested}</p>
            <p><strong>Total Value:</strong> ${portfolio.total_value}</p>
            <p><strong>Total Profit:</strong> ${portfolio.total_profit}</p>
          </div>
        )}
        {renderPortfolioChart()}
      </section>

      {portfolio?.holdings?.length > 0 && (
        <section className="mb-6">
          <h2 className="text-xl font-semibold">📊 Invested Companies</h2>
          <div className="flex flex-wrap gap-2 mt-2">
            {Array.from(new Set(portfolio.holdings.map((h) => h.symbol))).map((symbol, i) => (
              <span
                key={i}
                className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm font-medium"
              >
                {symbol}
              </span>
            ))}
          </div>
        </section>
      )}

      <section className="mb-6">
        <h2 className="text-xl font-semibold">📄 Recent Trades</h2>
        <ul className="list-disc ml-6">
          {trades.slice(0, 5).map((trade, i) => (
            <li key={i}>
              {trade.symbol} — {trade.trade_type} {trade.quantity} at {trade.execution_price}$ on {new Date(trade.timestamp * 1000).toLocaleDateString()}
            </li>
          ))}
        </ul>
      </section>

      <section className="mb-6">
        <h2 className="text-xl font-semibold">🏆 NFTs Earned</h2>
        {nfts.length === 0 ? (
          <p>No NFTs yet.</p>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
            {nfts.map((nft, i) => (
              <div key={i} className="bg-white shadow p-4 rounded-lg">
                <img src={nft.image} alt={nft.name} className="w-full h-48 object-contain mb-2" />
                <h3 className="font-bold text-lg">{nft.name}</h3>
                <p className="text-sm text-gray-600">{nft.description}</p>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
};

export default Dashboard;

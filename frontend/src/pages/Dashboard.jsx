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
  const [refreshCounter, setRefreshCounter] = useState(0);

    // State-uri pentru modalul de vânzare
  const [sellModalOpen, setSellModalOpen] = useState(false);
  const [selectedHolding, setSelectedHolding] = useState(null);
  const [sellQuantity, setSellQuantity] = useState(0);
  const [sellPrice, setSellPrice] = useState(0);
  const [sellFeedback, setSellFeedback] = useState("");
  
  // Funcție pentru deschiderea modalului de vânzare
  const openSellModal = (holding) => {
    setSelectedHolding(holding);
    setSellQuantity(holding.quantity); // Implicit, vinde tot
    setSellPrice(holding.current_price); // Prețul curent
    setSellFeedback("");
    setSellModalOpen(true);
  };

    const closeSellModal = () => {
    setSellModalOpen(false);
    setSelectedHolding(null);
    setSellQuantity(0);
    setSellPrice(0);
    setSellFeedback("");
  };
  
  // Funcție pentru executarea vânzării
  const executeSell = async () => {
    if (!selectedHolding || sellQuantity <= 0 || sellQuantity > selectedHolding.quantity) {
      setSellFeedback("❌ Cantitate invalidă");
      return;
    }
    
    try {
      const payload = {
        user_id: userId,
        symbol: selectedHolding.symbol,
        quantity: Number(sellQuantity),
        trade_type: "sell",
        order_type: "market",
        execution_price: Number(sellPrice),
        commission: 0,
      };
      
      setSellFeedback("Procesare tranzacție...");
      
      const response = await axios.post("http://127.0.0.1:8000/trades/", payload);
      console.log("Sell response:", response.data);
      
      setSellFeedback("✅ Tranzacție de vânzare realizată cu succes!");
      
      // După 2 secunde, închide modalul și actualizează datele
      setTimeout(() => {
        closeSellModal();
        forceRefresh(); // Actualizează dashboardul pentru a reflecta schimbările
      }, 2000);
      
    } catch (err) {
      console.error("Sell failed:", err);
      setSellFeedback(`❌ Eroare: ${err.response?.data?.detail || err.message}`);
    }
  };
  

  useEffect(() => {
    const payload = getTokenPayload();
    if (payload?.sub) {
      setUserId(payload.sub);
      
      // Funcția de actualizare a datelor
      const updateDashboard = () => {
        fetchTrades(payload.sub);
        fetchPortfolio(payload.sub);
        fetchNFTs(payload.sub);
      };
      
      // Încărcarea inițială
      updateDashboard();
      
      // Configurare refresh periodic - la 30 secunde
      const refreshInterval = setInterval(() => {
        console.log("Refreshing dashboard data...");
        updateDashboard();
      }, 30000);
      
      // Cleanup la unmount
      return () => clearInterval(refreshInterval);
    }
  }, [refreshCounter]);

  // Funcție pentru a forța reîmprospătarea
  const forceRefresh = () => {
    setRefreshCounter(prev => prev + 1);
  };

  const fetchTrades = async (uid) => {
    try {
      // Prima încercare cu endpoint-ul /trades/user/{uid}
      try {
        const res = await axios.get(`http://127.0.0.1:8000/trades/user/${uid}`);
        const data = Array.isArray(res.data) ? res.data : [];
        console.log("Loaded trades:", data);
        setTrades(data);
      } catch (specificErr) {
        // Dacă endpoint-ul specific utilizatorului nu există, încercăm să obținem toate tranzacțiile
        console.log("Specific user trades endpoint not found, falling back to all trades");
        const allTradesRes = await axios.get(`http://127.0.0.1:8000/trades/`);
        
        // Filtrăm manual tranzacțiile pentru utilizatorul curent
        const userTrades = allTradesRes.data.filter(trade => 
          trade.user_id === uid || 
          trade.user_id?.$oid === uid // Pentru cazul când MongoDB returnează ObjectId ca obiect
        );
        
        console.log("Filtered trades for user:", userTrades);
        setTrades(userTrades);
      }
    } catch (err) {
      console.error("Error loading trades:", err);
      setTrades([]);
    }
  };

  const fetchPortfolio = async (uid) => {
    try {
      // URL complet pentru API portfolios
      const res = await axios.get(`http://127.0.0.1:8000/portfolios/${uid}`);
      console.log("Loaded portfolio:", res.data);
      
      // Verifică dacă holdings este un array, altfel inițializează ca array gol
      if (!res.data.holdings || !Array.isArray(res.data.holdings)) {
        res.data.holdings = [];
      }
      
      setPortfolio(res.data);
    } catch (err) {
      console.error("Error loading portfolio:", err);
      // Setează un portofoliu gol în caz de eroare
      setPortfolio({ cash: 0, holdings: [] });
    }
  };

  const fetchNFTs = async (uid) => {
    try {
      // URL complet pentru API nfts
      const res = await axios.get(`http://127.0.0.1:8000/nfts/${uid}`);
      const nftArray = Array.isArray(res.data) ? res.data : res.data.nfts || [];

      const nftData = await Promise.all(
        nftArray.map(async (nft) => {
          const ipfsUrl = nft.token_uri.replace("ipfs://", "https://ipfs.io/ipfs/");
          try {
            const metaRes = await axios.get(ipfsUrl);
            return {
              ...nft,
              name: metaRes.data.name,
              image: metaRes.data.image.replace("ipfs://", "https://ipfs.io/ipfs/"),
              description: metaRes.data.description,
            };
          } catch (metaErr) {
            console.error("Error loading NFT metadata:", metaErr);
            return {
              ...nft,
              name: "Unknown NFT",
              image: "",
              description: "Metadata unavailable"
            };
          }
        })
      );
      setNfts(nftData);
    } catch (err) {
      console.error("Error loading NFTs:", err);
      setNfts([]);
    }
  };

  // Funcții de calcul pentru valorile portofolliului
  const calculateTotalInvested = () => {
    if (!portfolio?.holdings || !Array.isArray(portfolio.holdings) || portfolio.holdings.length === 0) {
      return "0.00";
    }
    
    const totalInvested = portfolio.holdings.reduce((sum, holding) => {
      const avgPrice = parseFloat(holding.avg_buy_price || 0);
      const quantity = parseFloat(holding.quantity || 0);
      return sum + (quantity * avgPrice);
    }, 0);
    
    return totalInvested.toFixed(2);
  };
  
  const calculateTotalValue = () => {
    if (!portfolio?.holdings || !Array.isArray(portfolio.holdings) || portfolio.holdings.length === 0) {
      return "0.00";
    }
    
    const totalValue = portfolio.holdings.reduce((sum, holding) => {
      const currentPrice = parseFloat(holding.current_price || 0);
      const quantity = parseFloat(holding.quantity || 0);
      return sum + (quantity * currentPrice);
    }, 0);
    
    return totalValue.toFixed(2);
  };
  
  const calculateTotalProfit = () => {
    const invested = parseFloat(calculateTotalInvested());
    const value = parseFloat(calculateTotalValue());
    return (value - invested).toFixed(2);
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
    
    {/* Buton pentru reîmprospătare manuală */}
    <button 
      onClick={forceRefresh}
      className="mb-4 bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 transition"
    >
      Refresh Dashboard
    </button>

    <section className="mb-6">
      <h2 className="text-xl font-semibold">📈 Portfolio Overview</h2>
      {portfolio && (
        <div className="mb-4 text-sm text-gray-700">
          <p><strong>Cash:</strong> ${parseFloat(portfolio.cash).toFixed(2)}</p>
          <p><strong>Total Invested:</strong> ${calculateTotalInvested()}</p>
          <p><strong>Total Value:</strong> ${calculateTotalValue()}</p>
          <p><strong>Total Profit:</strong> ${calculateTotalProfit()}</p>
        </div>
      )}
      {renderPortfolioChart()}
    </section>

 
    {portfolio?.holdings?.length > 0 && (
      <section className="mb-6">
        <h2 className="text-xl font-semibold">📊 Portfolio Holdings</h2>
        <div className="mt-2 overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Symbol</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Quantity</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Avg Price</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Current Price</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Value</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Profit/Loss</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {portfolio.holdings.map((holding, idx) => {
                const profitLoss = (holding.current_price - holding.avg_buy_price) * holding.quantity;
                const profitLossPercent = ((holding.current_price / holding.avg_buy_price) - 1) * 100;
                
                return (
                  <tr key={idx}>
                    <td className="px-6 py-4 whitespace-nowrap">{holding.symbol}</td>
                    <td className="px-6 py-4 whitespace-nowrap">{holding.quantity}</td>
                    <td className="px-6 py-4 whitespace-nowrap">${holding.avg_buy_price.toFixed(2)}</td>
                    <td className="px-6 py-4 whitespace-nowrap">${holding.current_price.toFixed(2)}</td>
                    <td className="px-6 py-4 whitespace-nowrap">${holding.market_value.toFixed(2)}</td>
                    <td className={`px-6 py-4 whitespace-nowrap ${profitLoss >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      ${profitLoss.toFixed(2)} ({profitLossPercent.toFixed(2)}%)
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <button
                        onClick={() => openSellModal(holding)}
                        className="bg-red-500 hover:bg-red-600 text-white py-1 px-3 rounded text-sm"
                      >
                        Vinde
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>
    )}

    <section className="mb-6">
      <h2 className="text-xl font-semibold">📄 Recent Trades</h2>
      {trades.length === 0 ? (
        <p>No trades yet.</p>
      ) : (
        <div className="overflow-x-auto mt-2">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Symbol</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Quantity</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Price</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Total</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {trades.slice(0, 10).map((trade, i) => {
                const tradeDate = new Date(trade.timestamp);
                const total = trade.quantity * trade.execution_price;
                
                return (
                  <tr key={i}>
                    <td className="px-6 py-4 whitespace-nowrap">{tradeDate.toLocaleDateString()}</td>
                    <td className="px-6 py-4 whitespace-nowrap">{trade.symbol}</td>
                    <td className={`px-6 py-4 whitespace-nowrap ${
                      trade.trade_type === 'buy' ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {trade.trade_type.toUpperCase()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">{trade.quantity}</td>
                    <td className="px-6 py-4 whitespace-nowrap">${trade.execution_price}</td>
                    <td className="px-6 py-4 whitespace-nowrap">${total.toFixed(2)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
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

    {/* Modalul de vânzare - aici este partea care lipsea */}
    {sellModalOpen && selectedHolding && (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-lg max-w-md w-full p-6">
          <h3 className="text-xl font-semibold mb-4">Vinde acțiuni {selectedHolding.symbol}</h3>
          
          <div className="mb-4">
            <p>Deții: <strong>{selectedHolding.quantity}</strong> acțiuni</p>
            <p>Preț de cumpărare: <strong>${selectedHolding.avg_buy_price.toFixed(2)}</strong></p>
            <p>Preț curent: <strong>${selectedHolding.current_price.toFixed(2)}</strong></p>
          </div>
          
          <div className="mb-4">
            <label className="block text-sm font-medium mb-1">Cantitate de vânzare</label>
            <input
              type="number"
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
              min="0.01"
              max={selectedHolding.quantity}
              step="0.01"
              value={sellQuantity}
              onChange={(e) => setSellQuantity(parseFloat(e.target.value))}
            />
            <div className="flex justify-between mt-2">
              <button 
                className="text-xs text-blue-600"
                onClick={() => setSellQuantity(selectedHolding.quantity / 4)}
              >
                25%
              </button>
              <button 
                className="text-xs text-blue-600"
                onClick={() => setSellQuantity(selectedHolding.quantity / 2)}
              >
                50%
              </button>
              <button 
                className="text-xs text-blue-600"
                onClick={() => setSellQuantity(selectedHolding.quantity * 0.75)}
              >
                75%
              </button>
              <button 
                className="text-xs text-blue-600"
                onClick={() => setSellQuantity(selectedHolding.quantity)}
              >
                100%
              </button>
            </div>
          </div>
          
          <div className="mb-4">
            <label className="block text-sm font-medium mb-1">Preț de vânzare</label>
            <input
              type="number"
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
              min="0.01"
              step="0.01"
              value={sellPrice}
              onChange={(e) => setSellPrice(parseFloat(e.target.value))}
            />
          </div>
          
          <div className="mb-4">
            <p className="font-semibold">
              Valoare totală: ${(sellQuantity * sellPrice).toFixed(2)}
            </p>
            {sellFeedback && (
              <p className={`mt-2 text-sm ${sellFeedback.includes("❌") ? "text-red-600" : "text-green-600"}`}>
                {sellFeedback}
              </p>
            )}
          </div>
          
          <div className="flex justify-end space-x-3">
            <button 
              className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-100"
              onClick={closeSellModal}
            >
              Anulare
            </button>
            <button 
              className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
              onClick={executeSell}
            >
              Vinde
            </button>
          </div>
        </div>
      </div>
    )}
  </div>
); 
};

export default Dashboard;
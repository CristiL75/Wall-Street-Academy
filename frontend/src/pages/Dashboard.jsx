import { useEffect, useState } from "react";
import { getTokenPayload } from "../utils/auth";
import axios from "axios";

import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";


import { Bar, Pie, Doughnut } from "react-chartjs-2"; // adaugă importurile pentru alte tipuri de grafice

// Actualizează înregistrarea componentelor Chart.js
ChartJS.register(CategoryScale, LinearScale, BarElement, ArcElement, Title, Tooltip, Legend);



const Dashboard = () => {
  const [userId, setUserId] = useState(null);
  const [trades, setTrades] = useState([]);
  const [portfolio, setPortfolio] = useState(null);
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

  // Sortăm holdingurile după valoarea de piață pentru o vizualizare mai clară
  const sortedHoldings = [...portfolio.holdings].sort((a, b) => b.market_value - a.market_value);

  // Paletă de culori profesională
  const colorPalette = [
    'rgba(66, 133, 244, 0.8)',   // Google Blue
    'rgba(219, 68, 55, 0.8)',    // Google Red
    'rgba(244, 180, 0, 0.8)',    // Google Yellow
    'rgba(15, 157, 88, 0.8)',    // Google Green
    'rgba(98, 0, 238, 0.8)',     // Purple
    'rgba(0, 188, 212, 0.8)',    // Cyan
    'rgba(255, 87, 34, 0.8)',    // Deep Orange
    'rgba(121, 85, 72, 0.8)',    // Brown
    'rgba(158, 158, 158, 0.8)',  // Grey
    'rgba(96, 125, 139, 0.8)'    // Blue Grey
  ];

  const data = {
    labels: sortedHoldings.map((h) => h.symbol),
    datasets: [
      {
        label: "Market Value",
        data: sortedHoldings.map((h) => h.market_value),
        backgroundColor: sortedHoldings.map((_, idx) => colorPalette[idx % colorPalette.length]),
        borderColor: sortedHoldings.map((_, idx) => colorPalette[idx % colorPalette.length].replace('0.8', '1')),
        borderWidth: 1,
        borderRadius: 4, // margini rotunjite pentru bare
        hoverBackgroundColor: sortedHoldings.map((_, idx) => colorPalette[idx % colorPalette.length].replace('0.8', '0.9')),
        hoverBorderWidth: 2,
      },
    ],
  };

  const totalValue = parseFloat(calculateTotalValue());

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    indexAxis: 'y', // arată barele orizontal pentru o mai bună vizibilitate la multe holdinguri
    plugins: {
      legend: {
        display: false, // ascundem legenda, deoarece etichetele apar oricum pe axă
      },
      title: {
        display: true,
        text: 'Portfolio Allocation by Market Value',
        font: {
          size: 16,
          weight: 'bold',
          family: "'Inter', 'Helvetica', 'Arial', sans-serif"
        },
        padding: {
          top: 10,
          bottom: 20
        },
        color: '#333'
      },
      tooltip: {
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        titleColor: '#333',
        bodyColor: '#333',
        titleFont: {
          size: 14,
          weight: 'bold'
        },
        bodyFont: {
          size: 13
        },
        padding: 12,
        cornerRadius: 8,
        displayColors: true,
        borderColor: 'rgba(0, 0, 0, 0.1)',
        borderWidth: 1,
        callbacks: {
          label: function(context) {
            const value = context.raw;
            const percentage = ((value / totalValue) * 100).toFixed(1);
            return [
              `Value: $${value.toFixed(2)}`, 
              `Percentage: ${percentage}%`
            ];
          },
          labelTextColor: function() {
            return '#333';
          }
        }
      }
    },
    scales: {
      x: {
        grid: {
          display: true,
          color: 'rgba(0, 0, 0, 0.05)',
          drawBorder: false,
        },
        ticks: {
          callback: function(value) {
            return '$' + value.toLocaleString();
          },
          color: '#666',
          font: {
            size: 11
          }
        }
      },
      y: {
        grid: {
          display: false
        },
        ticks: {
          color: '#333',
          font: {
            weight: '500',
            size: 12
          }
        }
      }
    },
    animation: {
      duration: 1500,
      easing: 'easeInOutQuart'
    },
    layout: {
      padding: {
        left: 15,
        right: 25,
        top: 15,
        bottom: 15
      }
    }
  };

  // Adăugăm un control pentru a schimba tipul de grafic
  return (
    <div className="bg-white p-5 rounded-lg shadow-md hover:shadow-lg transition-all duration-300">
      <div className="mb-3 flex justify-between items-center">
        <h3 className="text-gray-600 text-sm font-medium">Holdings Distribution</h3>
        <div className="text-sm text-gray-500">
          Total: <span className="font-semibold text-gray-800">${totalValue}</span>
        </div>
      </div>
      
      <div className="h-80">
        <Bar data={data} options={options} />
      </div>

      {/* Adaugă informații suplimentare sub grafic */}
      <div className="mt-4 grid grid-cols-2 gap-2 text-xs text-gray-600">
        {sortedHoldings.slice(0, 6).map((h, idx) => (
          <div key={idx} className="flex items-center">
            <div
              className="w-3 h-3 rounded-full mr-1"
              style={{ backgroundColor: colorPalette[idx % colorPalette.length] }}
            />
            <span>{h.symbol}: </span>
            <span className="ml-1 font-medium">
              {((h.market_value / totalValue) * 100).toFixed(1)}%
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};

// Adaugă această funcție pentru a avea și un grafic circular (opțional)
const renderPortfolioDistribution = () => {
  if (!portfolio?.holdings?.length) return null;
  
  const sortedHoldings = [...portfolio.holdings].sort((a, b) => b.market_value - a.market_value);
  const totalValue = parseFloat(calculateTotalValue());
  
  // Grupează holdingurile mici într-o categorie "Others"
  const TOP_HOLDINGS = 5; // Numărul de holdinguri principale afișate individual
  const THRESHOLD_PERCENT = 3; // Pragul sub care holdingurile sunt grupate în "Others"
  
  let chartData = sortedHoldings.map(h => ({
    symbol: h.symbol,
    value: h.market_value,
    percent: (h.market_value / totalValue) * 100
  }));
  
  // Separăm holdingurile mici într-o categorie "Others"
  const mainHoldings = chartData
    .filter(item => item.percent >= THRESHOLD_PERCENT || chartData.indexOf(item) < TOP_HOLDINGS);
  
  const otherHoldings = chartData
    .filter(item => item.percent < THRESHOLD_PERCENT && chartData.indexOf(item) >= TOP_HOLDINGS);
  
  // Dacă avem holdinguri mici, le grupăm
  if (otherHoldings.length > 0) {
    const otherTotal = otherHoldings.reduce((sum, item) => sum + item.value, 0);
    mainHoldings.push({
      symbol: "Others",
      value: otherTotal,
      percent: (otherTotal / totalValue) * 100
    });
  }
  
  // Paletă de culori profesională
  const colorPalette = [
    'rgba(66, 133, 244, 0.8)',
    'rgba(219, 68, 55, 0.8)',
    'rgba(244, 180, 0, 0.8)',
    'rgba(15, 157, 88, 0.8)',
    'rgba(98, 0, 238, 0.8)',
    'rgba(0, 188, 212, 0.8)',
    'rgba(255, 87, 34, 0.8)',
    'rgba(121, 85, 72, 0.8)',
    'rgba(158, 158, 158, 0.8)',
  ];
  
  const data = {
    labels: mainHoldings.map(h => h.symbol),
    datasets: [
      {
        data: mainHoldings.map(h => h.value),
        backgroundColor: mainHoldings.map((_, idx) => colorPalette[idx % colorPalette.length]),
        borderColor: '#ffffff',
        borderWidth: 2,
        hoverBackgroundColor: mainHoldings.map((_, idx) => 
          colorPalette[idx % colorPalette.length].replace('0.8', '0.9')
        ),
        hoverBorderColor: '#ffffff',
        hoverBorderWidth: 3,
      }
    ]
  };
  
  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'right',
        labels: {
          boxWidth: 12,
          padding: 15,
          font: {
            size: 11
          },
          generateLabels: function(chart) {
            const data = chart.data;
            if (data.labels.length && data.datasets.length) {
              return data.labels.map((label, i) => {
                const value = data.datasets[0].data[i];
                const percent = ((value / totalValue) * 100).toFixed(1);
                return {
                  text: `${label} (${percent}%)`,
                  fillStyle: data.datasets[0].backgroundColor[i],
                  strokeStyle: '#fff',
                  lineWidth: 1,
                  hidden: false
                };
              });
            }
            return [];
          }
        }
      },
      tooltip: {
        callbacks: {
          label: function(context) {
            const value = context.raw;
            const percent = ((value / totalValue) * 100).toFixed(1);
            return [
              `${context.label}: $${value.toFixed(2)}`,
              `${percent}% of portfolio`
            ];
          }
        }
      }
    },
    cutout: '50%', // pentru Doughnut
    radius: '90%'
  };

  return (
    <div className="bg-white p-5 rounded-lg shadow-md hover:shadow-lg transition-all duration-300">
      <div className="mb-3">
        <h3 className="text-gray-600 text-sm font-medium">Portfolio Allocation</h3>
      </div>
      
      <div className="h-64">
        <Doughnut data={data} options={options} />
      </div>
    </div>
  );
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
  <h2 className="text-xl font-semibold mb-3">📈 Portfolio Overview</h2>
  
  {portfolio && (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <div className="bg-white p-4 rounded-lg shadow-md hover:shadow-lg transition-all duration-300">
        <p className="text-sm text-gray-500 mb-1">Cash Balance</p>
        <p className="text-2xl font-bold">${parseFloat(portfolio.cash).toFixed(2)}</p>
      </div>
      
      <div className="bg-white p-4 rounded-lg shadow-md hover:shadow-lg transition-all duration-300">
        <p className="text-sm text-gray-500 mb-1">Total Invested</p>
        <p className="text-2xl font-bold">${calculateTotalInvested()}</p>
      </div>
      
      <div className="bg-white p-4 rounded-lg shadow-md hover:shadow-lg transition-all duration-300">
        <p className="text-sm text-gray-500 mb-1">Total Market Value</p>
        <p className="text-2xl font-bold">${calculateTotalValue()}</p>
      </div>
      
      <div className={`bg-white p-4 rounded-lg shadow-md hover:shadow-lg transition-all duration-300 ${
        parseFloat(calculateTotalProfit()) >= 0 ? 'border-l-4 border-green-500' : 'border-l-4 border-red-500'
      }`}>
        <p className="text-sm text-gray-500 mb-1">Total Profit/Loss</p>
        <div className="flex items-baseline">
          <p className={`text-2xl font-bold ${
            parseFloat(calculateTotalProfit()) >= 0 ? 'text-green-600' : 'text-red-600'
          }`}>
            ${calculateTotalProfit()}
          </p>
          {parseFloat(calculateTotalInvested()) > 0 && (
            <p className={`ml-2 text-sm ${
              parseFloat(calculateTotalProfit()) >= 0 ? 'text-green-600' : 'text-red-600'
            }`}>
              ({((parseFloat(calculateTotalValue()) / parseFloat(calculateTotalInvested()) - 1) * 100).toFixed(2)}%)
            </p>
          )}
        </div>
      </div>
    </div>
  )}
  
  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
    {renderPortfolioChart()}
    {renderPortfolioDistribution()}
  </div>
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
                        Sell
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



    {/* Modalul de vânzare - aici este partea care lipsea */}
    {sellModalOpen && selectedHolding && (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-lg max-w-md w-full p-6">
          <h3 className="text-xl font-semibold mb-4">Sell holdings{selectedHolding.symbol}</h3>
          
          <div className="mb-4">
            <p>You own: <strong>{selectedHolding.quantity}</strong> acțiuni</p>
            <p>Purchase price:<strong>${selectedHolding.avg_buy_price.toFixed(2)}</strong></p>
            <p>Current price: <strong>${selectedHolding.current_price.toFixed(2)}</strong></p>
          </div>
          
          <div className="mb-4">
            <label className="block text-sm font-medium mb-1">Quantity to sell</label>
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
            <label className="block text-sm font-medium mb-1">Selling price</label>
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
              Total Value: ${(sellQuantity * sellPrice).toFixed(2)}
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
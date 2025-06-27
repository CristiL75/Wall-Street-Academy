import { useEffect, useState } from "react";
import axios from "axios";
import { getTokenPayload } from "../utils/auth";
import { Line } from "react-chartjs-2";



const TradePage = () => {
  const [userId, setUserId] = useState(null);
  const [companies, setCompanies] = useState([]);
  const [selectedCompany, setSelectedCompany] = useState(null);
  const [quantity, setQuantity] = useState(0);
  const [price, setPrice] = useState(null);
  const [feedback, setFeedback] = useState("");

  useEffect(() => {
    const payload = getTokenPayload();
    if (payload?.sub) {
      setUserId(payload.sub);
      checkUserPortfolio(payload.sub);
      fetchCompanies();
    }
  }, []);


  const checkUserPortfolio = async (userId) => {
  try {
    // First check if portfolio exists
    await axios.get(`http://127.0.0.1:8000/portfolios/${userId}`);
    console.log("Portfolio exists");
  } catch (err) {
    if (err.response && err.response.status === 404) {
      // Portfolio doesn't exist, create one
      try {
        const res = await axios.post(`http://127.0.0.1:8000/portfolios/`, {
          user_id: userId,
          cash: 100000 // Initial balance
        });
        console.log("Created portfolio:", res.data);
        setFeedback("Portofoliu creat cu un sold inițial de $100,000");
      } catch (createErr) {
        console.error("Failed to create portfolio:", createErr);
        setFeedback("❌ Eroare la crearea portofoliului");
      }
    }
  }
};

  const fetchCompanies = async () => {
    try {
        const res = await axios.get("http://127.0.0.1:8000/stocks/");

      console.log("Fetched companies raw response:", res.data);
      const data = Array.isArray(res.data) ? res.data : [];
      if (!Array.isArray(res.data)) {
        console.warn("/stocks response is not an array. Received:", res.data);
      }
      setCompanies(data);
      if (data.length > 0) {
        handleCompanyClick(data[0]);
      }
    } catch (err) {
      console.error("Error fetching companies:", err);
    }
  };
  

  const handleCompanyClick = async (company) => {
    setSelectedCompany(company);
    await fetchPrice(company.symbol);
 
  };

// Replace fetchPrice function with this version that doesn't need a dedicated endpoint
const fetchPrice = async (symbol) => {
  try {
    // Get all stocks and filter for the symbol we need
    const res = await axios.get("http://127.0.0.1:8000/stocks/");
    
    if (Array.isArray(res.data)) {
      const stock = res.data.find(s => s.symbol === symbol);
      
      if (stock) {
        // Extract price from the stock data
        if (stock.last_price) {
          setPrice(stock.last_price);
        } else if (stock.price) {
          setPrice(stock.price);
        } else {
          console.error("Price data not found in stock object:", stock);
          setPrice(null);
        }
      } else {
        console.error(`Stock with symbol ${symbol} not found in response`);
        setPrice(null);
      }
    } else {
      console.error("Invalid response format from /stocks/ endpoint:", res.data);
      setPrice(null);
    }
  } catch (err) {
    console.error("Error fetching price:", err);
    setPrice(null);
  }
};



const handleSubmit = async (e) => {
  e.preventDefault();
  if (!userId || quantity <= 0 || !selectedCompany || price === null) {
    setFeedback("❌ Eroare: Lipsesc informații necesare pentru tranzacție");
    return;
  }
  
  // Create payload with all required fields and ensure price is a number
  const payload = {
    user_id: userId,
    symbol: selectedCompany.symbol,
    quantity: Number(quantity),
    trade_type: "buy",
    order_type: "market",
    execution_price: Number(price), // Convert to number explicitly
    commission: 0,
  };
  
  console.log("Submitting trade with payload:", payload); 
  
  try {
    const response = await axios.post("http://127.0.0.1:8000/trades/", payload);
    console.log("Trade response:", response.data);
    setFeedback("✅ Tranzacție efectuată cu succes!");
    
    // Reset quantity after successful transaction
    setQuantity(0);
    
    // Actualizează portofoliul după tranzacție reușită
    try {
      // Așteaptă puțin pentru a permite backend-ului să proceseze tranzacția complet
      setTimeout(async () => {
        // Obținem portofoliul actualizat
        const portfolioRes = await axios.get(`http://127.0.0.1:8000/portfolios/${userId}`);
        console.log("Portfolio updated after trade:", portfolioRes.data);
        
        // Opțional: Poți seta un feedback suplimentar
        setFeedback(prev => `${prev} Portofoliul a fost actualizat.`);
      }, 1000); // Așteaptă 1 secundă
    } catch (refreshErr) {
      console.error("Failed to refresh portfolio data:", refreshErr);
    }
  }
  catch (err) {
    console.error("Trade failed:", err);
    
    if (err.response) {
      console.error("Error data:", err.response.data);
      console.error("Error status:", err.response.status);
      
      // Show more specific error message
      setFeedback(`❌ Eroare: ${err.response.data?.detail?.[0]?.msg || err.response.data?.detail || "Unknown error"}`);
    } else {
      setFeedback(`❌ Eroare la efectuarea tranzacției: ${err.message}`);
    }
  }
};

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-3xl font-semibold mb-5 text-gray-800 flex items-center">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-7 w-7 mr-2 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
          Trade Stocks
      </h1>
      <div className="overflow-x-auto whitespace-nowrap mb-4 py-2 flex space-x-2 border-b pb-2">
        {companies.map((comp) => (
          <button
            key={comp.symbol}
            onClick={() => handleCompanyClick(comp)}
            className={`px-4 py-2 rounded border text-sm shrink-0 transition ${
              selectedCompany?.symbol === comp.symbol ? "bg-blue-600 text-white" : "bg-gray-100 text-gray-800"
            }`}
          >
            {comp.name} ({comp.symbol})
          </button>
        ))}
      </div>

      {selectedCompany && (
        <div className="mb-6 p-4 bg-gray-50 border rounded">
          <h2 className="text-lg font-semibold mb-2">{selectedCompany.name} ({selectedCompany.symbol})</h2>
          {selectedCompany.description && <p className="text-sm text-gray-700 mb-2">{selectedCompany.description}</p>}
          {selectedCompany.sector && <p className="text-sm text-gray-600">Sector: {selectedCompany.sector}</p>}
          {selectedCompany.market_cap && <p className="text-sm text-gray-600">Market Cap: ${selectedCompany.market_cap}</p>}
        </div>
      )}

      {/* Price information card instead of chart */}
{price && (
  <div className="mb-6 p-6 bg-white border rounded-lg shadow-sm">
    <div className="flex flex-col items-center">
      <h3 className="text-lg font-medium text-gray-700 mb-2">Current Market Price</h3>
      <div className="text-3xl font-bold text-blue-600">${price}</div>
      <div className="mt-4 bg-blue-50 px-4 py-2 rounded-full">
        <span className="text-sm text-blue-700">Last updated: {new Date().toLocaleTimeString()}</span>
      </div>
    </div>
    
    <div className="grid grid-cols-2 gap-4 mt-6">
      <div className="bg-gray-50 p-3 rounded">
        <p className="text-sm text-gray-500">Market Hours</p>
        <p className="font-medium">9:30 AM - 4:00 PM ET</p>
      </div>
      <div className="bg-gray-50 p-3 rounded">
        <p className="text-sm text-gray-500">Currency</p>
        <p className="font-medium">USD ($)</p>
      </div>
    </div>
  </div>
)}

      <form onSubmit={handleSubmit} className="space-y-4">
        <input
          type="number"
          value={quantity}
          onChange={(e) => setQuantity(e.target.value)}
          placeholder="Cantitate"
          min={1}
          className="w-full border px-3 py-2 rounded"
          required
        />
        {price && <p className="text-gray-600 font-medium tracking-tight">Current Price: <span className="text-blue-700">${price}</span></p>}
        <button className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
              Execute Trade
        </button>
        {feedback && <p className="text-sm mt-2">{feedback}</p>}
      </form>
    </div>
  );
};

export default TradePage;

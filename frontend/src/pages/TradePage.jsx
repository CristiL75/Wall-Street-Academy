import { useEffect, useState } from "react";
import axios from "axios";
import { getTokenPayload } from "../utils/auth";
import { Line } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  LineElement,
  PointElement,
  Tooltip,
  Legend
} from "chart.js";

ChartJS.register(CategoryScale, LinearScale, LineElement, PointElement, Tooltip, Legend);

const TradePage = () => {
  const [userId, setUserId] = useState(null);
  const [companies, setCompanies] = useState([]);
  const [selectedCompany, setSelectedCompany] = useState(null);
  const [quantity, setQuantity] = useState(0);
  const [price, setPrice] = useState(null);
  const [chartData, setChartData] = useState(null);
  const [feedback, setFeedback] = useState("");

  useEffect(() => {
    const payload = getTokenPayload();
    if (payload?.sub) {
      setUserId(payload.sub);
      fetchCompanies();
    }
  }, []);

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
    await fetchChart(company.symbol);
  };

  const fetchPrice = async (symbol) => {
    try {
      const res = await axios.get(`/price/${symbol}`);
      setPrice(res.data.price);
    } catch (err) {
      console.error("Error fetching price:", err);
      setPrice(null);
    }
  };

  const fetchChart = async (symbol) => {
    try {
      const res = await axios.get(`/api/chart/${symbol}`);
      const { labels, values } = res.data;
      setChartData({
        labels,
        datasets: [
          {
            label: `${symbol} Price Evolution`,
            data: values,
            fill: false,
            borderColor: "rgb(75, 192, 192)",
            tension: 0.1
          }
        ]
      });
    } catch (err) {
      console.error("Chart load error:", err);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!userId || quantity <= 0 || !selectedCompany) return;
    try {
      await axios.post("/trades/", {
        user_id: userId,
        symbol: selectedCompany.symbol,
        quantity: Number(quantity),
        trade_type: "buy",
        order_type: "market",
        execution_price: price,
        commission: 0,
      });
      setFeedback("✅ Tranzacție efectuată cu succes!");
    } catch (err) {
      console.error("Trade failed:", err);
      setFeedback("❌ Eroare la efectuarea tranzacției.");
    }
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">📈 Tranzacționează acțiuni</h1>

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

      {chartData && (
        <div className="mb-6">
          <Line data={chartData} />
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
        {price && <p className="text-gray-600">Preț curent: ${price}</p>}
        <button className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
          Execută Tranzacția
        </button>
        {feedback && <p className="text-sm mt-2">{feedback}</p>}
      </form>
    </div>
  );
};

export default TradePage;

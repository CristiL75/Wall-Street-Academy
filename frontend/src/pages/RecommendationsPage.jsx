import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { getTokenPayload } from '../utils/auth';
import { API_URL } from '../config';

const RecommendationsPage = () => {
  const [userId, setUserId] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [marketOverview, setMarketOverview] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedRecommendation, setSelectedRecommendation] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [recommendationDetails, setRecommendationDetails] = useState(null);
  
  const navigate = useNavigate();

  useEffect(() => {
    const checkAuth = () => {
      const payload = getTokenPayload();
      if (!payload || !payload.sub) {
        navigate('/login');
        return;
      }
      setUserId(payload.sub);
    };

    checkAuth();
  }, [navigate]);

  useEffect(() => {
    if (!userId) return;
    


const fetchRecommendations = async () => {
  try {
    setLoading(true);
    
  
    const response = await axios.get(`${API_URL}/recommendations/${userId}`);
    
    console.log('Market overview data:', response.data.market_overview);
    
    setRecommendations(response.data.recommendations || []);
    setMarketOverview(response.data.market_overview || null);
    
  } catch (err) {
    console.error('Error fetching recommendations:', err);
    setError('Failed to load recommendations. Please try again later.');
  } finally {
    setLoading(false);
  }
};

    fetchRecommendations();
  }, [userId]);

  const fetchRecommendationDetail = async (symbol) => {
    if (!userId) return;
    
    try {
      setDetailLoading(true);
      setSelectedRecommendation(symbol);
      
      const response = await axios.get(`${API_URL}/recommendations/${userId}/detail/${symbol}`);
      setRecommendationDetails(response.data);
      
    } catch (err) {
      console.error(`Error fetching details for ${symbol}:`, err);
      setError(`Failed to load details for ${symbol}.`);
    } finally {
      setDetailLoading(false);
    }
  };

  const handleTradeClick = (symbol) => {
    navigate(`/trade?symbol=${symbol}`);
  };

  const getConfidenceColor = (confidence) => {
    if (confidence >= 75) return 'bg-green-600';
    if (confidence >= 50) return 'bg-blue-600';
    if (confidence >= 25) return 'bg-yellow-600';
    return 'bg-gray-600';
  };

  const getPerformanceColor = (value) => {
    if (value > 3) return 'text-green-600';
    if (value >= 0) return 'text-green-500';
    if (value >= -3) return 'text-red-500';
    return 'text-red-600';
  };

  const getConsensusColor = (consensus) => {
    if (consensus === 'bullish') return 'text-green-600';
    if (consensus === 'bearish') return 'text-red-600';
    return 'text-gray-600';
  };

  const getSourceBadge = (source) => {
    const sourceColors = {
      'collaborative': 'bg-purple-100 text-purple-800',
      'content': 'bg-blue-100 text-blue-800',
      'technical': 'bg-green-100 text-green-800',
      'risk': 'bg-yellow-100 text-yellow-800',
      'diversification': 'bg-indigo-100 text-indigo-800',
    };
    
    return sourceColors[source] || 'bg-gray-100 text-gray-800';
  };

  const renderMarketOverview = () => {
    if (!marketOverview) return null;

    return (
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-xl font-bold mb-4">Market Overview</h2>
        <div className="flex items-center mb-4">
          <div 
            className={`w-3 h-3 rounded-full mr-2 ${
              marketOverview.trend === 'bullish' ? 'bg-green-500' : 'bg-red-500'
            }`}
          />
          <span className="text-lg font-medium capitalize">
            {marketOverview.trend} Market
          </span>
        </div>
        


{marketOverview.top_sectors && marketOverview.top_sectors.length > 0 && (
  <div>
    <h3 className="text-sm font-medium text-gray-500 mb-2">Top Performing Sectors</h3>
    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2">
      {marketOverview.top_sectors.map((sector, idx) => {
        const sectorName = sector.name || sector;
        const performance = sector.performance !== undefined ? Number(sector.performance) : null;
        const isPositive = performance !== null ? performance >= 0 : null;
        
        return (
          <div 
            key={idx} 
            className={`px-3 py-2 ${isPositive === null ? 'bg-gray-50' : isPositive ? 'bg-green-50' : 'bg-red-50'} 
                        rounded-md text-sm flex justify-between items-center`}
          >
            <span className="font-medium">{sectorName}</span>
            {performance !== null && (
              <span className={`font-bold ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
                {isPositive ? '+' : ''}{performance}%
              </span>
            )}
          </div>
        );
      })}
    </div>
  </div>
)}
      </div>
    );
  };

  const renderRecommendationsList = () => {
    if (loading) {
      return (
        <div className="flex justify-center my-8">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
        </div>
      );
    }

    if (error) {
      return (
        <div className="bg-red-50 border-l-4 border-red-500 p-4 mb-6">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-500" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          </div>
        </div>
      );
    }

    if (recommendations.length === 0) {
      return (
        <div className="bg-white rounded-lg shadow-md p-8 text-center">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <h3 className="mt-2 text-lg font-medium text-gray-900">No recommendations found</h3>
          <p className="mt-1 text-sm text-gray-500">
            We don't have personalized recommendations for you yet.
            <br />Try to make some trades first to help our AI understand your preferences.
          </p>
        </div>
      );
    }

    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {recommendations.map((rec) => (
          <div 
            key={rec.symbol}
            className={`bg-white rounded-lg shadow-md overflow-hidden transition-shadow hover:shadow-lg ${
              selectedRecommendation === rec.symbol ? 'ring-2 ring-blue-500' : ''
            }`}
            onClick={() => fetchRecommendationDetail(rec.symbol)}
          >
            <div className={`p-1 ${getConfidenceColor(rec.confidence)}`}></div>
            <div className="p-5">
              <div className="flex justify-between items-start mb-3">
                <div>
                  <h3 className="text-xl font-bold">{rec.symbol}</h3>
                  <p className="text-sm text-gray-600">{rec.details?.name}</p>
                </div>
                <div className="flex items-center">
                  <div className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-blue-100 text-blue-800">
                    {rec.details?.sector}
                  </div>
                </div>
              </div>
              
              <div className="mb-3">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Current Price</span>
                  <span className="font-medium">${rec.details?.last_price}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Market Cap</span>
                  <span className="font-medium">{rec.details?.market_cap_formatted}</span>
                </div>
              </div>
              
              {rec.details?.performance && (
                <div className="mb-3">
                  <p className="text-xs text-gray-500 mb-1">Performance</p>
                  <div className="flex justify-between text-sm">
                    <span>1 Month</span>
                    <span className={getPerformanceColor(rec.details.performance["1_month"])}>
                      {rec.details.performance["1_month"].toFixed(2)}%
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>3 Months</span>
                    <span className={getPerformanceColor(rec.details.performance["3_month"])}>
                      {rec.details.performance["3_month"].toFixed(2)}%
                    </span>
                  </div>
                </div>
              )}
              
              <div className="flex justify-between items-center mt-4">
                <div>
                  <div className="text-xs text-gray-500 mb-1">AI Confidence</div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className={`${getConfidenceColor(rec.confidence)} h-2 rounded-full`}
                      style={{ width: `${rec.confidence}%` }}
                    ></div>
                  </div>
                </div>
                <button 
                  onClick={(e) => {
                    e.stopPropagation();
                    handleTradeClick(rec.symbol);
                  }}
                  className="ml-3 bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700 transition"
                >
                  Trade
                </button>
              </div>
              
              <div className="mt-4 pt-4 border-t border-gray-100">
                <p className="text-xs text-gray-500 mb-1.5">Recommended by</p>
                <div className="flex flex-wrap gap-2">
                  {rec.sources.map((source, idx) => (
                    <span 
                      key={idx}
                      className={`text-xs px-2 py-0.5 rounded ${getSourceBadge(source)}`}
                    >
                      {source}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  };

  const renderRecommendationDetail = () => {
    if (!selectedRecommendation) return null;
    
    if (detailLoading) {
      return (
        <div className="bg-white rounded-lg shadow-md p-6 mt-6">
          <div className="flex justify-center my-8">
            <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500"></div>
          </div>
        </div>
      );
    }
    
    if (!recommendationDetails) return null;
    
    const details = recommendationDetails;
    
    return (
      <div className="bg-white rounded-lg shadow-md p-6 mt-6">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h2 className="text-2xl font-bold">{details.symbol}</h2>
            <p className="text-gray-600">{details.name}</p>
          </div>
          
          <div className="flex gap-2">
            <div className="text-sm font-medium px-2.5 py-0.5 rounded-full bg-blue-100 text-blue-800">
              {details.sector}
            </div>
            <div className={`text-sm font-medium px-2.5 py-0.5 rounded-full 
              ${details.consensus.direction === 'bullish' 
                ? 'bg-green-100 text-green-800' 
                : details.consensus.direction === 'bearish' 
                ? 'bg-red-100 text-red-800' 
                : 'bg-gray-100 text-gray-800'}`}
            >
              {details.consensus.direction.charAt(0).toUpperCase() + details.consensus.direction.slice(1)} ({details.consensus.strength}/10)
            </div>
          </div>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <div className="space-y-4">
            <div className="bg-gray-50 rounded-lg p-4">
              <h3 className="text-lg font-medium mb-2">Price Information</h3>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div className="text-gray-600">Current Price</div>
                <div className="font-medium text-right">${details.current_price.toFixed(2)}</div>
                
                <div className="text-gray-600">Market Cap</div>
                <div className="font-medium text-right">{details.market_cap_formatted}</div>
                
                {details.currently_owned && (
                  <>
                    <div className="text-gray-600">Your Position</div>
                    <div className="font-medium text-right">{details.holding_details.quantity} shares</div>
                    
                    <div className="text-gray-600">Average Cost</div>
                    <div className="font-medium text-right">${details.holding_details.avg_buy_price.toFixed(2)}</div>
                    
                    <div className="text-gray-600">P&L</div>
                    <div className={`font-medium text-right ${details.holding_details.profit_loss >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      ${details.holding_details.profit_loss.toFixed(2)} 
                      ({((details.holding_details.profit_loss / (details.holding_details.avg_buy_price * details.holding_details.quantity)) * 100).toFixed(2)}%)
                    </div>
                  </>
                )}
              </div>
            </div>
            
            <div className="bg-gray-50 rounded-lg p-4">
              <h3 className="text-lg font-medium mb-2">Performance</h3>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div className="text-gray-600">1 Week</div>
                <div className={`font-medium text-right ${getPerformanceColor(details.performance["1_week"])}`}>
                  {details.performance["1_week"].toFixed(2)}%
                </div>
                
                <div className="text-gray-600">1 Month</div>
                <div className={`font-medium text-right ${getPerformanceColor(details.performance["1_month"])}`}>
                  {details.performance["1_month"].toFixed(2)}%
                </div>
                
                <div className="text-gray-600">3 Months</div>
                <div className={`font-medium text-right ${getPerformanceColor(details.performance["3_month"])}`}>
                  {details.performance["3_month"].toFixed(2)}%
                </div>
                
                <div className="text-gray-600">6 Months</div>
                <div className={`font-medium text-right ${getPerformanceColor(details.performance["6_month"])}`}>
                  {details.performance["6_month"].toFixed(2)}%
                </div>
              </div>
            </div>
            
          </div>
          
          <div>
            <div className="bg-gray-50 rounded-lg p-4 mb-4">
              <h3 className="text-lg font-medium mb-2">Technical Indicators</h3>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div className="text-gray-600">RSI (14)</div>
                <div className={`font-medium text-right ${
                  details.technical.rsi < 30 ? 'text-green-600' : 
                  details.technical.rsi > 70 ? 'text-red-600' : 
                  'text-gray-800'
                }`}>
                  {details.technical.rsi.toFixed(2)}
                </div>
                
                <div className="text-gray-600">MACD</div>
                <div className={`font-medium text-right ${
                  details.technical.macd > details.technical.macd_signal ? 'text-green-600' : 'text-red-600'
                }`}>
                  {details.technical.macd.toFixed(4)}
                </div>
                
                <div className="text-gray-600">SMA20</div>
                <div className="font-medium text-right">${details.technical.sma20.toFixed(2)}</div>
                
                <div className="text-gray-600">SMA50</div>
                <div className="font-medium text-right">${details.technical.sma50.toFixed(2)}</div>
                
                <div className="text-gray-600">Volatility</div>
                <div className="font-medium text-right">{details.technical.volatility.toFixed(2)}%</div>
              </div>
            </div>
            
            <div className="bg-gray-50 rounded-lg p-4">
              <h3 className="text-lg font-medium mb-2">Risk/Reward</h3>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div className="text-gray-600">Potential Support</div>
                <div className="font-medium text-right">${details.risk_reward.support}</div>
                
                <div className="text-gray-600">Potential Resistance</div>
                <div className="font-medium text-right">${details.risk_reward.resistance}</div>
                
                <div className="text-gray-600">Stop Loss Level</div>
                <div className="font-medium text-right">${details.risk_reward.stop_loss} ({details.risk_reward.risk_percent}%)</div>
                
                <div className="text-gray-600">Target Price</div>
                <div className="font-medium text-right">${details.risk_reward.target} ({details.risk_reward.reward_percent}%)</div>
                
                <div className="text-gray-600">Risk/Reward Ratio</div>
                <div className={`font-medium text-right ${
                  details.risk_reward.ratio >= 2 ? 'text-green-600' : 
                  details.risk_reward.ratio >= 1 ? 'text-blue-600' : 
                  'text-red-600'
                }`}>
                  {details.risk_reward.ratio}:1
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <div className="bg-gray-50 rounded-lg p-4 mb-6">
          <h3 className="text-lg font-medium mb-2">Technical Signals</h3>
          <div className="space-y-2">
            {details.signals.map((signal, idx) => (
              <div 
                key={idx}
                className={`flex items-center p-2 rounded ${
                  signal.type === 'bullish' ? 'bg-green-50' : 
                  signal.type === 'bearish' ? 'bg-red-50' : 
                  'bg-gray-100'
                }`}
              >
                <div className={`w-2 h-2 rounded-full mr-2 ${
                  signal.type === 'bullish' ? 'bg-green-600' : 
                  signal.type === 'bearish' ? 'bg-red-600' : 
                  'bg-gray-600'
                }`}></div>
                <span className={`text-sm ${
                  signal.type === 'bullish' ? 'text-green-800' : 
                  signal.type === 'bearish' ? 'text-red-800' : 
                  'text-gray-800'
                }`}>
                  {signal.message}
                </span>
                <div className="ml-auto">
                  {Array(signal.strength).fill(0).map((_, i) => (
                    <span key={i} className="inline-block w-1.5 h-1.5 mx-px rounded-full bg-current"></span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
        
        <div className="mb-6">
          <h3 className="text-lg font-medium mb-2">Investment Thesis</h3>
          <div className="bg-white border border-gray-200 rounded-lg p-4 whitespace-pre-line text-sm text-gray-800">
            {details.thesis.split('\n').map((paragraph, idx) => (
              <p key={idx} className={`mb-2 ${paragraph.startsWith('**') ? 'font-bold' : ''}`}>
                {paragraph.replace(/\*\*/g, '')}
              </p>
            ))}
          </div>
        </div>
        
        <div className="flex justify-end mt-6">
          <button
            onClick={() => handleTradeClick(details.symbol)}
            className="bg-blue-600 text-white px-6 py-2 rounded font-medium hover:bg-blue-700 transition"
          >
            Trade {details.symbol}
          </button>
        </div>
      </div>
    );
  };

  return (
    <div className="p-4 md:p-6 max-w-7xl mx-auto">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-800 mb-2">AI Trading Recommendations</h1>
        <p className="text-gray-600">
          Personalized stock recommendations based on market analysis, technical indicators, and your trading history.
        </p>
      </div>

      {renderMarketOverview()}
      {renderRecommendationsList()}
      {renderRecommendationDetail()}
    </div>
  );
};

export default RecommendationsPage;
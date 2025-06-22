import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API_URL } from '../config';

const NewsPage = () => {
  const [news, setNews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [tickerFilter, setTickerFilter] = useState('');
  const [submittedTicker, setSubmittedTicker] = useState('');

useEffect(() => {
  const fetchNews = async () => {
    try {
      setLoading(true);
      // Log explicit pentru debugging
      const endpoint = submittedTicker 
        ? `${API_URL}/news/by-ticker/${submittedTicker}` 
        : `${API_URL}/news/all`;
      
      console.log("Trying to fetch from:", endpoint);
      
      const response = await axios.get(endpoint);
      console.log("Response:", response);
      setNews(response.data);
      setLoading(false);
    } catch (err) {
      console.error('Error fetching news:', err);
      setError('Failed to load news. Please try again later.');
      setLoading(false);
    }
  };

  fetchNews();
}, [submittedTicker]);

  const handleSubmit = (e) => {
    e.preventDefault();
    setSubmittedTicker(tickerFilter);
  };

 // Actualizează funcția formatDate pentru a gestiona mai bine datele

const formatDate = (timestamp) => {
  if (!timestamp) return 'Recent';
  
  try {
    // Verifică dacă timestamp-ul este valid
    const date = new Date(timestamp * 1000); // Convertește din secunde în milisecunde
    
    // Verifică dacă data este validă
    if (isNaN(date.getTime())) {
      // Încearcă cu timestamp-ul ca atare (poate fi deja în milisecunde)
      const dateMs = new Date(timestamp);
      if (isNaN(dateMs.getTime())) {
        return 'Recent'; // Dacă tot nu e valid, arată "Recent"
      }
      return dateMs.toLocaleDateString() + ' ' + dateMs.toLocaleTimeString();
    }
    
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
  } catch (e) {
    console.error('Error formatting date:', e);
    return 'Recent';
  }
};

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-6">Financial News</h1>
      
      {/* Filter form */}
      <form onSubmit={handleSubmit} className="mb-6">
        <div className="flex">
          <input
            type="text"
            value={tickerFilter}
            onChange={(e) => setTickerFilter(e.target.value.toUpperCase())}
            placeholder="Enter ticker symbol (e.g., AAPL, MSFT)"
            className="px-4 py-2 border border-gray-300 rounded-l w-full"
          />
          <button
            type="submit"
            className="bg-blue-600 text-white px-4 py-2 rounded-r hover:bg-blue-700"
          >
            Search
          </button>
        </div>
        {submittedTicker && (
          <p className="mt-2">
            Showing news for: <strong>{submittedTicker}</strong>
            <button
              onClick={() => {
                setTickerFilter('');
                setSubmittedTicker('');
              }}
              className="ml-2 text-sm text-blue-600 hover:underline"
            >
              Clear filter
            </button>
          </p>
        )}
      </form>
      
      {loading && (
        <div className="flex justify-center my-8">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
        </div>
      )}
      
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {news.map((item, index) => (
          <div key={index} className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow">
            {item.thumbnail?.resolutions?.[0]?.url && (
              <img 
                src={item.thumbnail.resolutions[0].url} 
                alt={item.title} 
                className="w-full h-48 object-cover"
              />
            )}
            <div className="p-4">
              <h2 className="text-lg font-semibold mb-2">{item.title}</h2>
              <p className="text-sm text-gray-600 mb-2">Publisher: {item.publisher}</p>
              
              {item.relatedTickers && item.relatedTickers.length > 0 && (
                <div className="mb-3">
                  <p className="text-xs text-gray-500">Related: 
                    {item.relatedTickers.map((ticker, i) => (
                      <button
                        key={i}
                        className="ml-1 bg-gray-100 px-1 py-0.5 rounded hover:bg-gray-200"
                        onClick={() => {
                          setTickerFilter(ticker);
                          setSubmittedTicker(ticker);
                        }}
                      >
                        {ticker}
                      </button>
                    ))}
                  </p>
                </div>
              )}
              
              <div className="flex justify-between items-center">
                <span className="text-xs text-gray-500">
                  {formatDate(item.providerPublishTime)}
                </span>
                <a 
                  href={item.link} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:text-blue-800 text-sm"
                >
                  Read more →
                </a>
              </div>
            </div>
          </div>
        ))}
      </div>

      {!loading && news.length === 0 && !error && (
        <p className="text-center text-gray-500 my-8">No news articles available.</p>
      )}
    </div>
  );
};

export default NewsPage;
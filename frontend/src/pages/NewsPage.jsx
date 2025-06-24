import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API_URL } from '../config';

const NewsPage = () => {
  const [news, setNews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [tickerFilter, setTickerFilter] = useState('');
  const [submittedTicker, setSubmittedTicker] = useState('');
  const [displayMode, setDisplayMode] = useState('cards'); // 'cards' sau 'list'

  useEffect(() => {
    const fetchNews = async () => {
      try {
        setLoading(true);
        const endpoint = submittedTicker 
          ? `${API_URL}/news/by-ticker/${submittedTicker}` 
          : `${API_URL}/news/all`;
        
        console.log("Fetching from:", endpoint);
        
        const response = await axios.get(endpoint);
        
        if (response.data && response.data.length) {
          // Sortăm știrile după dată (cele mai recente primele)
          const sortedNews = [...response.data].sort((a, b) => 
            (b.providerPublishTime || 0) - (a.providerPublishTime || 0)
          );
          
          setNews(sortedNews);
        } else {
          setNews([]);
        }
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

  // Funcție îmbunătățită pentru formatarea datei, cu aspect mai prietenos
  const formatDate = (timestamp) => {
    if (!timestamp) return 'Recent';
    
    try {
      // Încearcă să convertească timestamp-ul
      const date = new Date(timestamp * 1000);
      
      // Verifică dacă data este validă
      if (isNaN(date.getTime())) {
        // Încearcă ca timestamp în milisecunde
        const dateMs = new Date(parseInt(timestamp));
        if (!isNaN(dateMs.getTime())) {
          return formatRelativeTime(dateMs);
        }
        
        // Încearcă ca string ISO
        const dateIso = new Date(timestamp);
        if (!isNaN(dateIso.getTime())) {
          return formatRelativeTime(dateIso);
        }
        
        return 'Recent';
      }
      
      return formatRelativeTime(date);
    } catch (e) {
      console.error('Error formatting date:', e);
      return 'Recent';
    }
  };
  
  // Formatarea timpului relativ (ex: "2 hours ago", "Yesterday", etc.)
  const formatRelativeTime = (date) => {
    const now = new Date();
    const diffMs = now - date;
    const diffSec = Math.floor(diffMs / 1000);
    const diffMin = Math.floor(diffSec / 60);
    const diffHour = Math.floor(diffMin / 60);
    const diffDay = Math.floor(diffHour / 24);
    
    if (diffSec < 60) {
      return 'Just now';
    } else if (diffMin < 60) {
      return `${diffMin} minute${diffMin > 1 ? 's' : ''} ago`;
    } else if (diffHour < 24) {
      return `${diffHour} hour${diffHour > 1 ? 's' : ''} ago`;
    } else if (diffDay === 1) {
      return 'Yesterday';
    } else if (diffDay < 7) {
      return `${diffDay} days ago`;
    } else {
      return date.toLocaleDateString();
    }
  };
  
  // Extragem ticker-ele unice pentru filtrul rapid
  const getUniqueTickers = () => {
    if (!news || news.length === 0) return [];
    
    const allTickers = news.flatMap(item => 
      item.relatedTickers ? item.relatedTickers : []
    );
    
    return [...new Set(allTickers)].slice(0, 10); // Primele 10 ticker-e unice
  };
  
  // Randează headerul principal al paginii
  const renderHeader = () => (
    <div className="mb-8">
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-3xl font-bold text-gray-800">
          {submittedTicker ? `${submittedTicker} News` : 'Market News'}
        </h1>
        
        <div className="flex space-x-2">
          <button 
            onClick={() => setDisplayMode('cards')}
            className={`p-2 rounded ${displayMode === 'cards' 
              ? 'bg-blue-600 text-white' 
              : 'bg-gray-200 text-gray-700'}`}
            aria-label="Card view"
          >
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
              <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 18v-2.25zM13.5 6a2.25 2.25 0 012.25-2.25H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25a2.25 2.25 0 01-2.25-2.25V6zM13.5 15.75a2.25 2.25 0 012.25-2.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-2.25A2.25 2.25 0 0113.5 18v-2.25z" />
            </svg>
          </button>
          <button 
            onClick={() => setDisplayMode('list')}
            className={`p-2 rounded ${displayMode === 'list' 
              ? 'bg-blue-600 text-white' 
              : 'bg-gray-200 text-gray-700'}`}
            aria-label="List view"
          >
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
              <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 6.75h12M8.25 12h12m-12 5.25h12M3.75 6.75h.007v.008H3.75V6.75zm.375 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zM3.75 12h.007v.008H3.75V12zm.375 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm-.375 5.25h.007v.008H3.75v-.008zm.375 0a.375.375 0 11-.75 0 .375.375 0 01.75 0z" />
            </svg>
          </button>
        </div>
      </div>
      
      <form onSubmit={handleSubmit} className="mb-6">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex flex-1 shadow-sm rounded-lg overflow-hidden">
            <div className="bg-gray-100 px-3 flex items-center justify-center rounded-l">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5 text-gray-500">
                <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
              </svg>
            </div>
            <input
              type="text"
              value={tickerFilter}
              onChange={(e) => setTickerFilter(e.target.value.toUpperCase())}
              placeholder="Search by ticker symbol (e.g., AAPL, MSFT)"
              className="px-4 py-3 flex-1 border-none focus:outline-none focus:ring-0"
            />
          </div>
          <button
            type="submit"
            className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors flex items-center justify-center font-medium"
          >
            Search News
          </button>
        </div>

        {/* Filtre rapide */}
        {!submittedTicker && getUniqueTickers().length > 0 && (
          <div className="mt-4 flex flex-wrap gap-2">
            <span className="text-sm text-gray-500 self-center">Popular symbols:</span>
            {getUniqueTickers().map(ticker => (
              <button
                key={ticker}
                onClick={() => {
                  setTickerFilter(ticker);
                  setSubmittedTicker(ticker);
                }}
                className="bg-gray-100 hover:bg-gray-200 text-gray-800 px-2 py-1 rounded text-sm transition-colors"
              >
                {ticker}
              </button>
            ))}
          </div>
        )}
        
        {submittedTicker && (
          <div className="mt-4 flex items-center">
            <span className="bg-blue-100 text-blue-800 text-sm font-medium px-3 py-1 rounded-full">
              {submittedTicker}
            </span>
            <button
              type="button"
              onClick={() => {
                setTickerFilter('');
                setSubmittedTicker('');
              }}
              className="ml-2 text-sm text-gray-500 hover:text-gray-800"
              aria-label="Clear filter"
            >
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-4 h-4">
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        )}
      </form>
    </div>
  );

  // Randează lista de știri în funcție de modul de afișare
  const renderNewsItems = () => {
    if (loading) {
      return (
        <div className="flex justify-center my-12">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
        </div>
      );
    }
    
    if (error) {
      return (
        <div className="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 mb-6 rounded">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-500" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm">{error}</p>
            </div>
          </div>
        </div>
      );
    }
    
    if (!news.length) {
      return (
        <div className="text-center py-12 bg-white rounded-lg shadow">
          <div className="rounded-full bg-blue-50 p-3 mx-auto w-16 h-16 flex items-center justify-center">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-8 h-8 text-blue-500">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
            </svg>
          </div>
          <h3 className="mt-4 text-lg font-medium text-gray-900">No news found</h3>
          <p className="mt-2 text-sm text-gray-500">
            {submittedTicker ? `No news articles available for ${submittedTicker}.` : 'No news articles available at the moment.'}
          </p>
          {submittedTicker && (
            <div className="mt-6">
              <button
                type="button"
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700"
                onClick={() => {
                  setTickerFilter('');
                  setSubmittedTicker('');
                }}
              >
                View all news
              </button>
            </div>
          )}
        </div>
      );
    }

    if (displayMode === 'cards') {
      return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {news.map((item, index) => (
            <div key={item.id || index} 
              className="bg-white rounded-lg shadow-sm hover:shadow-md transition-all duration-300 border border-gray-100 flex flex-col">
              
              {/* Icon header instead of image */}
              <div className="bg-blue-50 px-4 py-3 rounded-t-lg flex justify-between items-center">
                <div className="flex items-center">
                  <div className="rounded-full bg-blue-100 p-1.5 mr-2">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-4 h-4 text-blue-700">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M12 7.5h1.5m-1.5 3h1.5m-7.5 3h7.5m-7.5 3h7.5m3-9h3.375c.621 0 1.125.504 1.125 1.125V18a2.25 2.25 0 01-2.25 2.25M16.5 7.5V18a2.25 2.25 0 002.25 2.25M16.5 7.5V4.875c0-.621-.504-1.125-1.125-1.125H4.125C3.504 3.75 3 4.254 3 4.875V18a2.25 2.25 0 002.25 2.25h13.5M6 7.5h3v3H6v-3z" />
                    </svg>
                  </div>
                  <span className="text-xs font-medium text-blue-800">
                    {item.publisher || "Financial News"}
                  </span>
                </div>
                
                <span className="text-xs text-blue-700">
                  {formatDate(item.providerPublishTime)}
                </span>
              </div>
              
              <div className="p-5 flex-1 flex flex-col">
                <h2 className="text-lg font-semibold mb-3 line-clamp-3 flex-grow">{item.title}</h2>
                
                {item.relatedTickers && item.relatedTickers.length > 0 && (
                  <div className="flex flex-wrap gap-1 mb-3">
                    {item.relatedTickers.slice(0, 6).map((ticker, i) => (
                      <button
                        key={i}
                        className="bg-gray-50 hover:bg-gray-100 text-gray-700 px-2 py-0.5 rounded text-xs transition-colors"
                        onClick={() => {
                          setTickerFilter(ticker);
                          setSubmittedTicker(ticker);
                        }}
                      >
                        {ticker}
                      </button>
                    ))}
                    {item.relatedTickers.length > 6 && (
                      <span className="text-xs text-gray-500">+{item.relatedTickers.length - 6} more</span>
                    )}
                  </div>
                )}
                
                <div className="mt-auto pt-4 border-t border-gray-100">
                  <a 
                    href={item.link} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:text-blue-800 text-sm font-medium flex items-center justify-end"
                  >
                    Read article
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-4 h-4 ml-1">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 6H5.25A2.25 2.25 0 003 8.25v10.5A2.25 2.25 0 005.25 21h10.5A2.25 2.25 0 0018 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" />
                    </svg>
                  </a>
                </div>
              </div>
            </div>
          ))}
        </div>
      );
    } else {
      // List view
      return (
        <div className="space-y-4">
          {news.map((item, index) => (
            <div key={item.id || index} className="bg-white rounded-lg shadow-sm hover:shadow-md transition-all duration-300 flex">
              {/* Icon column instead of image */}
              <div className="bg-blue-50 w-16 md:w-20 flex-shrink-0 flex items-center justify-center rounded-l-lg">
                <div className="rounded-full bg-blue-100 p-2">
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6 text-blue-700">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                  </svg>
                </div>
              </div>
              
              <div className="p-4 flex-1">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-blue-50 text-blue-700">
                    {item.publisher || "Financial News"}
                  </span>
                  <span className="text-xs text-gray-500">
                    {formatDate(item.providerPublishTime)}
                  </span>
                </div>
                
                <h2 className="text-base font-semibold mb-2">{item.title}</h2>
                
                <div className="flex flex-wrap items-center justify-between">
                  <div className="flex flex-wrap gap-1">
                    {item.relatedTickers && item.relatedTickers.slice(0, 4).map((ticker, i) => (
                      <button
                        key={i}
                        className="bg-gray-50 hover:bg-gray-100 text-gray-700 px-1.5 py-0.5 rounded text-xs transition-colors"
                        onClick={() => {
                          setTickerFilter(ticker);
                          setSubmittedTicker(ticker);
                        }}
                      >
                        {ticker}
                      </button>
                    ))}
                    {item.relatedTickers && item.relatedTickers.length > 4 && (
                      <span className="text-xs text-gray-500">+{item.relatedTickers.length - 4}</span>
                    )}
                  </div>
                  
                  <a 
                    href={item.link} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:text-blue-800 text-xs font-medium flex items-center"
                  >
                    Read article
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-3 h-3 ml-1">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
                    </svg>
                  </a>
                </div>
              </div>
            </div>
          ))}
        </div>
      );
    }
  };

  // Featured News Section - With a nice summary instead of an image
  const renderFeaturedNews = () => {
    if (!news.length || submittedTicker) return null;
    
    const featuredItem = news[0]; // Get the first news item as featured
    
    return (
      <div className="mb-8 bg-gradient-to-r from-blue-50 to-white rounded-xl shadow-sm overflow-hidden hover:shadow-md transition-shadow border border-blue-100">
        <div className="p-6">
          <div className="flex justify-between items-center mb-2">
            <div className="uppercase tracking-wide text-xs font-bold text-blue-600 flex items-center">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-4 h-4 mr-1">
                <path strokeLinecap="round" strokeLinejoin="round" d="M11.48 3.499a.562.562 0 011.04 0l2.125 5.111a.563.563 0 00.475.345l5.518.442c.499.04.701.663.321.988l-4.204 3.602a.563.563 0 00-.182.557l1.285 5.385a.562.562 0 01-.84.61l-4.725-2.885a.563.563 0 00-.586 0L6.982 20.54a.562.562 0 01-.84-.61l1.285-5.386a.562.562 0 00-.182-.557l-4.204-3.602a.563.563 0 01.321-.988l5.518-.442a.563.563 0 00.475-.345L11.48 3.5z" />
              </svg>
              Featured Story
            </div>
            <span className="text-xs text-gray-500">
              {formatDate(featuredItem.providerPublishTime)}
            </span>
          </div>
          
          <h2 className="text-2xl font-semibold mb-3 text-gray-800">
            {featuredItem.title}
          </h2>
          
          <div className="flex justify-between items-center mb-4">
            <span className="flex items-center text-sm text-gray-600">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-4 h-4 mr-1">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 7.5h1.5m-1.5 3h1.5m-7.5 3h7.5m-7.5 3h7.5m3-9h3.375c.621 0 1.125.504 1.125 1.125V18a2.25 2.25 0 01-2.25 2.25M16.5 7.5V18a2.25 2.25 0 002.25 2.25M16.5 7.5V4.875c0-.621-.504-1.125-1.125-1.125H4.125C3.504 3.75 3 4.254 3 4.875V18a2.25 2.25 0 002.25 2.25h13.5M6 7.5h3v3H6v-3z" />
              </svg>
              {featuredItem.publisher || "Financial News"}
            </span>
          </div>
          
          {featuredItem.relatedTickers && featuredItem.relatedTickers.length > 0 && (
            <div className="flex flex-wrap gap-1 mb-5">
              {featuredItem.relatedTickers.map((ticker, i) => (
                <button
                  key={i}
                  className="bg-white hover:bg-gray-100 text-gray-800 px-2 py-1 rounded-md text-sm border border-gray-200 transition-colors"
                  onClick={() => {
                    setTickerFilter(ticker);
                    setSubmittedTicker(ticker);
                  }}
                >
                  {ticker}
                </button>
              ))}
            </div>
          )}
          
          <div className="flex justify-end">
            <a 
              href={featuredItem.link} 
              target="_blank" 
              rel="noopener noreferrer"
              className="inline-flex items-center px-4 py-2 border border-blue-600 text-blue-600 hover:bg-blue-50 rounded-md text-sm font-medium transition-colors"
            >
              Read Full Story
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-4 h-4 ml-1">
                <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 6H5.25A2.25 2.25 0 003 8.25v10.5A2.25 2.25 0 005.25 21h10.5A2.25 2.25 0 0018 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" />
              </svg>
            </a>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="p-4 md:p-6 max-w-7xl mx-auto">
      {renderHeader()}
      {renderFeaturedNews()}
      {renderNewsItems()}
    </div>
  );
};

export default NewsPage;
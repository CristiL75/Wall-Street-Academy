import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import Login from "./pages/LoginPage";
import Signup from "./pages/Signup";
import Profile from "./pages/Profile";
import TradePage from "./pages/TradePage";
import NewsPage from "./pages/NewsPage";
import PrivateRoute from "./components/PrivateRoute";
import RecommendationsPage from './pages/RecommendationsPage';
import { isAuthenticated } from "./utils/auth";
import Navbar from "./components/Navbar";
// Adaugă importul pentru ChatbotPopup
import ChatbotPopup from "./components/ChatbotPopup";

const AppWrapper = () => {
  const location = useLocation();
  const showNavbar = isAuthenticated() && !["/login", "/signup"].includes(location.pathname);

  return (
    <>
      {showNavbar && <Navbar />}
      <Routes>
        <Route
          path="/"
          element={
            isAuthenticated() ? <Navigate to="/dashboard" /> : <Navigate to="/login" />
          }
        />
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
        <Route
          path="/dashboard"
          element={
            <PrivateRoute>
              <Dashboard />
            </PrivateRoute>
          }
        />
        <Route
          path="/profile"
          element={
            <PrivateRoute>
              <Profile />
            </PrivateRoute>
          }
        />
        <Route
          path="/trade"
          element={
            <PrivateRoute>
              <TradePage />
            </PrivateRoute>
          }
        />
        <Route
          path="/news"
          element={
            <PrivateRoute>
              <NewsPage />
            </PrivateRoute>
          }
        />
        <Route path="/recommendations" element={<RecommendationsPage />} />
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
      
      {/* Adaugă ChatbotPopup aici - va fi afișat pe toate paginile */}
      {isAuthenticated() && <ChatbotPopup />}
    </>
  );
};

function App() {
  return (
    <Router>
      <AppWrapper />
    </Router>
  );
}

export default App;
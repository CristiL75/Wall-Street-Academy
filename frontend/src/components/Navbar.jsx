// src/components/Navbar.jsx
import { Link, useNavigate } from "react-router-dom";
import { logout } from "../utils/auth";

const Navbar = () => {
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <nav className="bg-gray-800 text-white px-6 py-4 flex justify-between items-center">
      <h1 className="text-xl font-bold">Wall Street Academy</h1>
      <div className="space-x-4">
        <Link to="/dashboard" className="hover:underline">Dashboard</Link>
        <Link to="/trade" className="hover:underline">Trade</Link> {/* ✅ Nou */}
        <Link to="/profile" className="hover:underline">Profil</Link>
        <button onClick={handleLogout} className="text-red-400 hover:underline">
          Logout
        </button>
      </div>
    </nav>
  );
};

export default Navbar;

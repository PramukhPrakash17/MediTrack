import React, { useState } from "react";
import "./Navbar.css";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../../auth/AuthContext";

const Navbar = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const { isAuthenticated, logout, userName } = useAuth();
  const navigate = useNavigate();

  const toggleMenu = () => {
    setIsMenuOpen(!isMenuOpen);
  };

  return (
    <nav className="navbar">
      <div className="nav-container">
        <div className="nav-logo">
          <h2>MediTrack</h2>
        </div>

        <div className={`nav-menu ${isMenuOpen ? "active" : ""}`}>
          <Link to="/" className="nav-link">
            Home
          </Link>
          <Link to="/services" className="nav-link">
            Services
          </Link>
          {isAuthenticated ? (
            <div className="nav-user-section">
              {userName && <span className="nav-greeting">Hi, {userName}</span>}
              <button
                onClick={() => {
                  logout();
                  navigate("/auth");
                }}
                className="nav-link"
                style={{ background: "none", border: 0, cursor: "pointer" }}
              >
                Logout
              </button>
            </div>
          ) : (
            <Link to="/auth" className="nav-link">
              Login
            </Link>
          )}
        </div>

        <div className="nav-toggle" onClick={toggleMenu}>
          <span className="bar"></span>
          <span className="bar"></span>
          <span className="bar"></span>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;

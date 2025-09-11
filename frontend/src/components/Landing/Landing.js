import React from "react";
import "./Landing.css";

const Landing = () => {
  return (
    <section id="home" className="hero">
      <div className="hero-container">
        <div className="hero-content">
          <h1 className="hero-title">
            Streamline Patient Care with
            <span className="highlight"> MediTrack</span>
          </h1>
          <p className="hero-description">
            A comprehensive patient management system designed for healthcare
            professionals. Track patient records, manage appointments, and
            deliver better care with our intuitive platform.
          </p>
          <div className="hero-buttons">
            <button className="btn btn-primary">Get Started</button>
            <button className="btn btn-secondary">Learn More</button>
          </div>
        </div>
        <div className="hero-image">
          <div className="hero-placeholder">
            <div className="medical-icon">🏥</div>
            <p>Medical Dashboard</p>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Landing;

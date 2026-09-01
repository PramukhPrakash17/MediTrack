import React from "react";
import "./App.css";
import Navbar from "./components/Navbar/Navbar";
import Landing from "./components/Landing/Landing";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import AuthPage from "./pages/AuthPage/AuthPage";
import ServicesPage from "./pages/ServicesPage/ServicesPage";
import ChatWidget from "./components/ChatWidget/ChatWidget";
import { AuthProvider, useAuth } from "./auth/AuthContext";
import { PatientProvider } from "./patient/PatientContext";

const Protected = ({ children }) => {
  const { isAuthenticated } = useAuth();
  if (!isAuthenticated) {
    return <Navigate to="/auth" replace />;
  }
  return children;
};

function App() {
  return (
    <AuthProvider>
      <PatientProvider>
        <BrowserRouter>
          <div className="App">
            <Navbar />
            <Routes>
              <Route
                path="/"
                element={
                  <Protected>
                    <Landing />
                  </Protected>
                }
              />
              <Route
                path="/services"
                element={
                  <Protected>
                    <ServicesPage />
                  </Protected>
                }
              />
              <Route path="/auth" element={<AuthPage />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
            <ChatWidget />
          </div>
        </BrowserRouter>
      </PatientProvider>
    </AuthProvider>
  );
}

export default App;

import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../auth/AuthContext";
import { createApiClient } from "../../api/client";

const AuthPage = () => {
  const navigate = useNavigate();
  const { loginWithToken, setUserNameFromEmail } = useAuth();
  const api = createApiClient(() => null); // no auth for login/signup

  const [mode, setMode] = useState("login"); // 'login' | 'signup'
  const [form, setForm] = useState({
    firstName: "",
    lastName: "",
    email: "",
    password: "",
    role: "DOCTOR",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const onChange = (e) =>
    setForm((f) => ({ ...f, [e.target.name]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setSuccess("");
    try {
      if (mode === "login") {
        const res = await api.post(
          "/api/auth/login",
          {
            email: form.email,
            password: form.password,
          },
          { auth: false }
        );
        // Expecting token string or object { token }
        const token =
          typeof res === "string"
            ? res
            : res.token || res.jwt || res.accessToken;
        if (!token) throw new Error("No token returned by server");
        loginWithToken(token, form.email);
        // Fetch user name after login
        await setUserNameFromEmail(form.email);
        navigate("/");
      } else {
        await api.post(
          "/api/auth/signup",
          {
            firstName: form.firstName,
            lastName: form.lastName,
            email: form.email,
            password: form.password,
            role: form.role || "DOCTOR",
          },
          { auth: false }
        );
        // Signup successful - show success message and switch to login
        setSuccess(
          "Registration successful! Please login with your credentials."
        );
        setMode("login");
        // Clear form except email for convenience
        setForm((prev) => ({
          firstName: "",
          lastName: "",
          email: prev.email, // Keep email for convenience
          password: "",
          role: "DOCTOR",
        }));
      }
    } catch (err) {
      if (mode === "login") {
        setError("Login Failed");
      } else {
        setError(err.message || "Registration failed");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        maxWidth: 420,
        margin: "80px auto",
        padding: 24,
        border: "1px solid #e5e7eb",
        borderRadius: 12,
      }}
    >
      <h2 style={{ marginBottom: 8 }}>
        {mode === "login" ? "Doctor Login" : "Doctor Signup"}
      </h2>
      <p style={{ color: "#6b7280", marginTop: 0, marginBottom: 16 }}>
        {mode === "login" ? "Access your dashboard" : "Create your account"}
      </p>

      <form onSubmit={handleSubmit}>
        {mode === "signup" && (
          <div
            style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}
          >
            <div>
              <label>First name</label>
              <input
                name="firstName"
                value={form.firstName}
                onChange={onChange}
                required
                style={{ width: "100%", padding: 8, marginTop: 4 }}
              />
            </div>
            <div>
              <label>Last name</label>
              <input
                name="lastName"
                value={form.lastName}
                onChange={onChange}
                required
                style={{ width: "100%", padding: 8, marginTop: 4 }}
              />
            </div>
          </div>
        )}

        <div style={{ marginTop: 12 }}>
          <label>Email</label>
          <input
            type="email"
            name="email"
            value={form.email}
            onChange={onChange}
            required
            style={{ width: "100%", padding: 8, marginTop: 4 }}
          />
        </div>
        <div style={{ marginTop: 12 }}>
          <label>Password</label>
          <input
            type="password"
            name="password"
            value={form.password}
            onChange={onChange}
            required
            style={{ width: "100%", padding: 8, marginTop: 4 }}
          />
        </div>

        {mode === "signup" && (
          <div style={{ marginTop: 12 }}>
            <label>Role</label>
            <select
              name="role"
              value={form.role}
              onChange={onChange}
              style={{ width: "100%", padding: 8, marginTop: 4 }}
            >
              <option value="DOCTOR">DOCTOR</option>
              <option value="ADMIN">ADMIN</option>
            </select>
          </div>
        )}

        {error && (
          <div style={{ marginTop: 12, color: "#b91c1c" }}>{error}</div>
        )}
        {success && (
          <div
            style={{
              marginTop: 12,
              color: "#065f46",
              backgroundColor: "#d1fae5",
              padding: "8px 12px",
              borderRadius: "6px",
              border: "1px solid #a7f3d0",
            }}
          >
            {success}
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          style={{
            marginTop: 16,
            width: "100%",
            padding: 10,
            background: "#2563eb",
            color: "white",
            border: 0,
            borderRadius: 6,
          }}
        >
          {loading
            ? "Please wait..."
            : mode === "login"
            ? "Login"
            : "Create account"}
        </button>
      </form>

      <div style={{ marginTop: 16, textAlign: "center" }}>
        {mode === "login" ? (
          <button
            onClick={() => setMode("signup")}
            style={{
              background: "none",
              border: 0,
              color: "#2563eb",
              cursor: "pointer",
            }}
          >
            Don’t have an account? Sign up
          </button>
        ) : (
          <button
            onClick={() => setMode("login")}
            style={{
              background: "none",
              border: 0,
              color: "#2563eb",
              cursor: "pointer",
            }}
          >
            Already have an account? Login
          </button>
        )}
      </div>
    </div>
  );
};

export default AuthPage;

import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

// Toggle this to switch storage between localStorage and sessionStorage
const STORAGE = window.localStorage; // or: window.sessionStorage
const LOGGED_IN_KEY = "isLoggedIn";
const USER_EMAIL_KEY = "userEmail";
const USER_NAME_KEY = "userName";

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [isLoggedIn, setIsLoggedIn] = useState(
    () => STORAGE.getItem(LOGGED_IN_KEY) === "true"
  );
  const [userEmail, setUserEmail] = useState(
    () => STORAGE.getItem(USER_EMAIL_KEY) || null
  );
  const [userName, setUserName] = useState(
    () => STORAGE.getItem(USER_NAME_KEY) || null
  );

  useEffect(() => {
    if (isLoggedIn) {
      STORAGE.setItem(LOGGED_IN_KEY, "true");
    } else {
      STORAGE.removeItem(LOGGED_IN_KEY);
    }
  }, [isLoggedIn]);

  useEffect(() => {
    if (userEmail) {
      STORAGE.setItem(USER_EMAIL_KEY, userEmail);
    } else {
      STORAGE.removeItem(USER_EMAIL_KEY);
    }
  }, [userEmail]);

  useEffect(() => {
    if (userName) {
      STORAGE.setItem(USER_NAME_KEY, userName);
    } else {
      STORAGE.removeItem(USER_NAME_KEY);
    }
  }, [userName]);

  const setUserNameFromEmail = useCallback(async (email) => {
    try {
      const response = await fetch(
        `http://localhost:8080/api/auth/getName?email=${encodeURIComponent(
          email
        )}`,
        {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
          },
        }
      );

      if (response.ok) {
        const name = await response.text();
        setUserName(name);
      }
    } catch (error) {
      console.error("Failed to fetch user name:", error);
    }
  }, []);

  const login = useCallback((email) => {
    setIsLoggedIn(true);
    setUserEmail(email);
  }, []);

  // Fetch user name on mount if we have email but no name
  useEffect(() => {
    if (userEmail && !userName && isLoggedIn) {
      setUserNameFromEmail(userEmail);
    }
  }, [userEmail, userName, isLoggedIn, setUserNameFromEmail]);

  const logout = useCallback(() => {
    setIsLoggedIn(false);
    setUserEmail(null);
    setUserName(null);
  }, []);

  const value = useMemo(
    () => ({
      userEmail,
      userName,
      isAuthenticated: isLoggedIn,
      login,
      setUserNameFromEmail,
      logout,
    }),
    [isLoggedIn, userEmail, userName, login, setUserNameFromEmail, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
};

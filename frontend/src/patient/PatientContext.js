import React, {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
} from "react";

// Tracks which patient is "active" (currently open in ServicesPage) so the
// ChatWidget can auto-attach patient context to chat writes without the
// doctor typing an insurance number, and lets a chat-driven write notify
// ServicesPage to silently refresh instead of the doctor doing it by hand.
const PatientContext = createContext(null);

export const PatientProvider = ({ children }) => {
  const [activeInsuranceNumber, setActiveInsuranceNumber] = useState(null);
  // Bumped on every notifyDataChanged call so a useEffect elsewhere can
  // detect a fresh event even if the same kinds repeat back to back.
  const [lastChange, setLastChange] = useState({ kinds: [], token: 0 });

  const notifyDataChanged = useCallback((kinds) => {
    setLastChange((prev) => ({ kinds, token: prev.token + 1 }));
  }, []);

  const value = useMemo(
    () => ({
      activeInsuranceNumber,
      setActiveInsuranceNumber,
      lastChange,
      notifyDataChanged,
    }),
    [activeInsuranceNumber, lastChange, notifyDataChanged]
  );

  return (
    <PatientContext.Provider value={value}>{children}</PatientContext.Provider>
  );
};

export const usePatient = () => {
  const ctx = useContext(PatientContext);
  if (!ctx) throw new Error("usePatient must be used within PatientProvider");
  return ctx;
};

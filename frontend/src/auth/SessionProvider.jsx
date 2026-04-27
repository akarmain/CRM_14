import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';
import { clearSession, fetchSession, selectRole } from '../lib/leadsApi';

const SessionContext = createContext(null);

export function SessionProvider({ children }) {
  const [session, setSession] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  const refreshSession = async () => {
    setIsLoading(true);
    try {
      const nextSession = await fetchSession();
      setSession(nextSession);
      return nextSession;
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    void refreshSession();
  }, []);

  const handleRoleSelect = async (role) => {
    const nextSession = await selectRole(role);
    setSession(nextSession);
    return nextSession;
  };

  const handleLogout = async () => {
    await clearSession();
    setSession(null);
  };

  const value = useMemo(
    () => ({
      session,
      isLoading,
      refreshSession,
      selectRole: handleRoleSelect,
      logout: handleLogout,
    }),
    [session, isLoading]
  );

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
}

export function useSession() {
  const context = useContext(SessionContext);
  if (!context) {
    throw new Error('useSession must be used inside SessionProvider.');
  }
  return context;
}

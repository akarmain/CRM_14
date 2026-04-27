import React from 'react';
import { BrowserRouter, Navigate, Outlet, Route, Routes } from 'react-router-dom';
import { SessionProvider, useSession } from './auth/SessionProvider';
import HomePage from './components/HomePage';
import LeadsPage from './components/LeadsPage';
import ReportsPage from './components/ReportsPage';
import RequestsPage from './components/RequestsPage';

function FullScreenMessage({ title, subtitle }) {
  return (
    <div className="shell-screen">
      <div className="shell-card">
        <h1>{title}</h1>
        {subtitle && <p>{subtitle}</p>}
      </div>
    </div>
  );
}

function RootRoute() {
  const { session, isLoading } = useSession();

  if (isLoading) {
    return <FullScreenMessage title="CRM 14" subtitle="Загружаем сессию роли..." />;
  }

  if (session) {
    return <Navigate to="/leads/table" replace />;
  }

  return <HomePage />;
}

function ProtectedRoute({ allowedRoles = null }) {
  const { session, isLoading } = useSession();

  if (isLoading) {
    return <FullScreenMessage title="CRM 14" subtitle="Проверяем доступ..." />;
  }

  if (!session) {
    return <Navigate to="/" replace />;
  }

  if (allowedRoles && !allowedRoles.includes(session.role)) {
    return <Navigate to="/leads/table" replace />;
  }

  return <Outlet />;
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<RootRoute />} />
      <Route element={<ProtectedRoute />}>
        <Route path="/leads/:viewMode" element={<LeadsPage />} />
        <Route path="/leads" element={<Navigate to="/leads/table" replace />} />
      </Route>
      <Route element={<ProtectedRoute allowedRoles={['analyst', 'sales_head']} />}>
        <Route path="/reports" element={<ReportsPage />} />
      </Route>
      <Route element={<ProtectedRoute allowedRoles={['sales_head']} />}>
        <Route path="/requests" element={<RequestsPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <SessionProvider>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </SessionProvider>
  );
}

export default App;

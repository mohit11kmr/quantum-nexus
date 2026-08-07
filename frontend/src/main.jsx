import React from 'react';
import ReactDOM from 'react-dom/client';
import { HashRouter, Routes, Route, Navigate, useParams } from 'react-router-dom';
import App from './App.jsx';
import './App.css';
import { LanguageProvider } from './i18n.jsx';

function RedirectWithDefaultSymbol() {
  const { tab } = useParams();
  return <Navigate to={`/${tab || 'playbook'}/NIFTY`} replace />;
}

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("ErrorBoundary caught an error", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: '2rem', color: '#FF3366', fontFamily: 'JetBrains Mono' }}>
          <h2>SYSTEM ERROR DETECTED</h2>
          <p>{this.state.error?.toString()}</p>
        </div>
      );
    }
    return this.props.children;
  }
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <ErrorBoundary>
      <LanguageProvider>
        <HashRouter>
          <Routes>
            <Route path="/" element={<Navigate to="/playbook/NIFTY" replace />} />
            <Route path="/:tab" element={<RedirectWithDefaultSymbol />} />
            <Route path="/:tab/:symbol" element={<App />} />
          </Routes>
        </HashRouter>
      </LanguageProvider>
    </ErrorBoundary>
  </React.StrictMode>,
);

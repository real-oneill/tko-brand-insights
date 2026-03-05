import React, { useState, useEffect } from 'react';
import { fetchApi } from './utils/api';
import Dashboard from './components/Dashboard';
import PriceAnalysis from './components/PriceAnalysis';
import MarketShare from './components/MarketShare';
import BrandPerformance from './components/BrandPerformance';
import SearchVisibility from './components/SearchVisibility';
import InventoryHealth from './components/InventoryHealth';
import SentimentReviews from './components/SentimentReviews';
import ScenarioPlanner from './components/ScenarioPlanner';
import Filters from './components/Filters';

const TABS = [
  { id: 'dashboard', label: 'Dashboard' },
  { id: 'price', label: 'Price Intelligence' },
  { id: 'market', label: 'Market Share' },
  { id: 'brand', label: 'Brand Performance' },
  { id: 'serp', label: 'Search Visibility' },
  { id: 'inventory', label: 'Inventory' },
  { id: 'sentiment', label: 'Sentiment' },
  { id: 'scenario', label: 'Scenario Planner' },
];

const BRAND_COLORS = {
  'TKO Combat': '#e63946',
  'Century Martial Arts': '#457b9d',
  'Everlast': '#2a9d8f',
  'Hayabusa': '#e9c46a',
  'Venum': '#f4a261',
  'RDX Sports': '#264653',
};

export default function App() {
  const [tab, setTab] = useState('dashboard');
  const [filters, setFilters] = useState({
    start_date: '2025-01-01',
    end_date: '2025-03-01',
    brands: null,
    retailers: null,
    category: null,
  });
  const [filterOptions, setFilterOptions] = useState({ brands: [], retailers: [], categories: [] });

  useEffect(() => {
    fetchApi('/filters').then(data => {
      setFilterOptions(data.filters || {});
      if (data.date_range) {
        setFilters(f => ({
          ...f,
          start_date: data.date_range.min_date || f.start_date,
          end_date: data.date_range.max_date || f.end_date,
        }));
      }
    }).catch(() => {});
  }, []);

  const renderTab = () => {
    const props = { filters, colors: BRAND_COLORS };
    switch (tab) {
      case 'dashboard': return <Dashboard {...props} />;
      case 'price': return <PriceAnalysis {...props} />;
      case 'market': return <MarketShare {...props} />;
      case 'brand': return <BrandPerformance {...props} />;
      case 'serp': return <SearchVisibility {...props} />;
      case 'inventory': return <InventoryHealth {...props} />;
      case 'sentiment': return <SentimentReviews {...props} />;
      case 'scenario': return <ScenarioPlanner {...props} />;
      default: return <Dashboard {...props} />;
    }
  };

  return (
    <div style={styles.app}>
      <header style={styles.header}>
        <div style={styles.headerLeft}>
          <div style={styles.logo}>TKO</div>
          <div>
            <h1 style={styles.title}>Brand Analyzer</h1>
            <p style={styles.subtitle}>Competitive Intelligence Platform</p>
          </div>
        </div>
      </header>

      <nav style={styles.nav}>
        {TABS.map(t => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            style={{
              ...styles.navBtn,
              ...(tab === t.id ? styles.navBtnActive : {}),
            }}
          >
            {t.label}
          </button>
        ))}
      </nav>

      <Filters
        filters={filters}
        setFilters={setFilters}
        options={filterOptions}
      />

      <main style={styles.main}>
        {renderTab()}
      </main>
    </div>
  );
}

const styles = {
  app: {
    fontFamily: "'Inter', -apple-system, sans-serif",
    background: '#0f1117',
    color: '#e4e4e7',
    minHeight: '100vh',
    margin: 0,
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '16px 24px',
    background: '#161821',
    borderBottom: '1px solid #2a2d3a',
  },
  headerLeft: {
    display: 'flex',
    alignItems: 'center',
    gap: '16px',
  },
  logo: {
    background: '#e63946',
    color: '#fff',
    fontWeight: 800,
    fontSize: '20px',
    padding: '8px 14px',
    borderRadius: '8px',
    letterSpacing: '2px',
  },
  title: {
    margin: 0,
    fontSize: '20px',
    fontWeight: 600,
    color: '#fff',
  },
  subtitle: {
    margin: 0,
    fontSize: '12px',
    color: '#71717a',
    fontWeight: 400,
  },
  nav: {
    display: 'flex',
    gap: '2px',
    padding: '0 24px',
    background: '#161821',
    borderBottom: '1px solid #2a2d3a',
    overflowX: 'auto',
  },
  navBtn: {
    padding: '10px 16px',
    background: 'transparent',
    border: 'none',
    color: '#a1a1aa',
    cursor: 'pointer',
    fontSize: '13px',
    fontWeight: 500,
    borderBottom: '2px solid transparent',
    whiteSpace: 'nowrap',
    fontFamily: 'inherit',
    transition: 'color 0.2s',
  },
  navBtnActive: {
    color: '#e63946',
    borderBottom: '2px solid #e63946',
  },
  main: {
    padding: '20px 24px',
    maxWidth: '1400px',
    margin: '0 auto',
  },
};

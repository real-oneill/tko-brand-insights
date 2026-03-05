import React, { useState, useEffect } from 'react';
import { fetchApi } from '../utils/api';
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend, Cell
} from 'recharts';

export default function PriceAnalysis({ filters, colors }) {
  const [comparison, setComparison] = useState([]);
  const [trends, setTrends] = useState([]);
  const [gap, setGap] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      fetchApi('/price/comparison', filters),
      fetchApi('/price/trends', filters),
      fetchApi('/price/gap', filters),
    ]).then(([c, t, g]) => {
      setComparison(c);
      setTrends(t);
      setGap(g);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, [filters]);

  if (loading) return <div style={{ color: '#71717a', padding: '40px', textAlign: 'center' }}>Loading...</div>;

  const brands = [...new Set(trends.map(t => t.BRAND))];
  const dateMap = {};
  trends.forEach(t => {
    if (!dateMap[t.date]) dateMap[t.date] = { date: t.date };
    dateMap[t.date][t.BRAND] = parseFloat(t.avg_price);
  });
  const trendData = Object.values(dateMap).sort((a, b) => a.date.localeCompare(b.date));

  // Aggregate comparison by brand
  const brandAvg = {};
  comparison.forEach(c => {
    if (!brandAvg[c.BRAND]) brandAvg[c.BRAND] = { brand: c.BRAND, total: 0, count: 0 };
    brandAvg[c.BRAND].total += parseFloat(c.avg_price);
    brandAvg[c.BRAND].count += 1;
  });
  const brandData = Object.values(brandAvg).map(b => ({
    brand: b.brand,
    avg_price: Math.round(b.total / b.count * 100) / 100,
  })).sort((a, b) => b.avg_price - a.avg_price);

  return (
    <div>
      <h2 style={sectionTitle}>Price Intelligence</h2>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '16px' }}>
        <div style={card}>
          <h3 style={chartTitle}>Average Price by Brand</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={brandData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#2a2d3a" />
              <XAxis type="number" stroke="#71717a" tick={{ fontSize: 11 }} />
              <YAxis dataKey="brand" type="category" stroke="#71717a" tick={{ fontSize: 11 }} width={130} />
              <Tooltip contentStyle={tooltipStyle} />
              <Bar dataKey="avg_price" name="Avg Price ($)" radius={[0, 4, 4, 0]}>
                {brandData.map(d => (
                  <Cell key={d.brand} fill={colors[d.brand] || '#888'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div style={card}>
          <h3 style={chartTitle}>Price Gap vs Competitors (TKO Combat)</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={gap}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2a2d3a" />
              <XAxis dataKey="category" stroke="#71717a" tick={{ fontSize: 10 }} angle={-20} textAnchor="end" height={60} />
              <YAxis stroke="#71717a" tick={{ fontSize: 11 }} />
              <Tooltip contentStyle={tooltipStyle} />
              <Bar dataKey="gap_pct" name="Gap %" radius={[4, 4, 0, 0]}>
                {gap.map((d, i) => (
                  <Cell key={i} fill={parseFloat(d.gap_pct) > 0 ? '#ef4444' : '#22c55e'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div style={card}>
        <h3 style={chartTitle}>Price Trends Over Time</h3>
        <ResponsiveContainer width="100%" height={350}>
          <LineChart data={trendData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#2a2d3a" />
            <XAxis dataKey="date" stroke="#71717a" tick={{ fontSize: 11 }} />
            <YAxis stroke="#71717a" tick={{ fontSize: 11 }} />
            <Tooltip contentStyle={tooltipStyle} />
            <Legend wrapperStyle={{ fontSize: '12px' }} />
            {brands.map(b => (
              <Line key={b} type="monotone" dataKey={b} stroke={colors[b] || '#888'} dot={false} strokeWidth={2} />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

const sectionTitle = { fontSize: '18px', fontWeight: 600, color: '#fff', marginBottom: '16px' };
const chartTitle = { fontSize: '14px', fontWeight: 500, color: '#e4e4e7', margin: '0 0 16px 0' };
const card = { background: '#161821', borderRadius: '8px', padding: '16px 20px', border: '1px solid #2a2d3a' };
const tooltipStyle = { background: '#1a1c28', border: '1px solid #2a2d3a', borderRadius: '6px', fontSize: '12px' };

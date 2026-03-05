import React, { useState, useEffect } from 'react';
import { fetchApi } from '../utils/api';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from 'recharts';

const KPICard = ({ label, value, sub, color }) => (
  <div style={{ ...cardStyle, borderLeft: `3px solid ${color || '#e63946'}` }}>
    <div style={{ fontSize: '11px', color: '#71717a', textTransform: 'uppercase', letterSpacing: '0.5px' }}>{label}</div>
    <div style={{ fontSize: '28px', fontWeight: 700, color: '#fff', marginTop: '4px' }}>{value}</div>
    {sub && <div style={{ fontSize: '12px', color: '#a1a1aa', marginTop: '2px' }}>{sub}</div>}
  </div>
);

const cardStyle = {
  background: '#161821',
  borderRadius: '8px',
  padding: '16px 20px',
  border: '1px solid #2a2d3a',
};

export default function Dashboard({ filters, colors }) {
  const [kpis, setKpis] = useState([]);
  const [trends, setTrends] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      fetchApi('/dashboard/kpis', filters),
      fetchApi('/dashboard/trends', filters),
    ]).then(([k, t]) => {
      setKpis(k);
      setTrends(t);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, [filters]);

  if (loading) return <div style={{ color: '#71717a', padding: '40px', textAlign: 'center' }}>Loading dashboard...</div>;

  const tko = kpis.find(k => k.BRAND === 'TKO Combat') || {};
  const brands = [...new Set(trends.map(t => t.BRAND))];

  // Pivot trends for recharts
  const dateMap = {};
  trends.forEach(t => {
    if (!dateMap[t.date]) dateMap[t.date] = { date: t.date };
    dateMap[t.date][t.BRAND] = parseFloat(t.avg_price);
  });
  const trendData = Object.values(dateMap).sort((a, b) => a.date.localeCompare(b.date));

  return (
    <div>
      <h2 style={sectionTitle}>Executive Dashboard</h2>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px', marginBottom: '24px' }}>
        <KPICard label="Avg Price" value={`$${tko.avg_price || '—'}`} sub="TKO Combat" color="#e63946" />
        <KPICard label="Avg Rating" value={tko.avg_rating || '—'} sub={`${tko.avg_reviews || 0} avg reviews`} color="#2a9d8f" />
        <KPICard label="Availability" value={`${tko.availability_pct || 0}%`} sub="In-stock rate" color="#457b9d" />
        <KPICard label="Products" value={tko.product_count || 0} sub="Active listings" color="#e9c46a" />
      </div>

      <div style={{ ...cardStyle, marginBottom: '24px' }}>
        <h3 style={chartTitle}>Average Price Trends by Brand</h3>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={trendData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#2a2d3a" />
            <XAxis dataKey="date" stroke="#71717a" tick={{ fontSize: 11 }} />
            <YAxis stroke="#71717a" tick={{ fontSize: 11 }} />
            <Tooltip
              contentStyle={{ background: '#1a1c28', border: '1px solid #2a2d3a', borderRadius: '6px', fontSize: '12px' }}
            />
            <Legend wrapperStyle={{ fontSize: '12px' }} />
            {brands.map(b => (
              <Line key={b} type="monotone" dataKey={b} stroke={colors[b] || '#888'} dot={false} strokeWidth={2} />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div style={cardStyle}>
        <h3 style={chartTitle}>Brand Comparison</h3>
        <div style={{ overflowX: 'auto' }}>
          <table style={tableStyle}>
            <thead>
              <tr>
                <th style={th}>Brand</th>
                <th style={th}>Avg Price</th>
                <th style={th}>Rating</th>
                <th style={th}>Reviews</th>
                <th style={th}>Availability</th>
                <th style={th}>Products</th>
              </tr>
            </thead>
            <tbody>
              {kpis.map(k => (
                <tr key={k.BRAND} style={k.BRAND === 'TKO Combat' ? { background: '#1e2030' } : {}}>
                  <td style={td}>
                    <span style={{ display: 'inline-block', width: 10, height: 10, borderRadius: '50%', background: colors[k.BRAND] || '#888', marginRight: 8 }} />
                    {k.BRAND}
                  </td>
                  <td style={td}>${k.avg_price}</td>
                  <td style={td}>{k.avg_rating}</td>
                  <td style={td}>{Number(k.avg_reviews).toLocaleString()}</td>
                  <td style={td}>{k.availability_pct}%</td>
                  <td style={td}>{k.product_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

const sectionTitle = { fontSize: '18px', fontWeight: 600, color: '#fff', marginBottom: '16px' };
const chartTitle = { fontSize: '14px', fontWeight: 500, color: '#e4e4e7', margin: '0 0 16px 0' };
const tableStyle = { width: '100%', borderCollapse: 'collapse', fontSize: '13px' };
const th = { textAlign: 'left', padding: '8px 12px', borderBottom: '1px solid #2a2d3a', color: '#71717a', fontWeight: 500, fontSize: '11px', textTransform: 'uppercase' };
const td = { padding: '8px 12px', borderBottom: '1px solid #1e2030' };

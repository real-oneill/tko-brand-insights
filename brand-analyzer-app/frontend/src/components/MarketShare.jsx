import React, { useState, useEffect } from 'react';
import { fetchApi } from '../utils/api';
import {
  PieChart, Pie, Cell, BarChart, Bar, LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from 'recharts';

export default function MarketShare({ filters, colors }) {
  const [share, setShare] = useState([]);
  const [byRetailer, setByRetailer] = useState([]);
  const [trend, setTrend] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      fetchApi('/market/share', filters),
      fetchApi('/market/share-by-retailer', filters),
      fetchApi('/market/share-trend', filters),
    ]).then(([s, r, t]) => {
      setShare(s);
      setByRetailer(r);
      setTrend(t);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, [filters]);

  if (loading) return <div style={{ color: '#71717a', padding: '40px', textAlign: 'center' }}>Loading...</div>;

  const pieData = share.map(s => ({ name: s.BRAND, value: parseFloat(s.share_pct) }));
  const colorArr = pieData.map(d => colors[d.name] || '#888');

  // Retailer grouped bar data
  const retailers = [...new Set(byRetailer.map(r => r.retailer))];
  const brands = [...new Set(byRetailer.map(r => r.BRAND))];
  const retailerData = retailers.map(ret => {
    const row = { retailer: ret };
    byRetailer.filter(r => r.retailer === ret).forEach(r => {
      row[r.BRAND] = parseFloat(r.share_pct);
    });
    return row;
  });

  // Trend data
  const dateMap = {};
  trend.forEach(t => {
    if (!dateMap[t.date]) dateMap[t.date] = { date: t.date };
    dateMap[t.date][t.BRAND] = parseInt(t.product_count);
  });
  const trendData = Object.values(dateMap).sort((a, b) => a.date.localeCompare(b.date));
  const trendBrands = [...new Set(trend.map(t => t.BRAND))];

  return (
    <div>
      <h2 style={sectionTitle}>Market Share Analysis</h2>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '16px' }}>
        <div style={card}>
          <h3 style={chartTitle}>Share of Shelf by Brand</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie data={pieData} cx="50%" cy="50%" innerRadius={60} outerRadius={110}
                paddingAngle={2} dataKey="value" label={({ name, value }) => `${name}: ${value}%`}
                labelLine={{ stroke: '#71717a' }}
              >
                {pieData.map((_, i) => <Cell key={i} fill={colorArr[i]} />)}
              </Pie>
              <Tooltip contentStyle={tooltipStyle} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div style={card}>
          <h3 style={chartTitle}>Market Share by Retailer</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={retailerData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2a2d3a" />
              <XAxis dataKey="retailer" stroke="#71717a" tick={{ fontSize: 11 }} />
              <YAxis stroke="#71717a" tick={{ fontSize: 11 }} />
              <Tooltip contentStyle={tooltipStyle} />
              <Legend wrapperStyle={{ fontSize: '11px' }} />
              {brands.map(b => (
                <Bar key={b} dataKey={b} fill={colors[b] || '#888'} stackId="a" />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div style={card}>
        <h3 style={chartTitle}>Product Count Trends Over Time</h3>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={trendData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#2a2d3a" />
            <XAxis dataKey="date" stroke="#71717a" tick={{ fontSize: 11 }} />
            <YAxis stroke="#71717a" tick={{ fontSize: 11 }} />
            <Tooltip contentStyle={tooltipStyle} />
            <Legend wrapperStyle={{ fontSize: '12px' }} />
            {trendBrands.map(b => (
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

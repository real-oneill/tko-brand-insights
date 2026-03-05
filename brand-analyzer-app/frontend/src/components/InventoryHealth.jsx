import React, { useState, useEffect } from 'react';
import { fetchApi } from '../utils/api';
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Legend, Cell
} from 'recharts';

export default function InventoryHealth({ filters, colors }) {
  const [byBrand, setByBrand] = useState([]);
  const [trend, setTrend] = useState([]);
  const [byRetailer, setByRetailer] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      fetchApi('/inventory/by-brand', filters),
      fetchApi('/inventory/trend', filters),
      fetchApi('/inventory/by-retailer', filters),
    ]).then(([b, t, r]) => {
      setByBrand(b);
      setTrend(t);
      setByRetailer(r);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, [filters]);

  if (loading) return <div style={{ color: '#71717a', padding: '40px', textAlign: 'center' }}>Loading...</div>;

  // Availability by brand - stacked bar
  const brands = [...new Set(byBrand.map(b => b.BRAND))];
  const brandAvailData = brands.map(brand => {
    const row = { brand };
    byBrand.filter(b => b.BRAND === brand).forEach(b => {
      row[b.status] = parseFloat(b.pct);
    });
    return row;
  });

  // Trend data
  const dateMap = {};
  trend.forEach(t => {
    if (!dateMap[t.date]) dateMap[t.date] = { date: t.date };
    dateMap[t.date][t.BRAND] = parseFloat(t.in_stock_pct);
  });
  const trendData = Object.values(dateMap).sort((a, b) => a.date.localeCompare(b.date));
  const trendBrands = [...new Set(trend.map(t => t.BRAND))];

  // By retailer
  const retailers = [...new Set(byRetailer.map(r => r.retailer))];
  const retailerBrands = [...new Set(byRetailer.map(r => r.BRAND))];
  const retailerData = retailers.map(ret => {
    const row = { retailer: ret };
    byRetailer.filter(r => r.retailer === ret).forEach(r => {
      row[r.BRAND] = parseFloat(r.in_stock_pct);
    });
    return row;
  });

  return (
    <div>
      <h2 style={sectionTitle}>Inventory & Availability</h2>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '16px' }}>
        <div style={card}>
          <h3 style={chartTitle}>Availability Distribution by Brand</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={brandAvailData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#2a2d3a" />
              <XAxis type="number" stroke="#71717a" tick={{ fontSize: 11 }} domain={[0, 100]} />
              <YAxis dataKey="brand" type="category" stroke="#71717a" tick={{ fontSize: 10 }} width={130} />
              <Tooltip contentStyle={tooltipStyle} />
              <Legend wrapperStyle={{ fontSize: '11px' }} />
              <Bar dataKey="IN_STOCK" name="In Stock" fill="#22c55e" stackId="a" />
              <Bar dataKey="LIMITED_STOCK" name="Limited" fill="#f59e0b" stackId="a" />
              <Bar dataKey="OUT_OF_STOCK" name="Out of Stock" fill="#ef4444" stackId="a" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div style={card}>
          <h3 style={chartTitle}>In-Stock Rate by Retailer</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={retailerData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2a2d3a" />
              <XAxis dataKey="retailer" stroke="#71717a" tick={{ fontSize: 11 }} />
              <YAxis stroke="#71717a" tick={{ fontSize: 11 }} domain={[0, 100]} />
              <Tooltip contentStyle={tooltipStyle} />
              <Legend wrapperStyle={{ fontSize: '11px' }} />
              {retailerBrands.map(b => (
                <Bar key={b} dataKey={b} fill={colors[b] || '#888'} />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div style={card}>
        <h3 style={chartTitle}>In-Stock Rate Trend Over Time</h3>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={trendData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#2a2d3a" />
            <XAxis dataKey="date" stroke="#71717a" tick={{ fontSize: 11 }} />
            <YAxis stroke="#71717a" tick={{ fontSize: 11 }} domain={[60, 100]} />
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

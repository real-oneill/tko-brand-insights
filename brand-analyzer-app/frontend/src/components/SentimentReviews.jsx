import React, { useState, useEffect } from 'react';
import { fetchApi } from '../utils/api';
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Legend, Cell
} from 'recharts';

export default function SentimentReviews({ filters, colors }) {
  const [trends, setTrends] = useState([]);
  const [comparison, setComparison] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      fetchApi('/sentiment/trends', filters),
      fetchApi('/sentiment/comparison', filters),
    ]).then(([t, c]) => {
      setTrends(t);
      setComparison(c);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, [filters]);

  if (loading) return <div style={{ color: '#71717a', padding: '40px', textAlign: 'center' }}>Loading...</div>;

  // Rating trends
  const dateMap = {};
  trends.forEach(t => {
    if (!dateMap[t.date]) dateMap[t.date] = { date: t.date };
    dateMap[t.date][`${t.BRAND}_rating`] = parseFloat(t.avg_rating);
    dateMap[t.date][`${t.BRAND}_reviews`] = parseInt(t.avg_review_count);
  });
  const trendData = Object.values(dateMap).sort((a, b) => a.date.localeCompare(b.date));
  const brands = [...new Set(trends.map(t => t.BRAND))];

  // Sentiment distribution
  const sentData = comparison.map(c => ({
    brand: c.BRAND,
    excellent: parseInt(c.excellent_count),
    good: parseInt(c.good_count),
    average: parseInt(c.average_count),
    below_avg: parseInt(c.below_avg_count),
    avg_rating: parseFloat(c.avg_rating),
  }));

  return (
    <div>
      <h2 style={sectionTitle}>Customer Sentiment & Reviews</h2>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '12px', marginBottom: '16px' }}>
        {comparison.map(c => (
          <div key={c.BRAND} style={{ ...cardSm, borderLeft: `3px solid ${colors[c.BRAND] || '#888'}` }}>
            <div style={{ fontSize: '13px', fontWeight: 500, color: '#fff' }}>{c.BRAND}</div>
            <div style={{ fontSize: '28px', fontWeight: 700, color: colors[c.BRAND], marginTop: '4px' }}>
              {c.avg_rating}
            </div>
            <div style={{ fontSize: '11px', color: '#71717a' }}>
              {Number(c.max_reviews).toLocaleString()} max reviews
            </div>
          </div>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '16px' }}>
        <div style={card}>
          <h3 style={chartTitle}>Average Rating Trends</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={trendData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2a2d3a" />
              <XAxis dataKey="date" stroke="#71717a" tick={{ fontSize: 11 }} />
              <YAxis stroke="#71717a" tick={{ fontSize: 11 }} domain={[3, 5]} />
              <Tooltip contentStyle={tooltipStyle} />
              <Legend wrapperStyle={{ fontSize: '11px' }} />
              {brands.map(b => (
                <Line key={b} type="monotone" dataKey={`${b}_rating`} name={b}
                  stroke={colors[b] || '#888'} dot={false} strokeWidth={2} />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div style={card}>
          <h3 style={chartTitle}>Sentiment Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={sentData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2a2d3a" />
              <XAxis dataKey="brand" stroke="#71717a" tick={{ fontSize: 10 }} angle={-15} textAnchor="end" height={50} />
              <YAxis stroke="#71717a" tick={{ fontSize: 11 }} />
              <Tooltip contentStyle={tooltipStyle} />
              <Legend wrapperStyle={{ fontSize: '11px' }} />
              <Bar dataKey="excellent" name="4.5+" fill="#22c55e" stackId="a" />
              <Bar dataKey="good" name="4.0-4.4" fill="#84cc16" stackId="a" />
              <Bar dataKey="average" name="3.5-3.9" fill="#f59e0b" stackId="a" />
              <Bar dataKey="below_avg" name="<3.5" fill="#ef4444" stackId="a" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div style={card}>
        <h3 style={chartTitle}>Review Count Growth</h3>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={trendData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#2a2d3a" />
            <XAxis dataKey="date" stroke="#71717a" tick={{ fontSize: 11 }} />
            <YAxis stroke="#71717a" tick={{ fontSize: 11 }} />
            <Tooltip contentStyle={tooltipStyle} />
            <Legend wrapperStyle={{ fontSize: '11px' }} />
            {brands.map(b => (
              <Line key={b} type="monotone" dataKey={`${b}_reviews`} name={b}
                stroke={colors[b] || '#888'} dot={false} strokeWidth={2} />
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
const cardSm = { background: '#161821', borderRadius: '8px', padding: '12px 16px', border: '1px solid #2a2d3a' };
const tooltipStyle = { background: '#1a1c28', border: '1px solid #2a2d3a', borderRadius: '6px', fontSize: '12px' };

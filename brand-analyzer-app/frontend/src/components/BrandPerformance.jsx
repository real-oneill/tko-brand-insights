import React, { useState, useEffect } from 'react';
import { fetchApi } from '../utils/api';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend, Cell, RadarChart, Radar,
  PolarGrid, PolarAngleAxis, PolarRadiusAxis
} from 'recharts';

export default function BrandPerformance({ filters, colors }) {
  const [scorecard, setScorecard] = useState([]);
  const [ratingDist, setRatingDist] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      fetchApi('/brand/scorecard', filters),
      fetchApi('/brand/rating-distribution', filters),
    ]).then(([s, r]) => {
      setScorecard(s);
      setRatingDist(r);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, [filters]);

  if (loading) return <div style={{ color: '#71717a', padding: '40px', textAlign: 'center' }}>Loading...</div>;

  // Radar data: normalize metrics to 0-100
  const radarMetrics = ['avg_rating', 'availability_pct', 'product_count', 'category_count'];
  const maxValues = {};
  radarMetrics.forEach(m => {
    maxValues[m] = Math.max(...scorecard.map(s => parseFloat(s[m]) || 0));
  });
  const radarData = [
    { metric: 'Rating', ...Object.fromEntries(scorecard.map(s => [s.BRAND, ((parseFloat(s.avg_rating) || 0) / 5 * 100)])) },
    { metric: 'Availability', ...Object.fromEntries(scorecard.map(s => [s.BRAND, parseFloat(s.availability_pct) || 0])) },
    { metric: 'Products', ...Object.fromEntries(scorecard.map(s => [s.BRAND, ((parseFloat(s.product_count) || 0) / (maxValues.product_count || 1) * 100)])) },
    { metric: 'Categories', ...Object.fromEntries(scorecard.map(s => [s.BRAND, ((parseFloat(s.category_count) || 0) / (maxValues.category_count || 1) * 100)])) },
  ];
  const brandNames = scorecard.map(s => s.BRAND);

  // Rating distribution grouped
  const ratingBuckets = [1, 2, 3, 4];
  const distData = ratingBuckets.map(b => {
    const row = { bucket: `${b}.0-${b}.9` };
    ratingDist.filter(r => parseInt(r.rating_bucket) === b).forEach(r => {
      row[r.BRAND] = parseInt(r.count);
    });
    return row;
  });

  return (
    <div>
      <h2 style={sectionTitle}>Brand Performance Scorecard</h2>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px', marginBottom: '16px' }}>
        {scorecard.map(s => (
          <div key={s.BRAND} style={{ ...card, borderLeft: `3px solid ${colors[s.BRAND] || '#888'}` }}>
            <div style={{ fontSize: '14px', fontWeight: 600, color: '#fff', marginBottom: '8px' }}>{s.BRAND}</div>
            <div style={{ fontSize: '11px', color: '#71717a' }}>Health Index</div>
            <div style={{ fontSize: '24px', fontWeight: 700, color: colors[s.BRAND] || '#fff' }}>{s.health_index}</div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px', marginTop: '8px', fontSize: '11px' }}>
              <div><span style={{ color: '#71717a' }}>Rating:</span> {s.avg_rating}</div>
              <div><span style={{ color: '#71717a' }}>Avail:</span> {s.availability_pct}%</div>
              <div><span style={{ color: '#71717a' }}>Price:</span> ${s.avg_price}</div>
              <div><span style={{ color: '#71717a' }}>Products:</span> {s.product_count}</div>
            </div>
          </div>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
        <div style={card}>
          <h3 style={chartTitle}>Brand Comparison Radar</h3>
          <ResponsiveContainer width="100%" height={350}>
            <RadarChart data={radarData}>
              <PolarGrid stroke="#2a2d3a" />
              <PolarAngleAxis dataKey="metric" stroke="#71717a" tick={{ fontSize: 11 }} />
              <PolarRadiusAxis stroke="#2a2d3a" tick={{ fontSize: 10 }} />
              {brandNames.slice(0, 4).map(b => (
                <Radar key={b} name={b} dataKey={b} stroke={colors[b] || '#888'}
                  fill={colors[b] || '#888'} fillOpacity={0.1} strokeWidth={2} />
              ))}
              <Legend wrapperStyle={{ fontSize: '11px' }} />
              <Tooltip contentStyle={tooltipStyle} />
            </RadarChart>
          </ResponsiveContainer>
        </div>

        <div style={card}>
          <h3 style={chartTitle}>Rating Distribution</h3>
          <ResponsiveContainer width="100%" height={350}>
            <BarChart data={distData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2a2d3a" />
              <XAxis dataKey="bucket" stroke="#71717a" tick={{ fontSize: 11 }} />
              <YAxis stroke="#71717a" tick={{ fontSize: 11 }} />
              <Tooltip contentStyle={tooltipStyle} />
              <Legend wrapperStyle={{ fontSize: '11px' }} />
              {brandNames.map(b => (
                <Bar key={b} dataKey={b} fill={colors[b] || '#888'} />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}

const sectionTitle = { fontSize: '18px', fontWeight: 600, color: '#fff', marginBottom: '16px' };
const chartTitle = { fontSize: '14px', fontWeight: 500, color: '#e4e4e7', margin: '0 0 16px 0' };
const card = { background: '#161821', borderRadius: '8px', padding: '16px 20px', border: '1px solid #2a2d3a' };
const tooltipStyle = { background: '#1a1c28', border: '1px solid #2a2d3a', borderRadius: '6px', fontSize: '12px' };

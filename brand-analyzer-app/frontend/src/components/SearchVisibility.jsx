import React, { useState, useEffect } from 'react';
import { fetchApi } from '../utils/api';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend, Cell, PieChart, Pie
} from 'recharts';

export default function SearchVisibility({ filters, colors }) {
  const [rankings, setRankings] = useState([]);
  const [sov, setSov] = useState([]);
  const [byKeyword, setByKeyword] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      fetchApi('/serp/rankings'),
      fetchApi('/serp/share-of-voice'),
      fetchApi('/serp/by-keyword'),
    ]).then(([r, s, k]) => {
      setRankings(r);
      setSov(s);
      setByKeyword(k);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, [filters]);

  if (loading) return <div style={{ color: '#71717a', padding: '40px', textAlign: 'center' }}>Loading...</div>;

  // Map domains to brands for coloring
  const domainBrand = {
    'tkocombat.com': 'TKO Combat',
    'centurymartialarts.com': 'Century Martial Arts',
    'everlast.com': 'Everlast',
    'hayabusafight.com': 'Hayabusa',
    'venum.com': 'Venum',
    'rdxsports.com': 'RDX Sports',
    'amazon.com': '#f59e0b',
    'walmart.com': '#3b82f6',
    'target.com': '#ef4444',
  };

  const sovData = sov.map(s => ({
    name: s.domain_name,
    value: parseFloat(s.share_of_voice),
  }));

  // Top domains by avg position
  const domainAvg = {};
  rankings.forEach(r => {
    if (!domainAvg[r.domain_name]) domainAvg[r.domain_name] = { domain: r.domain_name, positions: [], appearances: 0 };
    domainAvg[r.domain_name].positions.push(parseFloat(r.avg_position));
    domainAvg[r.domain_name].appearances += parseInt(r.appearances);
  });
  const topDomains = Object.values(domainAvg)
    .map(d => ({ ...d, avg_position: Math.round(d.positions.reduce((a, b) => a + b, 0) / d.positions.length * 10) / 10 }))
    .sort((a, b) => a.avg_position - b.avg_position)
    .slice(0, 12);

  // Keyword analysis
  const keywords = [...new Set(byKeyword.map(k => k.keyword_category))];
  const keywordData = keywords.map(kw => {
    const row = { keyword: kw };
    byKeyword.filter(k => k.keyword_category === kw).forEach(k => {
      row[k.domain_name] = parseFloat(k.avg_position);
    });
    return row;
  });
  const allDomains = [...new Set(byKeyword.map(k => k.domain_name))].slice(0, 8);

  return (
    <div>
      <h2 style={sectionTitle}>Search Visibility (SERP)</h2>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '16px' }}>
        <div style={card}>
          <h3 style={chartTitle}>Share of Voice (Top 10 Results)</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie data={sovData} cx="50%" cy="50%" innerRadius={50} outerRadius={100}
                paddingAngle={2} dataKey="value"
                label={({ name, value }) => `${name}: ${value}%`}
                labelLine={{ stroke: '#71717a' }}
              >
                {sovData.map((d, i) => {
                  const brand = domainBrand[d.name];
                  const fill = typeof brand === 'string' && brand.startsWith('#') ? brand : (colors[brand] || `hsl(${i * 40}, 60%, 50%)`);
                  return <Cell key={i} fill={fill} />;
                })}
              </Pie>
              <Tooltip contentStyle={tooltipStyle} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div style={card}>
          <h3 style={chartTitle}>Average Search Position by Domain</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={topDomains} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#2a2d3a" />
              <XAxis type="number" stroke="#71717a" tick={{ fontSize: 11 }} reversed />
              <YAxis dataKey="domain" type="category" stroke="#71717a" tick={{ fontSize: 10 }} width={150} />
              <Tooltip contentStyle={tooltipStyle} />
              <Bar dataKey="avg_position" name="Avg Position" radius={[0, 4, 4, 0]}>
                {topDomains.map((d, i) => {
                  const brand = domainBrand[d.domain];
                  const fill = typeof brand === 'string' && brand.startsWith('#') ? brand : (colors[brand] || '#6366f1');
                  return <Cell key={i} fill={fill} />;
                })}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div style={card}>
        <h3 style={chartTitle}>Rankings by Keyword Category</h3>
        <div style={{ overflowX: 'auto' }}>
          <table style={tableStyle}>
            <thead>
              <tr>
                <th style={th}>Keyword</th>
                {allDomains.map(d => <th key={d} style={th}>{d}</th>)}
              </tr>
            </thead>
            <tbody>
              {keywordData.map(row => (
                <tr key={row.keyword}>
                  <td style={tdBold}>{row.keyword}</td>
                  {allDomains.map(d => {
                    const val = row[d];
                    const bg = val && val <= 5 ? '#22c55e20' : val && val <= 10 ? '#f59e0b20' : 'transparent';
                    return <td key={d} style={{ ...tdCell, background: bg }}>{val ? val.toFixed(1) : '—'}</td>;
                  })}
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
const card = { background: '#161821', borderRadius: '8px', padding: '16px 20px', border: '1px solid #2a2d3a' };
const tooltipStyle = { background: '#1a1c28', border: '1px solid #2a2d3a', borderRadius: '6px', fontSize: '12px' };
const tableStyle = { width: '100%', borderCollapse: 'collapse', fontSize: '12px' };
const th = { textAlign: 'left', padding: '6px 10px', borderBottom: '1px solid #2a2d3a', color: '#71717a', fontWeight: 500, fontSize: '10px', textTransform: 'uppercase' };
const tdBold = { padding: '6px 10px', borderBottom: '1px solid #1e2030', fontWeight: 500, color: '#e4e4e7' };
const tdCell = { padding: '6px 10px', borderBottom: '1px solid #1e2030', textAlign: 'center', color: '#a1a1aa' };

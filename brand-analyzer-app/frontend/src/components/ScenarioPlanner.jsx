import React, { useState, useEffect } from 'react';
import { fetchApi } from '../utils/api';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell, AreaChart, Area
} from 'recharts';

export default function ScenarioPlanner({ filters, colors }) {
  const [priceChange, setPriceChange] = useState(0);
  const [ratingChange, setRatingChange] = useState(0);
  const [availChange, setAvailChange] = useState(0);
  const [result, setResult] = useState(null);
  const [baseData, setBaseData] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchApi('/scenario/base-data', filters).then(setBaseData).catch(() => {});
  }, [filters]);

  useEffect(() => {
    setLoading(true);
    fetchApi('/scenario/simulate', {
      price_change_pct: priceChange,
      rating_change: ratingChange,
      availability_change: availChange,
    }).then(r => {
      setResult(r);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, [priceChange, ratingChange, availChange]);

  const leverData = result ? [
    { name: 'Price', value: result.lever_importance.price, fill: '#e63946' },
    { name: 'Rating', value: result.lever_importance.rating, fill: '#2a9d8f' },
    { name: 'Availability', value: result.lever_importance.availability, fill: '#457b9d' },
  ] : [];

  const histogram = result?.monte_carlo_histogram?.filter(h => h.count > 0) || [];

  return (
    <div>
      <h2 style={sectionTitle}>Scenario Planner</h2>
      <p style={{ color: '#71717a', fontSize: '13px', marginTop: '-8px', marginBottom: '16px' }}>
        Adjust parameters to simulate market share impact for TKO Combat
      </p>

      <div style={{ display: 'grid', gridTemplateColumns: '350px 1fr', gap: '20px' }}>
        {/* Controls */}
        <div style={card}>
          <h3 style={chartTitle}>Scenario Parameters</h3>

          <div style={sliderGroup}>
            <div style={sliderLabel}>
              <span>Price Change</span>
              <span style={{ color: priceChange < 0 ? '#22c55e' : priceChange > 0 ? '#ef4444' : '#a1a1aa', fontWeight: 600 }}>
                {priceChange > 0 ? '+' : ''}{priceChange}%
              </span>
            </div>
            <input type="range" min={-30} max={30} value={priceChange}
              onChange={e => setPriceChange(Number(e.target.value))} style={slider} />
            <div style={sliderRange}><span>-30%</span><span>+30%</span></div>
          </div>

          <div style={sliderGroup}>
            <div style={sliderLabel}>
              <span>Rating Change</span>
              <span style={{ color: ratingChange > 0 ? '#22c55e' : ratingChange < 0 ? '#ef4444' : '#a1a1aa', fontWeight: 600 }}>
                {ratingChange > 0 ? '+' : ''}{ratingChange.toFixed(1)}
              </span>
            </div>
            <input type="range" min={-10} max={10} value={ratingChange * 10}
              onChange={e => setRatingChange(Number(e.target.value) / 10)} style={slider} />
            <div style={sliderRange}><span>-1.0</span><span>+1.0</span></div>
          </div>

          <div style={sliderGroup}>
            <div style={sliderLabel}>
              <span>Availability Change</span>
              <span style={{ color: availChange > 0 ? '#22c55e' : availChange < 0 ? '#ef4444' : '#a1a1aa', fontWeight: 600 }}>
                {availChange > 0 ? '+' : ''}{availChange}%
              </span>
            </div>
            <input type="range" min={-20} max={20} value={availChange}
              onChange={e => setAvailChange(Number(e.target.value))} style={slider} />
            <div style={sliderRange}><span>-20%</span><span>+20%</span></div>
          </div>

          <div style={{ marginTop: '20px', padding: '12px', background: '#0f1117', borderRadius: '8px' }}>
            <div style={{ fontSize: '11px', color: '#71717a', textTransform: 'uppercase', marginBottom: '4px' }}>Scenario Summary</div>
            <div style={{ fontSize: '12px', color: '#a1a1aa', lineHeight: 1.6 }}>
              {priceChange !== 0 && <div>{priceChange < 0 ? 'Decrease' : 'Increase'} price by {Math.abs(priceChange)}%</div>}
              {ratingChange !== 0 && <div>{ratingChange > 0 ? 'Improve' : 'Decrease'} rating by {Math.abs(ratingChange).toFixed(1)}</div>}
              {availChange !== 0 && <div>{availChange > 0 ? 'Improve' : 'Decrease'} availability by {Math.abs(availChange)}%</div>}
              {priceChange === 0 && ratingChange === 0 && availChange === 0 && <div>No changes (baseline)</div>}
            </div>
          </div>
        </div>

        {/* Results */}
        <div>
          {result && (
            <>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', marginBottom: '16px' }}>
                <div style={{ ...resultCard, borderColor: result.share_delta >= 0 ? '#22c55e' : '#ef4444' }}>
                  <div style={resultLabel}>Projected Share</div>
                  <div style={{ ...resultValue, color: result.share_delta >= 0 ? '#22c55e' : '#ef4444' }}>
                    {result.projected_share}%
                  </div>
                  <div style={resultSub}>{result.share_delta >= 0 ? '+' : ''}{result.share_delta}% change</div>
                </div>
                <div style={resultCard}>
                  <div style={resultLabel}>90% Confidence</div>
                  <div style={resultValue}>{result.confidence_interval[0]}% - {result.confidence_interval[1]}%</div>
                  <div style={resultSub}>Monte Carlo (1K sims)</div>
                </div>
                <div style={resultCard}>
                  <div style={resultLabel}>P(Share &gt; 15%)</div>
                  <div style={resultValue}>{(result.probability_above_15pct * 100).toFixed(0)}%</div>
                  <div style={resultSub}>Probability</div>
                </div>
                <div style={{ ...resultCard, borderColor: result.revenue_change_pct >= 0 ? '#22c55e' : '#ef4444' }}>
                  <div style={resultLabel}>Revenue Impact</div>
                  <div style={{ ...resultValue, color: result.revenue_change_pct >= 0 ? '#22c55e' : '#ef4444' }}>
                    ${Number(result.projected_revenue).toLocaleString()}
                  </div>
                  <div style={resultSub}>{result.revenue_change_pct >= 0 ? '+' : ''}{result.revenue_change_pct}%</div>
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                <div style={card}>
                  <h3 style={chartTitle}>Lever Importance</h3>
                  <ResponsiveContainer width="100%" height={200}>
                    <BarChart data={leverData} layout="vertical">
                      <CartesianGrid strokeDasharray="3 3" stroke="#2a2d3a" />
                      <XAxis type="number" stroke="#71717a" tick={{ fontSize: 11 }} domain={[0, 100]} />
                      <YAxis dataKey="name" type="category" stroke="#71717a" tick={{ fontSize: 12 }} width={80} />
                      <Tooltip contentStyle={tooltipStyle} />
                      <Bar dataKey="value" name="Impact %" radius={[0, 4, 4, 0]}>
                        {leverData.map((d, i) => <Cell key={i} fill={d.fill} />)}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>

                <div style={card}>
                  <h3 style={chartTitle}>Monte Carlo Distribution</h3>
                  <ResponsiveContainer width="100%" height={200}>
                    <AreaChart data={histogram}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#2a2d3a" />
                      <XAxis dataKey="bucket" stroke="#71717a" tick={{ fontSize: 10 }} />
                      <YAxis stroke="#71717a" tick={{ fontSize: 11 }} />
                      <Tooltip contentStyle={tooltipStyle} />
                      <Area type="monotone" dataKey="count" stroke="#e63946" fill="#e6394630" strokeWidth={2} />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Base data table */}
      <div style={{ ...card, marginTop: '16px' }}>
        <h3 style={chartTitle}>Current Market Position (Base Data)</h3>
        <div style={{ overflowX: 'auto' }}>
          <table style={tableStyle}>
            <thead>
              <tr>
                <th style={th}>Brand</th>
                <th style={th}>Category</th>
                <th style={th}>Avg Price</th>
                <th style={th}>Rating</th>
                <th style={th}>Availability</th>
                <th style={th}>Products</th>
              </tr>
            </thead>
            <tbody>
              {baseData.filter(d => d.BRAND === 'TKO Combat').map((d, i) => (
                <tr key={i} style={{ background: '#1e2030' }}>
                  <td style={tdCell}>{d.BRAND}</td>
                  <td style={tdCell}>{d.category}</td>
                  <td style={tdCell}>${d.avg_price}</td>
                  <td style={tdCell}>{d.avg_rating}</td>
                  <td style={tdCell}>{d.availability_pct}%</td>
                  <td style={tdCell}>{d.product_count}</td>
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

const sliderGroup = { marginBottom: '20px' };
const sliderLabel = { display: 'flex', justifyContent: 'space-between', fontSize: '13px', color: '#e4e4e7', marginBottom: '6px' };
const slider = { width: '100%', accentColor: '#e63946' };
const sliderRange = { display: 'flex', justifyContent: 'space-between', fontSize: '10px', color: '#71717a', marginTop: '2px' };

const resultCard = { background: '#161821', borderRadius: '8px', padding: '14px 16px', border: '1px solid #2a2d3a' };
const resultLabel = { fontSize: '11px', color: '#71717a', textTransform: 'uppercase', letterSpacing: '0.5px' };
const resultValue = { fontSize: '22px', fontWeight: 700, color: '#fff', marginTop: '4px' };
const resultSub = { fontSize: '11px', color: '#a1a1aa', marginTop: '2px' };

const tableStyle = { width: '100%', borderCollapse: 'collapse', fontSize: '12px' };
const th = { textAlign: 'left', padding: '6px 10px', borderBottom: '1px solid #2a2d3a', color: '#71717a', fontWeight: 500, fontSize: '10px', textTransform: 'uppercase' };
const tdCell = { padding: '6px 10px', borderBottom: '1px solid #1e2030' };

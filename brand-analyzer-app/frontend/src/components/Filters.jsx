import React from 'react';

export default function Filters({ filters, setFilters, options }) {
  const update = (key, val) => setFilters(f => ({ ...f, [key]: val || null }));

  return (
    <div style={styles.bar}>
      <div style={styles.group}>
        <label style={styles.label}>From</label>
        <input
          type="date"
          value={filters.start_date}
          onChange={e => update('start_date', e.target.value)}
          style={styles.input}
        />
      </div>
      <div style={styles.group}>
        <label style={styles.label}>To</label>
        <input
          type="date"
          value={filters.end_date}
          onChange={e => update('end_date', e.target.value)}
          style={styles.input}
        />
      </div>
      <div style={styles.group}>
        <label style={styles.label}>Retailer</label>
        <select
          value={filters.retailers || ''}
          onChange={e => update('retailers', e.target.value)}
          style={styles.input}
        >
          <option value="">All Retailers</option>
          {(options.retailers || []).map(r => (
            <option key={r} value={r}>{r}</option>
          ))}
        </select>
      </div>
      <div style={styles.group}>
        <label style={styles.label}>Category</label>
        <select
          value={filters.category || ''}
          onChange={e => update('category', e.target.value)}
          style={styles.input}
        >
          <option value="">All Categories</option>
          {(options.categories || []).map(c => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>
      </div>
    </div>
  );
}

const styles = {
  bar: {
    display: 'flex',
    gap: '16px',
    padding: '12px 24px',
    background: '#1a1c28',
    borderBottom: '1px solid #2a2d3a',
    flexWrap: 'wrap',
    alignItems: 'flex-end',
  },
  group: {
    display: 'flex',
    flexDirection: 'column',
    gap: '4px',
  },
  label: {
    fontSize: '11px',
    color: '#71717a',
    fontWeight: 500,
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
  },
  input: {
    padding: '6px 10px',
    background: '#0f1117',
    border: '1px solid #2a2d3a',
    borderRadius: '6px',
    color: '#e4e4e7',
    fontSize: '13px',
    fontFamily: 'inherit',
    outline: 'none',
    minWidth: '140px',
  },
};

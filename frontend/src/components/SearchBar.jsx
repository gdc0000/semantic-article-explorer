// SearchBar.jsx
import React from 'react';

const SearchBar = ({ query, onChange, onSearch }) => {
  return (
    <div style={{ marginBottom: '1rem' }}>
      <input
        type="text"
        placeholder="Search articles..."
        value={query}
        onChange={e => onChange(e.target.value)}
        style={{ padding: '0.5rem', width: '70%' }}
      />
      <button onClick={onSearch} style={{ marginLeft: '0.5rem', padding: '0.5rem' }}>
        Search
      </button>
    </div>
  );
};

export default SearchBar;

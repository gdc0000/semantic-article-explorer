// App.jsx
import React, { useEffect, useState } from 'react';
import SearchBar from './components/SearchBar';
import SemanticMap from './components/SemanticMap';
import ArticleDetails from './components/ArticleDetails';

function App() {
  const [articles, setArticles] = useState([]);
  const [query, setQuery] = useState('');
  const [selectedId, setSelectedId] = useState(null);
  const [filtered, setFiltered] = useState([]);

  useEffect(() => {
    fetch('/mock_articles.json')
      .then(res => res.json())
      .then(data => {
        setArticles(data);
        setFiltered(data);
      });
  }, []);

  const handleSearch = () => {
    const q = query.toLowerCase();
    setFiltered(
      articles.filter(a => a.title.toLowerCase().includes(q) || a.abstract.toLowerCase().includes(q))
    );
    setSelectedId(null);
  };

  const selectedArticle = articles.find(a => a.id === selectedId);

  return (
    <div style={{ padding: '2rem' }}>
      <h1>Semantic Article Explorer</h1>
      <SearchBar query={query} onChange={setQuery} onSearch={handleSearch} />
      <SemanticMap articles={filtered} onPointClick={setSelectedId} selectedId={selectedId} />
      <hr />
      <ArticleDetails article={selectedArticle} />
    </div>
  );
}

export default App;

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

const handleSearch = async () => {
  try {
    // const response = await fetch('http://127.0.0.1:8000/search', {
    const response = await fetch('http://localhost:8000/search', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query }),
    });

    if (!response.ok) throw new Error('Errore nella richiesta al backend');

    const data = await response.json();
    // Logga i risultati ricevuti dal backend
    console.log('Risultati ricevuti dal backend:', data.results);

    // I risultati sono stringhe, quindi filtriamo gli articoli che matchano
    const filteredArticles = articles.filter(article =>
      data.results.some(result =>
        article.title.toLowerCase().includes(result.toLowerCase()) ||
        article.abstract.toLowerCase().includes(result.toLowerCase())
      )
    );

    setFiltered(filteredArticles);
    setSelectedId(null);
  } catch (error) {
    console.error('Errore nel fetch:', error);
  }
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

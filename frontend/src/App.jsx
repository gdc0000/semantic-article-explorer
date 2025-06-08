import React, { useEffect, useState } from 'react';
import SearchBar from './components/SearchBar';
import SemanticMap from './components/SemanticMap';
import ArticleDetails from './components/ArticleDetails';

function App() {
  const [articles, setArticles] = useState([]);          // Full original dataset
  const [initialArticles, setInitialArticles] = useState([]); // Save initial snapshot
  const [query, setQuery] = useState('');
  const [selectedId, setSelectedId] = useState(null);
  const [filtered, setFiltered] = useState([]);

  // Load initial data once on component mount
  useEffect(() => {
    fetch("http://localhost:8000/raw-data")
      .then(res => {
        if (!res.ok) throw new Error("Failed to fetch initial article data");
        return res.json();
      })
      .then(data => {
        setArticles(data);           // Main data used in search/similar
        setInitialArticles(data);    // Static snapshot for reset
        setFiltered(data);           // Initially, show everything
        console.log("✅ Loaded initial data:", data);
      })
      .catch(err => {
        console.error("❌ Error fetching initial data:", err);
      });
  }, []);

  // Handler: Semantic search
  const handleSearch = async () => {
    try {
      console.log("Sending query:", query);

      const response = await fetch('http://localhost:8000/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error("Backend returned error:", errorText);
        throw new Error('Failed to get results from backend');
      }

      const data = await response.json();
      console.log("✅ Backend search results:", data.results);

      const resultIds = data.results.map(result => result.id);

      const filteredArticles = articles.filter(article =>
        resultIds.includes(article.id)
      );

      setFiltered(filteredArticles);
      setSelectedId(null);
    } catch (error) {
      console.error("❌ Error during search fetch:", error);
    }
  };


  // Handler: Find similar articles given an ID
  const handleFindSimilar = async (articleId) => {
    try {
      console.log("Requesting similar articles for ID:", articleId);

      const response = await fetch(`http://localhost:8000/similar/${articleId}`);
      if (!response.ok) {
        const errorText = await response.text();
        console.error("Backend error:", errorText);
        throw new Error('Failed to get similar articles');
      }

      const data = await response.json();
      console.log("✅ Similar results:", data.results);

      const similarArticles = articles.filter(article =>
        data.results.includes(article.id)
      );

      setFiltered(similarArticles);
      setSelectedId(null);
    } catch (error) {
      console.error("❌ Error during similarity fetch:", error);
    }
  };

  // 🔁 Reset map to initial state
  const handleReset = () => {
    setFiltered(initialArticles);
    setSelectedId(null);
    setQuery('');
    console.log("🔄 Reset to full article list");
  };

  // Get full article info for the detail pane
  const selectedArticle = filtered.find(a => a.id === selectedId);

  return (
    <div style={{ padding: '2rem' }}>
      <h1>Semantic Article Explorer</h1>

      {/* Search bar */}
      <SearchBar query={query} onChange={setQuery} onSearch={handleSearch} />

      {/* Refresh button */}
      <button onClick={handleReset} style={{ marginBottom: '1rem' }}>
        🔄 Refresh map
      </button>

      {/* Map with scatterplot */}
      <SemanticMap
        articles={filtered}
        onPointClick={setSelectedId}
        selectedId={selectedId}
      />

      <hr />

      {/* Details panel */}
      <ArticleDetails article={selectedArticle} onFindSimilar={handleFindSimilar} />
    </div>
  );
}

export default App;
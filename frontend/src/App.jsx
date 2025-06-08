// App.jsx
import React, { useEffect, useState } from 'react';
import SearchBar from './components/SearchBar';
import SemanticMap from './components/SemanticMap';
import ArticleDetails from './components/ArticleDetails';

function App() {
  // State to store all articles from backend
  const [articles, setArticles] = useState([]);

  // State to store the user's search input
  const [query, setQuery] = useState('');

  // State to store the ID of the selected article (for details)
  const [selectedId, setSelectedId] = useState(null);

  // State to store only the articles matching the current query
  const [filtered, setFiltered] = useState([]);

  // 🔁 Run only once on page load: fetch initial dataset from backend
  useEffect(() => {
    fetch("http://localhost:8000/raw-data")
      .then(res => {
        if (!res.ok) throw new Error("Failed to fetch initial article data");
        return res.json(); // Convert response to JSON
      })
      .then(data => {
        setArticles(data);     // Store all articles
        setFiltered(data);     // Show all articles by default
        console.log("✅ Loaded initial data:", data);
      })
      .catch(err => {
        console.error("❌ Error fetching initial data:", err);
      });
  }, []);

  // 🔍 Called when user clicks the search button
  const handleSearch = async () => {
    try {
      console.log("Sending query:", query);

      // Send search query to FastAPI backend
      const response = await fetch('http://localhost:8000/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query }), // Wrap query in JSON
      });

      console.log("Backend raw response:", response);

      if (!response.ok) {
        const errorText = await response.text();
        console.error("Backend returned error:", errorText);
        throw new Error('Failed to get results from backend');
      }

      const data = await response.json();
      console.log("✅ Backend search results:", data.results);

      // Match backend result titles with full article objects
      const filteredArticles = articles.filter(article =>
        data.results.some(result =>
          article.title.toLowerCase().includes(result.toLowerCase()) ||
          article.abstract.toLowerCase().includes(result.toLowerCase())
        )
      );

      // Update the filtered articles and reset selection
      setFiltered(filteredArticles);
      setSelectedId(null);
    } catch (error) {
      console.error("❌ Error during search fetch:", error);
    }
  };

  // Find the full article object from its ID
  const selectedArticle = filtered.find(a => a.id === selectedId);

  // 🔧 Render the full app layout
  return (
    <div style={{ padding: '2rem' }}>
      <h1>Semantic Article Explorer</h1>

      {/* Top search bar with input and button */}
      <SearchBar query={query} onChange={setQuery} onSearch={handleSearch} />

      {/* Scatterplot of filtered articles */}
      <SemanticMap
        articles={filtered}
        onPointClick={setSelectedId}
        selectedId={selectedId}
      />

      <hr />

      {/* Display article details when a point is clicked */}
      <ArticleDetails article={selectedArticle} />
    </div>
  );
}

export default App;

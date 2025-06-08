// frontend/src/components/ArticleDetails.jsx
import React from 'react';

function ArticleDetails({ article, onFindSimilar }) {
  // If no article is selected, show a placeholder message
  if (!article) {
    return <p>Select an article from the map to view details.</p>;
  }

  return (
    <div style={{ marginTop: '1rem' }}>
      {/* Article title */}
      <h2>{article.title}</h2>

      {/* Metadata: authors, journal, year */}
      <p>
        <strong>Authors:</strong> {Array.isArray(article.authors) ? article.authors.join(', ') : article.authors}<br />
        <strong>Journal:</strong> {article.journal}<br />
        <strong>Year:</strong> {article.year}
      </p>

      {/* Abstract section */}
      <div>
        <strong>Abstract:</strong>
        <p>{article.abstract || "No abstract available."}</p>
      </div>

      {/* "Find Similar" button, visible only if a handler is passed */}
      {onFindSimilar && (
        <button
          onClick={() => onFindSimilar(article.id)}
          style={{
            marginTop: '1rem',
            padding: '0.5rem 1rem',
            backgroundColor: '#333',
            color: 'white',
            border: 'none',
            cursor: 'pointer',
            borderRadius: '4px'
          }}
        >
          🔍 Find Similar
        </button>
      )}
    </div>
  );
}

export default ArticleDetails;

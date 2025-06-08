// ArticleDetails.jsx
import React from 'react';

const ArticleDetails = ({ article }) => {
  if (!article) {
    return <p>Select an article from the map to view details.</p>;
  }

  return (
    <div>
      <h3>{article.title}</h3>
      <p><strong>ID:</strong> {article.id}</p>
      <p><strong>Journal:</strong> {article.journal}</p>
      <p><strong>Year:</strong> {article.year}</p>
      <p><strong>Abstract:</strong><br />{article.abstract}</p>
    </div>
  );
};

export default ArticleDetails;
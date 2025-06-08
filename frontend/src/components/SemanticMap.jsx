// SemanticMap.jsx
import React from 'react';
import Plot from 'react-plotly.js';

const SemanticMap = ({ articles, onPointClick, selectedId }) => {
  const data = [
    {
      x: articles.map(a => a.x),
      y: articles.map(a => a.y),
      text: articles.map(a => a.title),
      type: 'scatter',
      mode: 'markers',
      marker: {
        size: 10,
        color: articles.map(a => (a.id === selectedId ? 'red' : 'blue')),
      },
      customdata: articles.map(a => a.id),
    },
  ];

  const layout = {
    title: 'Semantic Map (UMAP)',
    hovermode: 'closest',
    height: 500,
  };

  const handleClick = event => {
    if (event.points && event.points.length > 0) {
      const clickedId = event.points[0].customdata;
      onPointClick(clickedId);
    }
  };

  return <Plot data={data} layout={layout} onClick={handleClick} />;
};

export default SemanticMap;

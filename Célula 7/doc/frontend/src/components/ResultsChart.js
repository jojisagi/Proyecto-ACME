import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const ResultsChart = ({ data }) => {
  const chartData = data.map(item => ({
    name: item.gadgetName.length > 15 
      ? item.gadgetName.substring(0, 15) + '...' 
      : item.gadgetName,
    votos: item.totalVotes,
    porcentaje: item.percentage
  }));

  return (
    <div style={{ width: '100%', height: 300, marginTop: 20 }}>
      <ResponsiveContainer>
        <BarChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis 
            dataKey="name" 
            angle={-45} 
            textAnchor="end" 
            height={100}
            style={{ fontSize: '0.8rem' }}
          />
          <YAxis />
          <Tooltip />
          <Legend />
          <Bar dataKey="votos" fill="#667eea" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default ResultsChart;

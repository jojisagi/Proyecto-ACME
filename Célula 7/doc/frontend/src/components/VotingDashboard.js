import React, { useState, useEffect } from 'react';
import { getResults, emitVote } from '../services/api';
import './VotingDashboard.css';
import ResultsChart from './ResultsChart';

const VotingDashboard = ({ user }) => {
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(true);
  const [hasVoted, setHasVoted] = useState(false);
  const [selectedGadget, setSelectedGadget] = useState(null);
  const [voting, setVoting] = useState(false);
  const [message, setMessage] = useState(null);

  useEffect(() => {
    fetchResults();
    const interval = setInterval(fetchResults, 3000); // Actualizar cada 3 segundos
    return () => clearInterval(interval);
  }, []);

  const fetchResults = async () => {
    try {
      const data = await getResults();
      setResults(data.results || []);
      setLoading(false);
    } catch (error) {
      console.error('Error al obtener resultados:', error);
      setLoading(false);
    }
  };

  const handleVote = async (gadgetId) => {
    if (hasVoted || voting) return;

    setVoting(true);
    setSelectedGadget(gadgetId);

    try {
      await emitVote(gadgetId, user.idToken);
      setHasVoted(true);
      setMessage({ type: 'success', text: '¡Voto registrado exitosamente!' });
      
      // Actualizar resultados inmediatamente
      setTimeout(fetchResults, 1000);
    } catch (error) {
      if (error.response?.status === 409) {
        setHasVoted(true);
        setMessage({ type: 'info', text: 'Ya has votado anteriormente' });
      } else {
        setMessage({ type: 'error', text: 'Error al registrar el voto' });
      }
    } finally {
      setVoting(false);
    }
  };

  if (loading) {
    return <div className="dashboard-loading">Cargando resultados...</div>;
  }

  const totalVotes = results.reduce((sum, r) => sum + r.totalVotes, 0);

  return (
    <div className="voting-dashboard">
      {message && (
        <div className={`message ${message.type}`}>
          {message.text}
        </div>
      )}

      <div className="dashboard-grid">
        <div className="gadgets-section">
          <h2>🎮 Gadgets Nominados</h2>
          <p className="section-subtitle">
            {hasVoted ? 'Gracias por votar' : 'Selecciona tu gadget favorito'}
          </p>
          
          <div className="gadgets-grid">
            {results.map((gadget) => (
              <div
                key={gadget.gadgetId}
                className={`gadget-card ${hasVoted ? 'disabled' : ''} ${
                  selectedGadget === gadget.gadgetId ? 'selected' : ''
                }`}
                onClick={() => !hasVoted && handleVote(gadget.gadgetId)}
              >
                <div className="gadget-icon">🔥</div>
                <h3>{gadget.gadgetName}</h3>
                <div className="vote-stats">
                  <div className="vote-count">{gadget.totalVotes} votos</div>
                  <div className="vote-percentage">{gadget.percentage}%</div>
                </div>
                <div className="progress-bar">
                  <div
                    className="progress-fill"
                    style={{ width: `${gadget.percentage}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="results-section">
          <h2>📊 Resultados en Tiempo Real</h2>
          <div className="total-votes">
            Total de votos: <strong>{totalVotes}</strong>
          </div>
          
          <ResultsChart data={results} />

          <div className="top-gadgets">
            <h3>🏆 Top 3</h3>
            {results.slice(0, 3).map((gadget, index) => (
              <div key={gadget.gadgetId} className="top-gadget-item">
                <span className="rank">#{index + 1}</span>
                <span className="name">{gadget.gadgetName}</span>
                <span className="votes">{gadget.totalVotes} votos</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default VotingDashboard;

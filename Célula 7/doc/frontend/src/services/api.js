import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_ENDPOINT || 'https://YOUR-API-ID.execute-api.YOUR-REGION.amazonaws.com/prod';

// Obtener resultados de votación
export const getResults = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/results`);
    return response.data;
  } catch (error) {
    console.error('Error al obtener resultados:', error);
    throw error;
  }
};

// Emitir un voto
export const emitVote = async (gadgetId, idToken) => {
  try {
    const response = await axios.post(
      `${API_BASE_URL}/vote`,
      { gadgetId },
      {
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${idToken}`
        }
      }
    );
    return response.data;
  } catch (error) {
    console.error('Error al emitir voto:', error);
    throw error;
  }
};

// services/api.js
const API_BASE_URL = 'http://localhost:8000';

export const sendCommand = async (portNumber, command) => {
  try {
    const response = await fetch(`${API_BASE_URL}/send_command/${portNumber}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ command }),
    });

    if (!response.ok) {
      throw new Error('Erro ao enviar comando');
    }

    return await response.json();
  } catch (error) {
    console.error('Erro:', error);
    throw error;
  }
};

// ADICIONE ESTA FUNÇÃO
export const startCalibration = async (portNumber = 1) => {
  try {
    const response = await sendCommand(portNumber, 'START_CALIBRATION');
    return response;
  } catch (error) {
    console.error('Erro na calibração:', error);
    throw error;
  }
};

// Ou se quiser uma função mais genérica
export const startTest = async (portNumber = 1) => {
  try {
    const response = await sendCommand(portNumber, 'START');
    return response;
  } catch (error) {
    console.error('Erro ao iniciar teste:', error);
    throw error;
  }
};
// src/services/api.js

const API_BASE_URL = 'http://localhost:8000';

// =========================
// Função genérica
// =========================
export const sendCommand = async (portNumber, command) => {
  try {
    const response = await fetch(`${API_BASE_URL}/send_command/${portNumber}?command=${encodeURIComponent(command)}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) throw new Error('Erro ao enviar comando');

    return await response.json();
  } catch (error) {
    console.error('Erro no sendCommand:', error);
    throw error;
  }
};

// =========================
// Status do servidor
// =========================
export const checkServerStatus = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/status`);
    return response.ok;
  } catch (error) {
    return false;
  }
};

// =========================
// COMANDOS
// =========================
export const startCalibration = async (portNumber = 1) => {
  return await sendCommand(portNumber, 'START_CALIBRATION');
};

export const startTest = async (portNumber = 1) => {
  return await sendCommand(portNumber, 'START');
};

export const executeFingerDown = async (portNumber = 1) => {
  return await sendCommand(portNumber, 'FINGER_DOWN');
};

// =========================
// OBJETO AGRUPADO
// =========================
export const apiService = {
  sendCommand,
  checkServerStatus,
  startCalibration,
  startTest,
  executeFingerDown,
};

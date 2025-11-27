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
// Portas Seriais
// =========================
export const getSerialPorts = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/get_serial_ports`);
    
    if (!response.ok) {
      throw new Error('Erro ao buscar portas seriais');
    }

    const data = await response.json();
    
    if (data.status === 'error') {
      throw new Error(data.message);
    }
    
    return data;
  } catch (error) {
    console.error('Erro ao buscar portas seriais:', error);
    throw error;
  }
};

export const connectPort = async (portNumber, portName) => {
  try {
    const response = await fetch(`${API_BASE_URL}/connect_port/${portNumber}?port_name=${encodeURIComponent(portName)}`);
    
    if (!response.ok) {
      throw new Error('Erro ao conectar porta');
    }

    const data = await response.json();
    
    if (data.status === 'error') {
      throw new Error(data.message);
    }
    
    return data;
  } catch (error) {
    console.error('Erro ao conectar porta:', error);
    throw error;
  }
};

export const disconnectPort = async (portNumber) => {
  try {
    const response = await fetch(`${API_BASE_URL}/disconnect_port/${portNumber}`);
    
    if (!response.ok) {
      throw new Error('Erro ao desconectar porta');
    }

    const data = await response.json();
    
    if (data.status === 'error') {
      throw new Error(data.message);
    }
    
    return data;
  } catch (error) {
    console.error('Erro ao desconectar porta:', error);
    throw error;
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
  getSerialPorts,
  connectPort,
  disconnectPort,
  startCalibration,
  startTest,
  executeFingerDown,
};

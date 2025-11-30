// src/services/api.js

const API_BASE_URL = 'http://localhost:8000';

// =========================
// Função genérica
// =========================
export const sendCommand = async (portNumber, command) => {
  try {
    const response = await fetch(`${API_BASE_URL}/send_command/${portNumber}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ command }),
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
export const startCalibration = async (portNumber = 2) => {
  // Calibração sempre usa porta 2 (GRBL) para enviar $H
  return await sendCommand(2, 'START_CALIBRATION');
};

export const startTest = async (portNumber = 1) => {
  return await sendCommand(portNumber, 'START');
};

export const executeFingerDown = async (portNumber = 1) => {
  return await sendCommand(portNumber, 'FINGER_DOWN');
};

export const executeFingerDownWithPhotos = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/start_complete_process_with_photos`, {
      method: 'POST',
    });
    if (!response.ok) throw new Error('Erro ao iniciar processo com fotos');
    return await response.json();
  } catch (error) {
    console.error('Erro ao executar fingerdown com fotos:', error);
    throw error;
  }
};

// =========================
// PORTAS SERIAIS
// =========================
export const getSerialPorts = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/get_serial_ports`);
    if (!response.ok) throw new Error('Erro ao buscar portas');
    return await response.json();
  } catch (error) {
    console.error('Erro ao buscar portas seriais:', error);
    throw error;
  }
};

export const connectPort = async (portNumber, portName, baudRate = null) => {
  try {
    let url = `${API_BASE_URL}/connect_port/${portNumber}?port_name=${encodeURIComponent(portName)}`;
    if (baudRate) {
      url += `&baud_rate=${baudRate}`;
    }
    const response = await fetch(url);
    if (!response.ok) throw new Error('Erro ao conectar porta');
    return await response.json();
  } catch (error) {
    console.error('Erro ao conectar porta:', error);
    throw error;
  }
};

export const disconnectPort = async (portNumber) => {
  try {
    const response = await fetch(`${API_BASE_URL}/disconnect_port/${portNumber}`);
    if (!response.ok) throw new Error('Erro ao desconectar porta');
    return await response.json();
  } catch (error) {
    console.error('Erro ao desconectar porta:', error);
    throw error;
  }
};

export const sendHomeCommand = async (portNumber) => {
  try {
    const response = await fetch(`${API_BASE_URL}/send_home/${portNumber}`, {
      method: 'POST',
    });
    if (!response.ok) throw new Error('Erro ao enviar comando Home');
    return await response.json();
  } catch (error) {
    console.error('Erro ao enviar comando Home:', error);
    throw error;
  }
};

// =========================
// CÂMERAS
// =========================
export const captureCameraFrame = async (cameraId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/capture_frame/${cameraId}`);
    if (!response.ok) throw new Error('Erro ao capturar frame');
    const blob = await response.blob();
    return blob;
  } catch (error) {
    console.error('Erro ao capturar frame:', error);
    throw error;
  }
};

export const saveCameraFrame = async (cameraId, filename = null) => {
  try {
    let url = `${API_BASE_URL}/save_camera_frame/${cameraId}`;
    if (filename) {
      url += `?filename=${encodeURIComponent(filename)}`;
    }
    const response = await fetch(url, { method: 'POST' });
    if (!response.ok) throw new Error('Erro ao salvar frame');
    return await response.json();
  } catch (error) {
    console.error('Erro ao salvar frame:', error);
    throw error;
  }
};

export const downloadCameraFrame = async (cameraId, filename = null) => {
  try {
    const blob = await captureCameraFrame(cameraId);
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename || `camera_${cameraId}_${new Date().getTime()}.jpg`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
    return { status: 'success', message: 'Foto baixada com sucesso' };
  } catch (error) {
    console.error('Erro ao baixar frame:', error);
    throw error;
  }
};

export const getTestReport = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/get_test_report`);
    if (!response.ok) throw new Error('Erro ao buscar relatório');
    return await response.json();
  } catch (error) {
    console.error('Erro ao buscar relatório:', error);
    throw error;
  }
};

export const getPneumaticMessage = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/get_pneumatic_message`);
    if (!response.ok) throw new Error('Erro ao buscar mensagem pneumática');
    return await response.json();
  } catch (error) {
    console.error('Erro ao buscar mensagem pneumática:', error);
    throw error;
  }
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
  executeFingerDownWithPhotos,
  getSerialPorts,
  connectPort,
  disconnectPort,
  sendHomeCommand,
  captureCameraFrame,
  saveCameraFrame,
  downloadCameraFrame,
  getTestReport,
  getPneumaticMessage,
};

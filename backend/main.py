from tempfile import template
from ir_reader import ir_reader, IRReader
from typing import Dict, Optional, Any
from pathlib import Path
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import serial
import serial.tools.list_ports
import asyncio
import time
from datetime import datetime
import os
from fastapi import HTTPException
import json
import cv2
import numpy as np
from contextlib import asynccontextmanager
import logging

import threading
import time
from concurrent.futures import ThreadPoolExecutor
from enum import Enum

# Configurar logging para câmeras
camera_logger = logging.getLogger("camera")
camera_logger.setLevel(logging.INFO)

# =========================
# GERENCIAMENTO DE CÂMERAS
# =========================
MAX_CAMERAS = 4
camera_managers: Dict[int, 'CameraManager'] = {}

class CameraManager:
    """Gerenciador de câmera com reconexão automática"""
    
    def __init__(self, camera_id: int):
        self.camera_id = camera_id
        self.cap: Optional[cv2.VideoCapture] = None
        self.latest_frame: Optional[np.ndarray] = None
        self.is_running = False
        self.lock = threading.Lock()
        self.thread: Optional[threading.Thread] = None
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 10
        self.reconnect_delay = 2  # segundos
        
    def connect(self) -> bool:
        """Tenta conectar à câmera"""
        try:
            if self.cap is not None:
                self.cap.release()
            
            self.cap = cv2.VideoCapture(self.camera_id)
            
            if not self.cap.isOpened():
                camera_logger.warning(f"Câmera {self.camera_id} não pôde ser aberta")
                return False
            
            # Configurar propriedades da câmera para melhor performance
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduzir buffer para frames mais recentes
            
            camera_logger.info(f"Câmera {self.camera_id} conectada com sucesso")
            self.reconnect_attempts = 0
            return True
            
        except Exception as e:
            camera_logger.error(f"Erro ao conectar câmera {self.camera_id}: {e}")
            return False
    
    def capture_loop(self):
        """Loop de captura em thread separada"""
        while self.is_running:
            try:
                if self.cap is None or not self.cap.isOpened():
                    if self.reconnect_attempts < self.max_reconnect_attempts:
                        camera_logger.info(f"Tentando reconectar câmera {self.camera_id}...")
                        if self.connect():
                            continue
                        else:
                            self.reconnect_attempts += 1
                            time.sleep(self.reconnect_delay)
                            continue
                    else:
                        camera_logger.error(f"Câmera {self.camera_id} não pôde ser reconectada após {self.max_reconnect_attempts} tentativas")
                        time.sleep(self.reconnect_delay)
                        continue
                
                ret, frame = self.cap.read()
                
                if not ret:
                    camera_logger.warning(f"Falha ao ler frame da câmera {self.camera_id}")
                    self.cap.release()
                    self.cap = None
                    continue
                
                with self.lock:
                    self.latest_frame = frame.copy()
                    
            except Exception as e:
                camera_logger.error(f"Erro na captura da câmera {self.camera_id}: {e}")
                if self.cap is not None:
                    try:
                        self.cap.release()
                    except:
                        pass
                    self.cap = None
                time.sleep(0.1)
    
    def start(self):
        """Inicia a captura da câmera"""
        if self.is_running:
            return
        
        if not self.connect():
            camera_logger.warning(f"Não foi possível conectar à câmera {self.camera_id} (pode não estar disponível)")
            return
        
        self.is_running = True
        self.thread = threading.Thread(target=self.capture_loop, daemon=True)
        self.thread.start()
        camera_logger.info(f"Câmera {self.camera_id} iniciada")
    
    def stop(self):
        """Para a captura da câmera"""
        self.is_running = False
        
        if self.thread is not None:
            self.thread.join(timeout=2)
        
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        
        camera_logger.info(f"Câmera {self.camera_id} parada")
    
    def get_frame(self) -> Optional[np.ndarray]:
        """Obtém o frame mais recente"""
        with self.lock:
            if self.latest_frame is not None:
                return self.latest_frame.copy()
        return None
    
    def is_connected(self) -> bool:
        """Verifica se a câmera está conectada"""
        return self.cap is not None and self.cap.isOpened()

def detect_cameras() -> list:
    """Detecta câmeras disponíveis"""
    available_cameras = []
    for i in range(MAX_CAMERAS):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            available_cameras.append(i)
            cap.release()
    return available_cameras

def generate_frame(camera_id: int):
    """Gera frames para streaming"""
    while True:
        manager = camera_managers.get(camera_id)
        if manager is None:
            break
        
        frame = manager.get_frame()
        
        if frame is None:
            # Enviar frame preto se não houver frame disponível
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(frame, f"Camera {camera_id} - Aguardando...", 
                       (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        # Codificar frame como JPEG
        ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        if not ret:
            continue
        
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        
        # Controlar FPS do stream
        time.sleep(1/30)  # ~30 FPS

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia o ciclo de vida da aplicação"""
    # Startup: Inicializar câmeras
    camera_logger.info("Inicializando câmeras...")
    available_cameras = detect_cameras()
    camera_logger.info(f"Câmeras detectadas: {available_cameras}")
    
    for camera_id in range(MAX_CAMERAS):
        manager = CameraManager(camera_id)
        camera_managers[camera_id] = manager
        try:
            manager.start()
        except Exception as e:
            camera_logger.error(f"Erro ao iniciar câmera {camera_id}: {e}")
    
    # Inicia escuta de comando START via pneumática
    pneumatic_task = asyncio.create_task(listen_pneumatic_start())
    print("✅ Escuta pneumática iniciada")
    
    yield
    
    # Shutdown: Parar todas as câmeras
    camera_logger.info("Parando todas as câmeras...")
    for manager in camera_managers.values():
        manager.stop()
    
    # Cancela task pneumática
    pneumatic_task.cancel()
    try:
        await pneumatic_task
    except asyncio.CancelledError:
        pass
    print("✅ Escuta pneumática parada")

app = FastAPI(title="Remote Control Tester Backend", lifespan=lifespan)

# CONFIGURAÇÃO CORS - DEVE VIR ANTES DE TODAS AS ROTAS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://127.0.0.1:8080", "http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/status")
async def status():
    """Endpoint para verificar status do servidor"""
    return JSONResponse(
        status_code=200,
        content={
            "status": "online",
            "timestamp": datetime.now().isoformat(),
            "message": "Servidor FastAPI está rodando"
        }
    )



# ESTADOS DA MÁQUINA
class MachineState(Enum):
    IDLE = "idle"
    MOVING = "moving"
    PRESSING = "pressing"
    EMERGENCY = "emergency"
    CALIBRATING = "calibrating"


# VARIÁVEIS GLOBAIS COM CONTROLE
fingerdown_running = False
current_test_cycle = 0
linha_atual = 0
libera_envio_comandos = False
machine_state = MachineState.IDLE


# LOCKS PARA SINCRONIZAÇÃO
serial_lock1 = threading.Lock()
serial_lock2 = threading.Lock()
serial_lock3 = threading.Lock()
state_lock = threading.Lock()


command_executor = ThreadPoolExecutor(max_workers=3, thread_name_prefix="MachineCmd")

def set_machine_state(new_state: MachineState):
    """Altera o estado da máquina com thread safety"""
    global machine_state
    with state_lock:
        old_state = machine_state
        machine_state = new_state
        print(f"🔄 MUDANÇA DE ESTADO: {old_state.value} -> {new_state.value}")

def get_machine_state() -> MachineState:
    """Retorna o estado atual da máquina"""
    with state_lock:
        return machine_state





# Variáveis globais para as portas seriais
serial_port1 = None  # Porta para comandos K/P (Arduino/Relés)
serial_port2 = None  # Porta para comandos G-code (GRBL)
serial_port3 = None  # Porta para receber dados IR (Nano)
serial_port4 = None  # Porta adicional

# Variáveis de controle
process_running = False
linha_atual = 0
libera_envio_comandos = False

# Variáveis específicas do FingerDown
fingerdown_running = False
current_test_cycle = 0
last_test_report = None  # Armazena o último relatório de validação
last_pneumatic_message = None  # Armazena a última mensagem recebida via pneumática



test_coordinates = [
    {"command": "G90", "x": 41, "y": 135, "nome": "POWER"},
    {"command": "G90", "x": 14, "y": 135, "nome": "FUNCAO"},
    {"command": "G90", "x": 28, "y": 127, "nome": "TEMP_MAX"},
    {"command": "G90", "x": 41, "y": 114, "nome": "TEMPORIZADOR"},
    {"command": "G90", "x": 41, "y": 114, "nome": "TEMPORIZADOR_2"},
    {"command": "G90", "x": 28, "y": 102, "nome": "TEMP_DOWN"},
    {"command": "G90", "x": 14, "y": 114, "nome": "VELOCIDADE"},
    {"command": "G90", "x": 14, "y": 94, "nome": "OSCILAR"},
    {"command": "G90", "x": 14, "y": 71, "nome": "TURBO"},
    {"command": "G90", "x": 24, "y": 71, "nome": "CONFORTO"},
    {"command": "G90", "x": 44, "y": 71, "nome": "IONAIR"},
    {"command": "G90", "x": 24, "y": 55, "nome": "VISOR"},
    {"command": "G90", "x": 14, "y": 55, "nome": "DORMIR"},
    {"command": "G90", "x": 41, "y": 135, "nome": "POWER_FINAL"},
    {"command": "G90", "x": 34, "y": 71, "nome": "LIMPAR"},
    {"command": "G90", "x": 34, "y": 55, "nome": "ANTIMORFO"}
    #{"command": "G90", "x": 42, "y": 96},      # OCULTO ABAIXO TEMPORIZADOR
    #{"command": "G90", "x": 44, "y": 55},      # OCULTO ABAIXO IONAIR
]





html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>Teste IR - FingerDown + Início1</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            max-width: 1000px; 
            margin: 0 auto; 
            padding: 20px; 
            background-color: #f5f5f5;
        }
        .container { 
            background: white; 
            padding: 20px; 
            border-radius: 10px; 
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .status { 
            padding: 10px; 
            margin: 10px 0; 
            border-radius: 5px; 
        }
        .connected { background-color: #d4edda; color: #155724; }
        .disconnected { background-color: #f8d7da; color: #721c24; }
        button { 
            padding: 10px 20px; 
            margin: 5px; 
            background-color: #007bff; 
            color: white; 
            border: none; 
            border-radius: 5px; 
            cursor: pointer;
        }
        button:hover { background-color: #0056b3; }
        button:disabled { 
            background-color: #6c757d; 
            cursor: not-allowed;
        }
        .port-select { 
            padding: 8px; 
            margin: 5px; 
            border-radius: 5px; 
            border: 1px solid #ccc;
            width: 250px;
        }
        .refresh-btn { background-color: #28a745; }
        .refresh-btn:hover { background-color: #218838; }
        .home-btn { background-color: #ffc107; color: black; }
        .home-btn:hover { background-color: #e0a800; }
        .log-info { color: #17a2b8; }
        .log-success { color: #28a745; }
        .log-error { color: #dc3545; }
        .log-warning { color: #ffc107; }
        .log-ir { color: #6f42c1; font-weight: bold; }
        .port-section {
            margin-bottom: 15px;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
        }
        .command-section {
            margin: 20px 0;
            padding: 15px;
            border: 1px solid #ddd;
            border-radius: 5px;
            background-color: #f8f9fa;
        }
        .command-btn { background-color: #6f42c1; }
        .command-btn:hover { background-color: #5a2d9c; }
        .command-btn-port2 { background-color: #e83e8c; }
        .command-btn-port2:hover { background-color: #d91a72; }
        .command-btn-port3 { background-color: #20c997; }
        .command-btn-port3:hover { background-color: #199d76; }
        .status-panel {
            background: #e9ecef;
            padding: 15px;
            border-radius: 5px;
            margin: 10px 0;
        }
        .ir-data {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
            font-family: monospace;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🧪 Teste IR - FingerDown + Início1</h1>
        
        <div class="status-panel">
            <h3>Status do Sistema</h3>
            <div><strong>Processo Ativo:</strong> <span id="processStatus">Não</span></div>
            <div><strong>Comandos Liberados:</strong> <span id="commandStatus">Não</span></div>
            <div><strong>Linha Atual:</strong> <span id="currentLine">0</span></div>
            <div><strong>Dados IR Recebidos:</strong> <span id="irCount">0</span></div>
        </div>
        
        <div class="controls">
            <h3>Configuração das Portas Seriais</h3>
            <button onclick="loadSerialPorts()" class="refresh-btn">🔄 Atualizar Lista de Portas</button>
            <br><br>
            
            <div class="port-section">
                <h4>Porta Serial 1 (Comandos K/P - Arduino)</h4>
                <label for="port1">Porta:</label>
                <select id="port1" class="port-select">
                    <option value="">Selecione a porta</option>
                </select>
                <button onclick="connectPort(1)">Conectar</button>
                <button onclick="disconnectPort(1)">Desconectar</button>
                <button onclick="sendHomeCommand(1)" class="home-btn" id="homeBtn1">Enviar $H (Home)</button>
                <div id="status1" class="status disconnected">Porta 1: Desconectada</div>
            </div>
            
            <div class="port-section">
                <h4>Porta Serial 2 (Comandos G-code - GRBL)</h4>
                <label for="port2">Porta:</label>
                <select id="port2" class="port-select">
                    <option value="">Selecione a porta</option>
                </select>
                <button onclick="connectPort(2)">Conectar</button>
                <button onclick="disconnectPort(2)">Desconectar</button>
                <button onclick="sendHomeCommand(2)" class="home-btn" id="homeBtn2">Enviar $H (Home)</button>
                <div id="status2" class="status disconnected">Porta 2: Desconectada</div>
            </div>

            <div class="port-section">
                <h4>Porta Serial 3 (Receber IR - Nano)</h4>
                <label for="port3">Porta:</label>
                <select id="port3" class="port-select">
                    <option value="">Selecione a porta</option>
                </select>
                <button onclick="connectPort(3)">Conectar</button>
                <button onclick="disconnectPort(3)">Desconectar</button>
                <button onclick="startIRListening()" class="home-btn" id="irBtn">Iniciar Escuta IR</button>
                <div id="status3" class="status disconnected">Porta 3: Desconectada</div>
            </div>
        </div>

        <div class="command-section">
            <h3>Comandos Individuais - Porta 1 (K/P)</h3>
            <button onclick="sendCommand(1, 'K2_1')" class="command-btn">K2_1 (Avançar)</button>
            <button onclick="sendCommand(1, 'P_1')" class="command-btn">P_1 (Pressionar)</button>
            <button onclick="sendCommand(1, 'P_0')" class="command-btn">P_0 (Liberar)</button>
            <button onclick="sendCommand(1, 'P_2')" class="command-btn">P_2 (Travar)</button>
            <button onclick="sendCommand(1, 'K7_1')" class="command-btn">K7_1 (Expandir)</button>
            <button onclick="sendCommand(1, 'B1_1')" class="command-btn">B1_1 (Iniciar IR)</button>
             <button onclick="sendCommand(1, 'K2_0')" class="command-btn">ENA (voltar)</button>
            <button onclick="sendCommand(1, 'ENA')" class="command-btn">ENA (Enable)</button>
        </div>

        <div class="command-section">
            <h3>Comandos Individuais - Porta 2 (G-code)</h3>
            <button onclick="sendCommand(2, 'G90 X29.787 Y82.987')" class="command-btn-port2">Mover para Posição Inicial</button>
            <button onclick="sendCommand(2, 'G90 X394.805 Y77.726')" class="command-btn-port2">Mover para Posição 2</button>
            <button onclick="sendCommand(2, 'G28')" class="command-btn-port2">Home (G28)</button>
            <button onclick="sendCommand(2, 'G1 X10 Y10 F1000')" class="command-btn-port2">Mover X10 Y10</button>
        </div>

        <div class="command-section">
            <h3>Comandos Individuais - Porta 3 (IR Nano)</h3>
            <button onclick="sendCommand(3, 'GET')" class="command-btn-port3">GET (Solicitar Dados IR)</button>
            <button onclick="sendCommand(3, 'RESET')" class="command-btn-port3">RESET (Reiniciar Nano)</button>
        </div>
        
        <div class="actions">
            <h3>Ações Automáticas</h3>
            <button onclick="startFingerDown()" id="startBtn">▶️ Iniciar FingerDown + Início1</button>
            <button onclick="stopProcess()" id="stopBtn" disabled>⏹️ Parar Processo</button>
            <button onclick="resetSystem()" id="resetBtn">🔄 Resetar Sistema</button>
            <button onclick="testIRSequence()" id="testIRBtn">🧪 Testar Sequência IR</button>
        </div>

        <div class="ir-data">
            <h3>📟 Dados IR Recebidos</h3>
            <div id="irData" style="height: 100px; overflow-y: auto; border: 1px solid #ccc; padding: 10px; background-color: #f8f9fa; font-family: monospace;"></div>
        </div>
        
        <div class="logs">
            <h3>📋 Logs do Sistema</h3>
            <div id="logs" style="height: 300px; overflow-y: auto; border: 1px solid #ccc; padding: 10px; background-color: #f8f9fa;"></div>
        </div>
    </div>

    <script>
        let processRunning = false;
        let irDataCount = 0;
        
        // Carregar portas seriais disponíveis
        async function loadSerialPorts() {
            try {
                addLog('Buscando portas seriais disponíveis...', 'info');
                const response = await fetch('/get_serial_ports');
                const data = await response.json();
                
                if (data.status === 'error') {
                    throw new Error(data.message);
                }
                
                const selects = ['port1', 'port2', 'port3'];
                const currentValues = selects.map(id => document.getElementById(id).value);
                
                selects.forEach((selectId, index) => {
                    const select = document.getElementById(selectId);
                    while (select.children.length > 1) select.removeChild(select.lastChild);
                    
                    data.ports.forEach(port => {
                        const option = document.createElement('option');
                        option.value = port.device;
                        option.textContent = `${port.device} - ${port.description}`;
                        select.appendChild(option);
                    });
                    
                    if (currentValues[index]) {
                        select.value = currentValues[index];
                    }
                });
                
                addLog(`Encontradas ${data.ports.length} portas seriais`, 'success');
                
            } catch (error) {
                addLog('Erro ao carregar portas seriais: ' + error, 'error');
            }
        }
        
        // Conectar porta serial
        async function connectPort(portNumber) {
            const select = document.getElementById(`port${portNumber}`);
            const port = select.value;
            
            if (!port) {
                alert('Por favor, selecione uma porta serial');
                return;
            }
            
            try {
                addLog(`Conectando porta ${portNumber}: ${port}`, 'info');
                const response = await fetch(`/connect_port/${portNumber}?port_name=${encodeURIComponent(port)}`);
                const result = await response.json();
                
                if (result.status === 'success') {
                    document.getElementById(`status${portNumber}`).className = 'status connected';
                    document.getElementById(`status${portNumber}`).textContent = `Porta ${portNumber}: Conectada (${port})`;
                    addLog(`✅ Porta ${portNumber} conectada: ${port}`, 'success');
                    document.getElementById(`homeBtn${portNumber}`).disabled = false;
                } else {
                    throw new Error(result.message);
                }
            } catch (error) {
                addLog(`❌ Erro ao conectar porta ${portNumber}: ${error}`, 'error');
            }
        }
        
        // Desconectar porta serial
        async function disconnectPort(portNumber) {
            try {
                addLog(`Desconectando porta ${portNumber}`, 'info');
                const response = await fetch(`/disconnect_port/${portNumber}`);
                const result = await response.json();
                
                if (result.status === 'success') {
                    document.getElementById(`status${portNumber}`).className = 'status disconnected';
                    document.getElementById(`status${portNumber}`).textContent = `Porta ${portNumber}: Desconectada`;
                    addLog(`Porta ${portNumber} desconectada`, 'info');
                    document.getElementById(`homeBtn${portNumber}`).disabled = true;
                }
            } catch (error) {
                addLog(`Erro ao desconectar porta ${portNumber}: ${error}`, 'error');
            }
        }
        
        // Enviar comando Home
        async function sendHomeCommand(portNumber) {
            try {
                const status = document.getElementById(`status${portNumber}`).className.includes('connected');
                if (!status) {
                    alert(`Conecte a Porta ${portNumber} primeiro`);
                    return;
                }
                
                addLog(`Enviando comando $H (Home) para Porta ${portNumber}...`, 'info');
                document.getElementById(`homeBtn${portNumber}`).disabled = true;
                
                const response = await fetch(`/send_home/${portNumber}`, { method: 'POST' });
                const result = await response.json();
                
                if (result.status === 'success') {
                    addLog(`✅ Comando $H (Home) enviado para Porta ${portNumber}`, 'success');
                } else {
                    throw new Error(result.message);
                }
                
            } catch (error) {
                addLog(`❌ Erro ao enviar comando Home: ${error}`, 'error');
            } finally {
                document.getElementById(`homeBtn${portNumber}`).disabled = false;
            }
        }
        
        // Enviar comando individual
        async function sendCommand(portNumber, command) {
            try {
                const status = document.getElementById(`status${portNumber}`).className.includes('connected');
                if (!status) {
                    alert(`Conecte a Porta ${portNumber} primeiro`);
                    return;
                }
                
                addLog(`Enviando para Porta ${portNumber}: ${command}`, 'info');
                
                const response = await fetch(`/send_command/${portNumber}?command=${encodeURIComponent(command)}`, {
                    method: 'POST'
                });
                const result = await response.json();
                
                if (result.status === 'success') {
                    addLog(`✅ Comando enviado: ${command}`, 'success');
                } else {
                    throw new Error(result.message);
                }
                
            } catch (error) {
                addLog(`❌ Erro ao enviar comando: ${error}`, 'error');
            }
        }
        
        // Iniciar processo completo
        async function startFingerDown() {
            if (processRunning) return;
            
            try {
                processRunning = true;
                document.getElementById('startBtn').disabled = true;
                document.getElementById('stopBtn').disabled = false;
                document.getElementById('processStatus').textContent = 'Sim';
                
                addLog('🚀 INICIANDO PROCESSO COMPLETO: FingerDown + Início1', 'info');
                
                const response = await fetch('/start_complete_process', { method: 'POST' });
                const result = await response.json();
                
                if (result.status === 'success') {
                    addLog('✅ Processo completo iniciado com sucesso!', 'success');
                } else {
                    throw new Error(result.message);
                }
            } catch (error) {
                addLog(`❌ Erro ao iniciar processo: ${error}`, 'error');
                processRunning = false;
                document.getElementById('startBtn').disabled = false;
                document.getElementById('stopBtn').disabled = true;
                document.getElementById('processStatus').textContent = 'Não';
            }
        }
        
        // Testar sequência IR
        async function testIRSequence() {
            try {
                addLog('🧪 Iniciando teste de sequência IR...', 'info');
                const response = await fetch('/test_ir_sequence', { method: 'POST' });
                const result = await response.json();
                
                if (result.status === 'success') {
                    addLog('✅ Teste IR iniciado', 'success');
                }
            } catch (error) {
                addLog(`❌ Erro no teste IR: ${error}`, 'error');
            }
        }
        
        // Parar processo
        async function stopProcess() {
            try {
                const response = await fetch('/stop_process', { method: 'POST' });
                const result = await response.json();
                
                processRunning = false;
                document.getElementById('startBtn').disabled = false;
                document.getElementById('stopBtn').disabled = true;
                document.getElementById('processStatus').textContent = 'Não';
                document.getElementById('commandStatus').textContent = 'Não';
                addLog('⏹️ Processo parado pelo usuário', 'warning');
            } catch (error) {
                addLog(`Erro ao parar processo: ${error}`, 'error');
            }
        }
        
        // Resetar sistema
        async function resetSystem() {
            try {
                const response = await fetch('/reset_system', { method: 'POST' });
                const result = await response.json();
                
                document.getElementById('currentLine').textContent = '0';
                document.getElementById('irCount').textContent = '0';
                document.getElementById('commandStatus').textContent = 'Não';
                document.getElementById('irData').innerHTML = '';
                addLog('🔄 Sistema resetado', 'info');
            } catch (error) {
                addLog(`Erro ao resetar sistema: ${error}`, 'error');
            }
        }
        
        // Iniciar escuta IR
        async function startIRListening() {
            try {
                addLog('👂 Iniciando escuta de dados IR...', 'info');
                // Aqui você implementaria a escuta contínua das portas
            } catch (error) {
                addLog(`Erro na escuta IR: ${error}`, 'error');
            }
        }
        
        // Adicionar log
        function addLog(message, type = 'info') {
            const logsDiv = document.getElementById('logs');
            const timestamp = new Date().toLocaleTimeString();
            const logEntry = document.createElement('div');
            logEntry.textContent = `[${timestamp}] ${message}`;
            logEntry.className = `log-${type}`;
            logsDiv.appendChild(logEntry);
            logsDiv.scrollTop = logsDiv.scrollHeight;
        }
        
        // Adicionar dado IR
        function addIRData(data) {
            const irDiv = document.getElementById('irData');
            const timestamp = new Date().toLocaleTimeString();
            const dataEntry = document.createElement('div');
            dataEntry.textContent = `[${timestamp}] ${data}`;
            dataEntry.className = 'log-ir';
            irDiv.appendChild(dataEntry);
            irDiv.scrollTop = irDiv.scrollHeight;
            
            irDataCount++;
            document.getElementById('irCount').textContent = irDataCount;
        }
        
        // Carregar portas ao iniciar
        window.onload = function() {
            loadSerialPorts();
            document.getElementById('homeBtn1').disabled = true;
            document.getElementById('homeBtn2').disabled = true;
        };

        // WebSocket para dados IR em tempo real (opcional)
        // const ws = new WebSocket('ws://localhost:8000/ws');
        // ws.onmessage = function(event) {
        //     const data = JSON.parse(event.data);
        //     if (data.type === 'ir_data') {
        //         addIRData(data.message);
        //     }
        // };
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def read_root():
    return HTMLResponse(content=html_content)




@app.get("/health")
async def health_check():
    """Endpoint específico para health check"""
    return {
        "status": "healthy",
        "service": "remote-control-tester",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/test")
async def test():
    return {"message": "✅ API está funcionando!", "status": "success"}



# ENDPOINT FINGERDOWN CORRIGIDO E OTIMIZADO
@app.post("/fingerdown1")
async def fingerdown():
    """Sequência FingerDown 1 - Movimentos coordenados para operação fingerdown"""
    global fingerdown_running, current_test_cycle
    
    print("🎯 ENDPOINT /fingerdown1 ACESSADO DIRETAMENTE!")
    
    if fingerdown_running:
        raise HTTPException(status_code=400, detail="FingerDown já em execução")
    
    try:
        fingerdown_running = True
        current_test_cycle += 1
        
        print("=== INICIANDO FINGERDOWN 1 ===")
        print(f"📦 Ciclo de teste: {current_test_cycle}")
        
        # Verificar portas conectadas
        port1_connected = serial_port1 and serial_port1.is_open
        port2_connected = serial_port2 and serial_port2.is_open
        
        print(f"🔌 Porta 1 conectada: {port1_connected}")
        print(f"🔌 Porta 2 conectada: {port2_connected}")
        
        if not port1_connected or not port2_connected:
            raise HTTPException(status_code=400, detail="Portas necessárias não conectadas")
        
        # VERIFICAÇÃO INICIAL DE ESTADO
        await verificar_estado_inicial()
        
        # SEQUÊNCIA FINGERDOWN OTIMIZADA
        # 1. Avançar (Porta 1)
        await enviar_comando_porta(1, "K2_1", "Avançar", timeout=3.0)
        
        # 2. Mover na posição (Porta 2) - COM VERIFICAÇÃO
        await enviar_comando_porta(2, "G90 X29.787 Y82.987", "Mover para posição inicial", timeout=4.0)
        
        # 3. Pressionar (Porta 1)
        await enviar_comando_porta(1, "P_1", "Pressionar", timeout=1.5)
        
        # 4. Travar (Porta 1)
        await enviar_comando_porta(1, "K4_1", "Travar", timeout=1.0)
        
        # 5. Expandir a pilha (Porta 1) - COM CONTROLE
        await enviar_comando_porta(1, "K7_1", "Expandir pilha - 1º", timeout=0.8)
        await asyncio.sleep(0.2)  # Pequena pausa entre expansões
        await enviar_comando_porta(1, "K7_1", "Expandir pilha - 2º", timeout=0.8)
        
        # 6. Tirar o pressionamento (Porta 1)
        await enviar_comando_porta(1, "P_0", "Liberar pressão", timeout=1.0)
        
        print("✅ FINGERDOWN 1 CONCLUÍDO")

        # Inicia sequência principal
        await inicio1()

        return {
            "status": "success", 
            "message": "FingerDown executado com sucesso",
            "cycle": current_test_cycle,
            "timestamp": datetime.now().isoformat(),
            "port1_connected": port1_connected,
            "port2_connected": port2_connected
        }
        
    except Exception as e:
        error_msg = f"❌ Erro crítico no FingerDown: {str(e)}"
        print(error_msg)
        await emergency_stop()
        raise HTTPException(status_code=500, detail=error_msg)
    finally:
        fingerdown_running = False

async def verificar_estado_inicial():
    """Verifica e reseta o estado inicial das máquinas"""
    try:
        print("🔍 Verificando estado inicial...")
        
        # Reset inicial na Porta 2 (GRBL)
        if serial_port2 and serial_port2.is_open:
            serial_port2.write(b"\x18\n")  # Ctrl-X - Soft reset
            await asyncio.sleep(1.0)
            serial_port2.write(b"$X\n")    # Unlock
            await asyncio.sleep(0.5)
            serial_port2.write(b"G90\n")   # Absolute positioning
            await asyncio.sleep(0.2)
            serial_port2.write(b"G21\n")   # Millimeter units
            await asyncio.sleep(0.2)
            print("✅ Reset GRBL realizado")
        
        # Estado inicial Porta 1
        if serial_port1 and serial_port1.is_open:
            serial_port1.write(b"P_0\n")   # Garantir pressionamento liberado
            await asyncio.sleep(0.3)
            serial_port1.write(b"B1_0\n")  # Garantir IR desligado
            await asyncio.sleep(0.3)
            print("✅ Estado inicial Porta 1 configurado")
            
    except Exception as e:
        print(f"⚠️ Aviso na verificação inicial: {e}")

async def enviar_comando_porta(port_number: int, command: str, descricao: str, timeout: float = 2.0):
    """Envia comando para porta com tratamento de erro e timeout"""
    try:
        print(f"📤 [{port_number}] {descricao}: {command}")
        
        port = None
        if port_number == 1:
            port = serial_port1
        elif port_number == 2:
            port = serial_port2
        elif port_number == 3:
            port = serial_port3
            
        if not port or not port.is_open:
            raise Exception(f"Porta {port_number} não disponível")
        
        # Envia comando
        port.write(f"{command}\n".encode())
        
        # Aguarda tempo baseado no comando
        if timeout > 0:
            await asyncio.sleep(timeout)
            
        # Verifica resposta para comandos GRBL
        if port_number == 2 and command.startswith(('G', 'X', 'Y')):
            await verificar_status_grbl()
            
        print(f"✅ [{port_number}] {descricao} concluído")
        
    except Exception as e:
        error_msg = f"❌ Erro no comando {descricao}: {str(e)}"
        print(error_msg)
        raise

async def verificar_status_grbl():
    """Verifica status do GRBL para garantir que está pronto"""
    try:
        if serial_port2 and serial_port2.is_open:
            # Limpa buffer
            while serial_port2.in_waiting > 0:
                serial_port2.read(serial_port2.in_waiting)
            
            # Solicita status
            serial_port2.write(b"?\n")
            await asyncio.sleep(0.1)
            
            # Lê resposta
            if serial_port2.in_waiting > 0:
                status = serial_port2.read(serial_port2.in_waiting).decode().strip()
                if 'Idle' not in status and 'Run' not in status:
                    print(f"⚠️ Status GRBL não ideal: {status}")
                    # Tenta recuperar
                    serial_port2.write(b"$X\n")
                    await asyncio.sleep(0.5)
                    
    except Exception as e:
        print(f"⚠️ Erro na verificação GRBL: {e}")

async def emergency_stop():
    """Para todas as operações em caso de emergência"""
    try:
        print("🛑 EMERGENCY STOP ATIVADO")
        
        if serial_port1 and serial_port1.is_open:
            serial_port1.write(b"P_0\n")
            serial_port1.write(b"B1_0\n")
            
        if serial_port2 and serial_port2.is_open:
            serial_port2.write(b"\x85\n")  # Stop Jog
            serial_port2.write(b"P_0\n")
            
        await asyncio.sleep(1.0)
        print("✅ Emergency stop concluído")
        
    except Exception as e:
        print(f"❌ Erro no emergency stop: {e}")

async def inicio1():
    """Início do teste real - sequência de comandos otimizada"""
    global linha_atual, libera_envio_comandos
    
    try:
        print("=== INICIANDO INÍCIO1 (TESTE REAL) ===")
        
        # Reset de estado
        libera_envio_comandos = True
        linha_atual = 0
        
        # Envia comando para iniciar IR
        await enviar_comando_porta(1, "B1_1", "Iniciar IR", timeout=0.5)
        await enviar_comando_porta(1, "B1_1", "Iniciar IR - 2º", timeout=2.5)
        
        # Inicia sequência de comandos
        asyncio.create_task(executar_sequencia_comandos())
        
        return {"status": "success", "message": "Início1 executado"}
        
    except Exception as e:
        print(f"❌ Erro no Início1: {e}")
        await emergency_stop()
        return {"status": "error", "message": str(e)}






# =========================
# ENDPOINTS PARA O FRONTEND
# =========================

@app.post("/send_command/{port_number}")
async def send_command_endpoint(port_number: int, request: Request):
    """Endpoint para receber comandos do frontend"""
    try:
        # Parse do JSON do body
        body = await request.json()
        command = body.get('command', '')
        
        print(f"📤 Comando recebido do frontend - Porta {port_number}: {command}")
        
        # Processa comandos especiais
        if command == 'START_CALIBRATION':
            # Calibração sempre envia $H para porta 2 (GRBL)
            return await send_home_command(2)
        elif command == 'START':
            return await start_test_sequence(port_number)
        elif command == 'FINGER_DOWN':
            return await fingerdown()  # Usa o endpoint existente
        else:
            # Envia comando direto para a porta serial
            return await send_raw_command(port_number, command)
            
    except Exception as e:
        print(f"❌ Erro no endpoint send_command: {e}")
        return {"status": "error", "message": str(e)}

async def send_raw_command(port_number: int, command: str):
    """Envia comando direto para porta serial"""
    global serial_port1, serial_port2, serial_port3, serial_port4
    
    try:
        port = None
        if port_number == 1:
            port = serial_port1
        elif port_number == 2:
            port = serial_port2
        elif port_number == 3:
            port = serial_port3
        elif port_number == 4:
            port = serial_port4
        else:
            return {"status": "error", "message": f"Porta {port_number} inválida"}
        
        if not port or not port.is_open:
            return {"status": "error", "message": f"Porta {port_number} não conectada"}
        
        # Envia comando
        command_bytes = f"{command}\n".encode()
        port.write(command_bytes)
        
        print(f"✅ Comando enviado para porta {port_number}: {command}")
        
        # Pequena pausa para processamento
        await asyncio.sleep(0.1)
        
        return {
            "status": "success", 
            "message": f"Comando '{command}' enviado para porta {port_number}",
            "command": command,
            "port": port_number
        }
        
    except Exception as e:
        error_msg = f"Erro ao enviar comando: {str(e)}"
        print(f"❌ {error_msg}")
        return {"status": "error", "message": error_msg}

async def start_calibration_sequence(port_number: int):
    """Inicia sequência de calibração"""
    try:
        print("🔧 Iniciando calibração...")
        
        # Comandos de calibração
        commands = ["G28", "G90", "G21", "$H"]
        
        for cmd in commands:
            await send_raw_command(port_number, cmd)
            await asyncio.sleep(1.0)
        
        return {
            "status": "success", 
            "message": "Calibração concluída",
            "sequence": "calibration"
        }
        
    except Exception as e:
        return {"status": "error", "message": f"Erro na calibração: {str(e)}"}

async def start_test_sequence(port_number: int):
    """Inicia sequência de teste"""
    try:
        print("🧪 Iniciando teste...")
        
        # Comandos de teste básicos
        commands = ["G90", "G1 X10 Y10 F1000", "G1 X20 Y20 F1000"]
        
        for cmd in commands:
            await send_raw_command(port_number, cmd)
            await asyncio.sleep(0.5)
        
        return {
            "status": "success", 
            "message": "Teste concluído",
            "sequence": "test"
        }
        
    except Exception as e:
        return {"status": "error", "message": f"Erro no teste: {str(e)}"}






async def executar_sequencia_comandos():
    """Executa a sequência completa de comandos COM PRESSIONAMENTO e salva UM único JSON consolidado"""
    global linha_atual, libera_envio_comandos
    
    # Lista para armazenar TODOS os dados IR capturados
    todos_dados_ir = []
    
    try:
        print(f"🎯 INICIANDO SEQUÊNCIA DE {len(test_coordinates)} COMANDOS")
        print("📝 Modo: UM único JSON consolidado com todos os botões")
        print("🔘 AGORA COM PRESSIONAMENTO DE BOTÕES!")
        
        for i, coord in enumerate(test_coordinates):
            if not libera_envio_comandos:
                print("⏸️ Sequência interrompida")
                break
                
            linha_atual = i
            nome_botao = coord.get('nome', f'Botão {i+1}')
            print(f"🔹 Comando {i+1}/{len(test_coordinates)} - {nome_botao}")
            
            # 1. Move para posição
            command = f"{coord['command']} X{coord['x']} Y{coord['y']}"
            await enviar_comando_porta(2, command, f"Movimento {i+1}", timeout=1.5)
            
            # 2. ✅ CORREÇÃO: PRESSIONA O BOTÃO antes de capturar IR
            print(f"🔘 [{i+1}] Pressionando botão {nome_botao}...")
            
            # Pressiona o botão
            await enviar_comando_porta(1, "P_1", f"Pressionar {nome_botao}", timeout=0.3)
            await asyncio.sleep(0.2)  # Pequena pausa para estabilização
            
            # Libera o botão
            await enviar_comando_porta(1, "P_0", f"Liberar {nome_botao}", timeout=0.3)
            
            # 3. Captura dados IR APÓS pressionar o botão
            print(f"📡 [{i+1}] Capturando dados IR após pressionar {nome_botao}...")
            resultado_ir = await capturar_dados_ir(
                nano='nano1',
                timeout=8000,
                salvar_captura=False  # NÃO salva individualmente
            )
            
            # Adiciona à lista consolidada
            if resultado_ir.get('success'):
                dados_botao = {
                    "botao_numero": i + 1,
                    "coordenadas": coord,
                    "timestamp": resultado_ir.get('timestamp'),
                    "request_id": resultado_ir.get('request_id'),
                    "dados_ir": resultado_ir.get('data'),
                    "nome_botao": nome_botao,
                    "comando_executado": f"Pressionar {nome_botao} em X{coord['x']} Y{coord['y']}"
                }
                todos_dados_ir.append(dados_botao)
                print(f"✅ [{i+1}] Botão pressionado e dados IR capturados")
            else:
                print(f"❌ [{i+1}] Falha na captura IR: {resultado_ir.get('error')}")
            
            # 4. Pequena pausa entre comandos
            if i < len(test_coordinates) - 1:
                await asyncio.sleep(1.0)
        
        print("✅ SEQUÊNCIA DE COMANDOS CONCLUÍDA")
        print(f"📊 Total de botões pressionados: {len(todos_dados_ir)}")
        
        # 5. SALVA UM ÚNICO JSON COM TODOS OS DADOS
        if todos_dados_ir:
            await salvar_json_consolidado(todos_dados_ir)
        else:
            print("⚠️ Nenhum dado IR foi capturado")
        
        # 6. FINALIZA O PROCESSO
        await finalizar_processo()
    
    except Exception as e:
        print(f"❌ Erro na sequência de comandos: {e}")
        await emergency_stop()

# =========================
# SISTEMA DE COMPARAÇÃO DE IMAGENS
# =========================

def processar_imagem(img_path: str) -> np.ndarray:
    """Processa imagem: carrega, redimensiona, converte para escala de cinza e normaliza"""
    try:
        img = cv2.imread(str(img_path))
        if img is None:
            raise ValueError(f"Não foi possível carregar imagem: {img_path}")
        
        # Redimensiona para tamanho padrão (640x480)
        img = cv2.resize(img, (640, 480))
        
        # Converte para escala de cinza
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Aplica blur para reduzir ruído
        gray = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Normaliza
        gray = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX)
        
        return gray
    except Exception as e:
        print(f"❌ Erro ao processar imagem {img_path}: {e}")
        return None

def calcular_similaridade_template_matching(img1: np.ndarray, img2: np.ndarray) -> float:
    """Calcula similaridade usando template matching"""
    try:
        if img1 is None or img2 is None:
            return 0.0
        
        # Garante que as imagens têm o mesmo tamanho
        if img1.shape != img2.shape:
            img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))
        
        # Template matching
        result = cv2.matchTemplate(img1, img2, cv2.TM_CCOEFF_NORMED)
        similarity = float(result[0][0])
        return max(0.0, similarity)  # Garante que não seja negativo
    except Exception as e:
        print(f"❌ Erro ao calcular template matching: {e}")
        return 0.0

def calcular_similaridade_histograma(img1: np.ndarray, img2: np.ndarray) -> float:
    """Calcula similaridade usando histograma"""
    try:
        if img1 is None or img2 is None:
            return 0.0
        
        # Garante que as imagens têm o mesmo tamanho
        if img1.shape != img2.shape:
            img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))
        
        # Calcula histogramas
        hist1 = cv2.calcHist([img1], [0], None, [256], [0, 256])
        hist2 = cv2.calcHist([img2], [0], None, [256], [0, 256])
        
        # Normaliza histogramas
        hist1 = cv2.normalize(hist1, hist1).flatten()
        hist2 = cv2.normalize(hist2, hist2).flatten()
        
        # Calcula correlação
        correlation = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
        return float(correlation)
    except Exception as e:
        print(f"❌ Erro ao calcular similaridade de histograma: {e}")
        return 0.0

def encontrar_imagem_referencia(botao_numero: int, nome_botao: str, camera_id: int, referencia_dir: Path) -> Optional[Path]:
    """Encontra imagem de referência correspondente"""
    try:
        nome_botao_clean = nome_botao.replace(' ', '_').replace('-', '_').upper()
        
        # Padrões de busca
        patterns = [
            f"botao_{botao_numero:03d}_{nome_botao_clean}_camera_{camera_id}_*.jpg",
            f"botao_{botao_numero:03d}_*_{nome_botao_clean}_*_camera_{camera_id}_*.jpg",
            f"*{nome_botao_clean}*camera_{camera_id}*.jpg",
            f"*botao_{botao_numero:03d}*camera_{camera_id}*.jpg"
        ]
        
        for pattern in patterns:
            matches = list(referencia_dir.glob(pattern))
            if matches:
                # Retorna a mais recente se houver múltiplas
                return max(matches, key=lambda p: p.stat().st_mtime)
        
        return None
    except Exception as e:
        print(f"❌ Erro ao buscar imagem de referência: {e}")
        return None

def comparar_imagem_com_referencia(imagem_teste_path: str, imagem_ref_path: str, threshold: float = 0.75) -> Dict[str, Any]:
    """Compara imagem de teste com imagem de referência"""
    try:
        # Processa ambas as imagens
        img_teste = processar_imagem(imagem_teste_path)
        img_ref = processar_imagem(imagem_ref_path)
        
        if img_teste is None or img_ref is None:
            return {
                "aprovado": False,
                "similaridade_template": 0.0,
                "similaridade_hist": 0.0,
                "similaridade_media": 0.0,
                "erro": "Erro ao processar imagens"
            }
        
        # Calcula similaridades
        template_score = calcular_similaridade_template_matching(img_teste, img_ref)
        hist_score = calcular_similaridade_histograma(img_teste, img_ref)
        
        # Média ponderada (template matching tem mais peso)
        similaridade_media = (template_score * 0.7) + (hist_score * 0.3)
        
        # Determina aprovação
        aprovado = similaridade_media >= threshold
        
        return {
            "aprovado": aprovado,
            "similaridade_template": round(template_score, 4),
            "similaridade_hist": round(hist_score, 4),
            "similaridade_media": round(similaridade_media, 4),
            "threshold": threshold
        }
    except Exception as e:
        print(f"❌ Erro ao comparar imagens: {e}")
        return {
            "aprovado": False,
            "similaridade_template": 0.0,
            "similaridade_hist": 0.0,
            "similaridade_media": 0.0,
            "erro": str(e)
        }

# Mapeamento de botões para controles (baseado no RemoteControlContainer)
MAPEAMENTO_CONTROLES = {
    1: {  # Controle 1
        "botoes": ["POWER", "FUNCAO", "TEMP_MAX", "TEMPORIZADOR", "TEMP_DOWN", "VELOCIDADE", 
                   "OSCILAR", "TURBO", "CONFORTO", "IONAIR", "VISOR", "DORMIR", "POWER_FINAL", "LIMPAR", "ANTIMORFO"]
    },
    2: {  # Controle 2
        "botoes": ["POWER", "FUNCAO", "TEMP_MAX", "TEMPORIZADOR", "TEMP_DOWN", "VELOCIDADE", 
                   "OSCILAR", "TURBO", "CONFORTO", "IONAIR", "VISOR", "DORMIR", "POWER_FINAL", "LIMPAR", "ANTIMORFO"]
    },
    3: {  # Controle 3
        "botoes": ["POWER", "FUNCAO", "TEMP_MAX", "TEMPORIZADOR", "TEMP_DOWN", "VELOCIDADE", 
                   "OSCILAR", "TURBO", "CONFORTO", "IONAIR", "VISOR", "DORMIR", "POWER_FINAL", "LIMPAR", "ANTIMORFO"]
    },
    4: {  # Controle 4
        "botoes": ["POWER", "FUNCAO", "TEMP_MAX", "TEMPORIZADOR", "TEMP_DOWN", "VELOCIDADE", 
                   "OSCILAR", "TURBO", "CONFORTO", "IONAIR", "VISOR", "DORMIR", "POWER_FINAL", "LIMPAR", "ANTIMORFO"]
    }
}

def obter_controle_do_botao(nome_botao: str) -> int:
    """Retorna o número do controle baseado no nome do botão"""
    # Por padrão, todos os botões são testados em todos os 4 controles
    # Mas podemos mapear baseado na posição na sequência
    # Por enquanto, retorna baseado no índice do botão na sequência
    for i, coord in enumerate(test_coordinates):
        if coord.get('nome') == nome_botao:
            # Distribui os botões entre os 4 controles
            return (i % 4) + 1
    return 1  # Default

def gerar_relatorio_controles(resultados_validacao: list) -> Dict[str, Any]:
    """Gera relatório final de aprovação/reprovação por controle"""
    # Agrupa resultados por controle
    controles_resultados = {1: [], 2: [], 3: [], 4: []}
    
    for resultado in resultados_validacao:
        controle_num = resultado.get('controle_numero', 1)
        if controle_num in controles_resultados:
            controles_resultados[controle_num].append(resultado)
    
    relatorio = {
        "controles": {},
        "resumo": {
            "total_controles": 4,
            "controles_aprovados": 0,
            "controles_reprovados": 0
        }
    }
    
    for controle_num in range(1, 5):
        resultados_controle = controles_resultados[controle_num]
        
        if not resultados_controle:
            relatorio["controles"][controle_num] = {
                "status": "sem_dados",
                "aprovado": False,
                "total_botoes": 0,
                "botoes_aprovados": 0,
                "botoes_reprovados": 0,
                "taxa_aprovacao": 0.0,
                "similaridade_media": 0.0,
                "botoes": []
            }
            continue
        
        # Calcula estatísticas
        total_botoes = len(resultados_controle)
        botoes_aprovados = sum(1 for r in resultados_controle if r.get('validacao', {}).get('aprovado', False))
        botoes_reprovados = total_botoes - botoes_aprovados
        
        # Calcula similaridade média
        similaridades = [r.get('validacao', {}).get('similaridade_media', 0.0) for r in resultados_controle]
        similaridade_media = sum(similaridades) / len(similaridades) if similaridades else 0.0
        
        # Controle é aprovado se pelo menos 80% dos botões foram aprovados
        taxa_aprovacao = botoes_aprovados / total_botoes if total_botoes > 0 else 0.0
        controle_aprovado = taxa_aprovacao >= 0.8 and similaridade_media >= 0.70
        
        relatorio["controles"][controle_num] = {
            "status": "aprovado" if controle_aprovado else "reprovado",
            "aprovado": controle_aprovado,
            "total_botoes": total_botoes,
            "botoes_aprovados": botoes_aprovados,
            "botoes_reprovados": botoes_reprovados,
            "taxa_aprovacao": round(taxa_aprovacao * 100, 2),
            "similaridade_media": round(similaridade_media, 4),
            "botoes": [
                {
                    "nome": r.get('nome_botao'),
                    "aprovado": r.get('validacao', {}).get('aprovado', False),
                    "similaridade": r.get('validacao', {}).get('similaridade_media', 0.0)
                }
                for r in resultados_controle
            ]
        }
        
        if controle_aprovado:
            relatorio["resumo"]["controles_aprovados"] += 1
        else:
            relatorio["resumo"]["controles_reprovados"] += 1
    
    return relatorio

def limpar_imagens_teste():
    """Limpa as imagens capturadas durante os testes anteriores (NÃO as imagens de referência)"""
    try:
        resultados_dir = Path("test_results")
        if not resultados_dir.exists():
            return
        
        deleted_count = 0
        
        # Lista todos os diretórios de ciclos anteriores
        for ciclo_dir in resultados_dir.glob("ciclo_*"):
            if ciclo_dir.is_dir():
                # Limpa todas as fotos dentro do diretório fotos/ do ciclo
                fotos_dir = ciclo_dir / "fotos"
                if fotos_dir.exists():
                    for img_file in fotos_dir.glob("*.jpg"):
                        try:
                            img_file.unlink()
                            deleted_count += 1
                        except Exception as e:
                            print(f"⚠️ Erro ao deletar {img_file.name}: {e}")
                
                # Opcional: Remove o diretório do ciclo se estiver vazio
                # (mas mantém o JSON do resultado)
                try:
                    if fotos_dir.exists() and not any(fotos_dir.iterdir()):
                        fotos_dir.rmdir()
                except:
                    pass
        
        if deleted_count > 0:
            print(f"🗑️ {deleted_count} imagem(ns) de teste deletada(s) dos ciclos anteriores")
        else:
            print("🗑️ Nenhuma imagem de teste anterior encontrada para deletar")
            
        # IMPORTANTE: NUNCA deleta nada da pasta camera_photos_modelo1
        # Essa pasta contém as imagens de REFERÊNCIA que devem ser preservadas!
        
    except Exception as e:
        print(f"⚠️ Erro ao limpar imagens de teste: {e}")

async def executar_sequencia_comandos_com_fotos():
    """Executa a sequência completa COM CAPTURA DE FOTOS de todas as câmeras a cada botão pressionado"""
    global linha_atual, libera_envio_comandos, current_test_cycle, last_pneumatic_message, last_test_report
    
    # Lista para armazenar TODOS os dados IR capturados
    todos_dados_ir = []
    
    # Diretório para salvar fotos de teste (temporário, será movido depois)
    photos_dir = Path("camera_photos_modelo1")
    photos_dir.mkdir(exist_ok=True)
    
    # Diretório para resultados dos testes
    resultados_dir = Path("test_results")
    resultados_dir.mkdir(exist_ok=True)
    
    # Cria subdiretório para este ciclo de teste
    ciclo_dir = resultados_dir / f"ciclo_{current_test_cycle}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    ciclo_dir.mkdir(exist_ok=True)
    ciclo_fotos_dir = ciclo_dir / "fotos"
    ciclo_fotos_dir.mkdir(exist_ok=True)
    
    print(f"📁 Diretório de resultados criado: {ciclo_dir}")
    
    try:
        print(f"🎯 INICIANDO SEQUÊNCIA COM FOTOS - {len(test_coordinates)} COMANDOS")
        print("📸 Modo: Captura fotos de todas as câmeras a cada botão pressionado")
        print("🔘 PRESSIONAMENTO DE BOTÕES + FOTOS!")
        
        for i, coord in enumerate(test_coordinates):
            if not libera_envio_comandos:
                print("⏸️ Sequência interrompida")
                break
                
            linha_atual = i
            nome_botao = coord.get('nome', f'Botão {i+1}')
            print(f"🔹 Comando {i+1}/{len(test_coordinates)} - {nome_botao}")
            
            # 1. Move para posição
            command = f"{coord['command']} X{coord['x']} Y{coord['y']}"
            await enviar_comando_porta(2, command, f"Movimento {i+1}", timeout=1.5)
            
            # 2. PRESSIONA O BOTÃO
            print(f"🔘 [{i+1}] Pressionando botão {nome_botao}...")
            await enviar_comando_porta(1, "P_1", f"Pressionar {nome_botao}", timeout=0.3)
            await asyncio.sleep(0.2)  # Pequena pausa para estabilização
            
            # 3. 📸 CAPTURA FOTOS DE TODAS AS CÂMERAS E COMPARA COM REFERÊNCIA
            print(f"📸 [{i+1}] Capturando fotos de todas as câmeras...")
            fotos_capturadas = []
            validacoes_fotos = []
            # Normaliza nome do botão para o nome do arquivo
            nome_botao_arquivo = nome_botao.replace(' ', '_').replace('-', '_').upper()
            
            # Diretório de referência
            referencia_dir = Path("camera_photos_modelo1")
            
            for camera_id in range(MAX_CAMERAS):
                try:
                    manager = camera_managers.get(camera_id)
                    if manager and manager.is_connected():
                        frame = manager.get_frame()
                        if frame is not None:
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                            filename = f"botao_{i+1:03d}_{nome_botao_arquivo}_camera_{camera_id}_{timestamp}.jpg"
                            # Salva na pasta de fotos do ciclo
                            filepath = ciclo_fotos_dir / filename
                            cv2.imwrite(str(filepath), frame)
                            
                            # 🔍 COMPARA COM IMAGEM DE REFERÊNCIA
                            img_ref_path = encontrar_imagem_referencia(i + 1, nome_botao, camera_id, referencia_dir)
                            
                            validacao = {
                                "camera_id": camera_id,
                                "aprovado": False,
                                "similaridade_media": 0.0,
                                "imagem_referencia_encontrada": False
                            }
                            
                            if img_ref_path and img_ref_path.exists():
                                resultado_comparacao = comparar_imagem_com_referencia(str(filepath), str(img_ref_path))
                                validacao.update(resultado_comparacao)
                                validacao["imagem_referencia_encontrada"] = True
                                validacao["imagem_referencia"] = str(img_ref_path)
                                
                                status = "✅ APROVADO" if resultado_comparacao["aprovado"] else "❌ REPROVADO"
                                print(f"  {status} Câmera {camera_id}: Similaridade {resultado_comparacao['similaridade_media']:.2%}")
                            else:
                                print(f"  ⚠️ Câmera {camera_id}: Imagem de referência não encontrada")
                                validacao["erro"] = "Imagem de referência não encontrada"
                            
                            fotos_capturadas.append({
                                "camera_id": camera_id,
                                "filename": filename,
                                "filepath": str(filepath)
                            })
                            validacoes_fotos.append(validacao)
                            print(f"  ✅ Foto câmera {camera_id} salva: {filename}")
                        else:
                            print(f"  ⚠️ Câmera {camera_id} sem frame disponível")
                    else:
                        print(f"  ⚠️ Câmera {camera_id} não conectada")
                except Exception as e:
                    print(f"  ❌ Erro ao capturar foto da câmera {camera_id}: {e}")
            
            # 4. Libera o botão
            await enviar_comando_porta(1, "P_0", f"Liberar {nome_botao}", timeout=0.3)
            
            # 5. Captura dados IR APÓS pressionar o botão (opcional - não bloqueia o teste)
            print(f"📡 [{i+1}] Capturando dados IR após pressionar {nome_botao}...")
            resultado_ir = await capturar_dados_ir(
                nano='nano1',
                timeout=8000,
                salvar_captura=False
            )
            
            # Calcula validação geral do botão (aprovado se todas as câmeras aprovarem)
            todas_aprovadas = all(v.get('aprovado', False) for v in validacoes_fotos if v.get('imagem_referencia_encontrada'))
            similaridade_media_botao = sum(v.get('similaridade_media', 0.0) for v in validacoes_fotos) / len(validacoes_fotos) if validacoes_fotos else 0.0
            
            # SEMPRE adiciona os dados, mesmo se a captura IR falhar
            # (o teste de imagem é o principal, o IR é complementar)
            dados_botao = {
                "botao_numero": i + 1,
                "coordenadas": coord,
                "timestamp": resultado_ir.get('timestamp') if resultado_ir.get('success') else datetime.now().isoformat(),
                "request_id": resultado_ir.get('request_id') if resultado_ir.get('success') else None,
                "dados_ir": resultado_ir.get('data') if resultado_ir.get('success') else None,
                "ir_capturado": resultado_ir.get('success', False),
                "ir_erro": resultado_ir.get('error') if not resultado_ir.get('success') else None,
                "nome_botao": nome_botao,
                "comando_executado": f"Pressionar {nome_botao} em X{coord['x']} Y{coord['y']}",
                "fotos_capturadas": fotos_capturadas,
                "validacao": {
                    "aprovado": todas_aprovadas,
                    "similaridade_media": round(similaridade_media_botao, 4),
                    "validacoes_por_camera": validacoes_fotos
                },
                "controle_numero": obter_controle_do_botao(nome_botao)
            }
            todos_dados_ir.append(dados_botao)
            
            if resultado_ir.get('success'):
                print(f"✅ [{i+1}] Botão pressionado, {len(fotos_capturadas)} fotos e dados IR capturados")
            else:
                print(f"⚠️ [{i+1}] Botão pressionado, {len(fotos_capturadas)} fotos capturadas (IR não capturado: {resultado_ir.get('error', 'Erro desconhecido')})")
            
            print(f"   📊 Validação: {'✅ APROVADO' if todas_aprovadas else '❌ REPROVADO'} (Similaridade média: {similaridade_media_botao:.2%})")
            
            # 6. Pequena pausa entre comandos
            if i < len(test_coordinates) - 1:
                await asyncio.sleep(1.0)
        
        print("✅ SEQUÊNCIA COM FOTOS CONCLUÍDA")
        print(f"📊 Total de botões pressionados: {len(todos_dados_ir)}")
        
        # 7. GERA RELATÓRIO DE VALIDAÇÃO POR CONTROLE
        resultados_validacao = [
            {
                "controle_numero": d.get('controle_numero', 1),
                "nome_botao": d.get('nome_botao'),
                "botao_numero": d.get('botao_numero'),
                "validacao": d.get('validacao', {})
            }
            for d in todos_dados_ir if d.get('validacao')
        ]
        
        relatorio_controles = gerar_relatorio_controles(resultados_validacao)
        
        # 8. IMPRIME RELATÓRIO FINAL
        print("\n" + "="*60)
        print("📋 RELATÓRIO FINAL DE VALIDAÇÃO POR CONTROLE")
        print("="*60)
        for controle_num in range(1, 5):
            info = relatorio_controles["controles"][controle_num]
            status_emoji = "✅" if info["aprovado"] else "❌"
            print(f"\n{status_emoji} CONTROLE {controle_num}: {info['status'].upper()}")
            print(f"   Total de botões: {info['total_botoes']}")
            print(f"   Botões aprovados: {info['botoes_aprovados']}")
            print(f"   Botões reprovados: {info['botoes_reprovados']}")
            print(f"   Taxa de aprovação: {info['taxa_aprovacao']}%")
            print(f"   Similaridade média: {info['similaridade_media']:.2%}")
        
        print(f"\n📊 RESUMO GERAL:")
        print(f"   Controles aprovados: {relatorio_controles['resumo']['controles_aprovados']}/4")
        print(f"   Controles reprovados: {relatorio_controles['resumo']['controles_reprovados']}/4")
        print("="*60 + "\n")
        
        # 9. SALVA RESULTADOS NO DIRETÓRIO DO CICLO
        if todos_dados_ir:
            # Salva JSON consolidado no diretório do ciclo
            json_path = ciclo_dir / f"resultado_teste_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            dados_consolidados = {
                "metadata": {
                    "arquivo_salvo_em": datetime.now().isoformat(),
                    "ciclo_teste": current_test_cycle,
                    "total_botoes_mapeados": len(todos_dados_ir),
                    "sequencia_executada": "FingerDown + Início1",
                    "timestamp_inicio": todos_dados_ir[0]['timestamp'] if todos_dados_ir else None,
                    "timestamp_fim": datetime.now().isoformat(),
                    "diretorio_fotos": str(ciclo_fotos_dir)
                },
                "botoes_mapeados": todos_dados_ir,
                "relatorio_controles": relatorio_controles
            }
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(dados_consolidados, f, indent=2, ensure_ascii=False)
            
            # Armazena o relatório globalmente para acesso via API
            last_test_report = relatorio_controles
            
            print(f"💾 RESULTADO SALVO: {json_path}")
            print(f"📁 Fotos salvas em: {ciclo_fotos_dir}")
            print(f"📊 Total de botões mapeados: {len(todos_dados_ir)}")
        else:
            print("⚠️ Nenhum dado IR foi capturado")
        
        # 10. FINALIZA O PROCESSO
        await finalizar_processo()
        
        # Atualiza mensagem para a dashboard
        last_pneumatic_message = "✅ Teste concluído com sucesso!"
    
    except Exception as e:
        print(f"❌ Erro na sequência de comandos com fotos: {e}")
        await emergency_stop()
        
        # Atualiza mensagem de erro
        last_pneumatic_message = f"❌ Erro no teste: {str(e)}"

async def inicio1_com_fotos():
    """Início do teste real COM FOTOS - sequência de comandos otimizada"""
    global linha_atual, libera_envio_comandos
    
    try:
        print("=== INICIANDO INÍCIO1 COM FOTOS (TESTE REAL) ===")
        
        # Reset de estado
        libera_envio_comandos = True
        linha_atual = 0
        
        # Envia comando para iniciar IR
        await enviar_comando_porta(1, "B1_1", "Iniciar IR", timeout=0.5)
        await enviar_comando_porta(1, "B1_1", "Iniciar IR - 2º", timeout=2.5)
        
        # Inicia sequência de comandos COM FOTOS
        asyncio.create_task(executar_sequencia_comandos_com_fotos())
        
        return {"status": "success", "message": "Início1 com fotos executado"}
        
    except Exception as e:
        print(f"❌ Erro no Início1 com fotos: {e}")
        await emergency_stop()
        return {"status": "error", "message": str(e)}

async def capturar_dados_ir(nano: str = 'nano1', timeout: int = 10000, 
                           salvar_captura: bool = False) -> Dict[str, Any]:  # Mude para False por padrão
    """
    CAPTURA dados IR do Nano (APENAS LEITURA)
    Agora retorna os dados para serem consolidados em um único JSON
    """
    try:
        print(f"🎯 Capturando IR do {nano}...")
        
        async with IRReader() as reader:
            # Captura os dados IR
            result = await reader.capture_ir_data(nano=nano, timeout=timeout)
            
            if result.get('success'):
                print(f"✅ Dados IR capturados com sucesso!")
                return {
                    "success": True,
                    "nano": nano,
                    "data": result.get('data'),
                    "timestamp": result.get('timestamp'),
                    "request_id": result.get('requestId')
                }
            else:
                print(f"❌ Falha na captura IR: {result.get('error')}")
                return result
                
    except Exception as e:
        error_msg = f"❌ Erro na captura IR: {str(e)}"
        print(error_msg)
        return {"success": False, "error": error_msg}


async def pressionar_botao_otimizado(numero_comando: int):
    """Função otimizada para pressionar botão"""
    try:
        if serial_port1 and serial_port1.is_open:
            # Pressiona
            await enviar_comando_porta(1, "P_1", f"Pressionar [{numero_comando}]", timeout=0.3)
            
            # Libera
            await enviar_comando_porta(1, "P_0", f"Liberar [{numero_comando}]", timeout=0.3)
            
            # Solicita dados IR
            if serial_port3 and serial_port3.is_open:
                serial_port3.write(b"GET\n")
                print(f"📡 [{numero_comando}] Dados IR solicitados")
                
        return True
    except Exception as e:
        print(f"❌ Erro ao pressionar botão [{numero_comando}]: {e}")
        return False


import aiohttp
import asyncio



async def pressionar_botao_otimizado(numero_comando: int):
    """Função otimizada para pressionar botão + CAPTURA IR"""
    try:
        if serial_port1 and serial_port1.is_open:
            print(f"🔘 [{numero_comando}] Pressionando botão...")
            
            # 1. Pressiona o botão (GERA o sinal IR)
            await enviar_comando_porta(1, "P_1", f"Pressionar [{numero_comando}]", timeout=0.3)
            
            # 2. Pequena pausa para o IR ser gerado
            await asyncio.sleep(0.2)
            
            # 3. Libera o botão
            await enviar_comando_porta(1, "P_0", f"Liberar [{numero_comando}]", timeout=0.3)
            
            # 4. CAPTURA os dados IR gerados (LEITURA via Node.js)
            print(f"📡 [{numero_comando}] Capturando dados IR...")
            capture_task = asyncio.create_task(
                capturar_dados_ir(
                    nano='nano1',
                    timeout=8000,  # 8 segundos timeout
                    salvar_captura=True
                )
            )
            
            # Não espera pela captura - executa em background
            # Para esperar: await capture_task
            
            print(f"✅ [{numero_comando}] Ação concluída - Captura IR em background")
            
        return True
        
    except Exception as e:
        print(f"❌ Erro ao pressionar botão [{numero_comando}]: {e}")
        return False

async def _salvar_resposta_arquivo(dados: Dict[str, Any], nano: str, diretorio_saida: Optional[str] = None) -> None:
    """Salva a resposta em arquivo JSON organizado"""
    try:
        # Define diretório de saída
        if diretorio_saida:
            diretorio = Path(diretorio_saida)
        else:
            # Diretório padrão organizado
            diretorio = Path.home() / "ir_data" / "capturas"
        
        # Cria diretório se não existir
        diretorio.mkdir(parents=True, exist_ok=True)
        
        # Nome do arquivo com timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_arquivo = f"ir_{nano}_{timestamp}.json"
        caminho_arquivo = diretorio / nome_arquivo
        
        # Prepara dados para salvar
        dados_arquivo = {
            "metadata": {
                "nano": nano,
                "timestamp": dados.get('timestamp'),
                "request_id": dados.get('requestId'),
                "trigger_source": dados.get('trigger_source', 'PYTHON_API'),
                "arquivo_salvo_em": datetime.now().isoformat()
            },
            "dados_ir": dados.get('data', {})
        }
        
        # Salva arquivo
        with open(caminho_arquivo, 'w', encoding='utf-8') as f:
            json.dump(dados_arquivo, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Dados salvos em: {caminho_arquivo}")
        
        # Também salva um resumo no diretório de logs
        await _salvar_log_resumo(dados_arquivo, nano)
        
    except Exception as e:
        print(f"⚠️ Erro ao salvar arquivo: {e}")


async def _salvar_log_resumo(dados: Dict[str, Any], nano: str) -> None:
    """Salva um resumo da captura em arquivo de log consolidado"""
    try:
        log_dir = Path.home() / "ir_data" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / f"capturas_{datetime.now().strftime('%Y%m')}.json"
        
        # Lê log existente ou cria novo
        log_data = []
        if log_file.exists():
            with open(log_file, 'r', encoding='utf-8') as f:
                log_data = json.load(f)
        
        # Adiciona nova entrada
        entrada_log = {
            "timestamp": dados["metadata"]["arquivo_salvo_em"],
            "nano": nano,
            "request_id": dados["metadata"]["request_id"],
            "arquivo": dados["metadata"]["arquivo_salvo_em"].split('.')[0] + ".json"
        }
        
        log_data.append(entrada_log)
        
        # Salva log atualizado
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)
            
    except Exception as e:
        print(f"⚠️ Erro ao salvar log: {e}")

async def salvar_json_consolidado(dados_ir: list, relatorio_controles: Optional[Dict] = None):
    """Salva TODOS os dados IR em um único arquivo JSON consolidado"""
    try:
        # Cria diretório se não existir
        output_dir = Path("ir_captures_consolidado")
        output_dir.mkdir(exist_ok=True)
        
        # Nome do arquivo com timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"mapeamento_ir_completo_{timestamp}.json"
        filepath = output_dir / filename
        
        # Estrutura do arquivo consolidado
        dados_consolidados = {
            "metadata": {
                "arquivo_salvo_em": datetime.now().isoformat(),
                "total_botoes_mapeados": len(dados_ir),
                "sequencia_executada": "FingerDown + Início1",
                "timestamp_inicio": dados_ir[0]['timestamp'] if dados_ir else None,
                "timestamp_fim": datetime.now().isoformat()
            },
            "botoes_mapeados": dados_ir,
            "relatorio_controles": relatorio_controles or {}
        }
        
        # Salva o arquivo
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(dados_consolidados, f, indent=2, ensure_ascii=False)
        
        print(f"💾 ARQUIVO CONSOLIDADO SALVO: {filepath}")
        print(f"📊 Total de botões mapeados: {len(dados_ir)}")
        
        return str(filepath)
        
    except Exception as e:
        print(f"❌ Erro ao salvar JSON consolidado: {e}")
        return ""

async def finalizar_processo():
    """Finaliza o processo de forma segura"""
    global libera_envio_comandos
    
    try:
        print("🔄 Finalizando processo...")
        libera_envio_comandos = False
        
        # Sequência de finalização
        await enviar_comando_porta(1, "P_0", "Liberar pressão final", timeout=0.5)
        await enviar_comando_porta(1, "B1_0", "Desligar IR", timeout=0.5)
        await enviar_comando_porta(2, "P_0", "Reset Porta 2", timeout=0.5)
        await enviar_comando_porta(2, "ENA", "Habilitar GRBL", timeout=0.5)
        
        # Move para posição segura
        await enviar_comando_porta(2, "G90 X10 Y10", "Posição segura", timeout=2.0)
        
        print("✅ Processo finalizado com sucesso")
        
    except Exception as e:
        print(f"⚠️ Erro na finalização: {e}")


async def ler_capturas_ir(diretorio: Optional[str] = None) -> list:
    """Lê todas as capturas IR salvas"""
    if not diretorio:
        diretorio = Path.home() / "ir_data" / "capturas"
    else:
        diretorio = Path(diretorio)
    
    if not diretorio.exists():
        print(f"❌ Diretório não encontrado: {diretorio}")
        return []
    
    arquivos_json = list(diretorio.glob("ir_*.json"))
    capturas = []
    
    for arquivo in arquivos_json:
        try:
            with open(arquivo, 'r', encoding='utf-8') as f:
                dados = json.load(f)
                capturas.append({
                    "arquivo": arquivo.name,
                    "caminho": str(arquivo),
                    "dados": dados
                })
        except Exception as e:
            print(f"⚠️ Erro ao ler arquivo {arquivo}: {e}")
    
    print(f"📂 Encontradas {len(capturas)} capturas IR")
    return capturas


async def ler_json_diretorio(caminho_arquivo=None):
    """
    Lê um arquivo JSON de um diretório específico e retorna os dados no terminal
    
    Args:
        caminho_arquivo (str): Caminho completo para o arquivo JSON. 
                              Se None, usa um caminho padrão.
    
    Returns:
        dict: Dados do JSON ou None em caso de erro
    """
    try:
        # Se nenhum caminho for especificado, usa um padrão
        if caminho_arquivo is None:
            # Define um caminho padrão - ajuste conforme sua necessidade
            caminho_arquivo = "config/comandos.json"
        
        print(f"📁 Tentando ler arquivo: {caminho_arquivo}")
        
        # Verifica se o arquivo existe
        if not os.path.exists(caminho_arquivo):
            print(f"❌ Arquivo não encontrado: {caminho_arquivo}")
            await finalizar_processo()
            return None
        
        # Lê o arquivo JSON
        with open(caminho_arquivo, 'r', encoding='utf-8') as arquivo:
            dados = json.load(arquivo)
        
        # Exibe os dados no terminal de forma organizada
        print("📊 DADOS DO ARQUIVO JSON:")
        print("=" * 50)
        print(json.dumps(dados, indent=2, ensure_ascii=False))
        print("=" * 50)
        
        # Mostra informações básicas sobre a estrutura
        if isinstance(dados, list):
            print(f"📋 Total de itens na lista: {len(dados)}")
            if dados and isinstance(dados[0], dict):
                print("🔑 Chaves disponíveis:", list(dados[0].keys()))
        elif isinstance(dados, dict):
            print("🔑 Chaves disponíveis:", list(dados.keys()))
        
        print("✅ LEITURA DO JSON CONCLUÍDA COM SUCESSO")
        await finalizar_processo()
        
        return dados
        
    except json.JSONDecodeError as e:
        print(f"❌ Erro ao decodificar JSON: {e}")
        await finalizar_processo()
        return None
    except Exception as e:
        print(f"❌ Erro ao ler arquivo JSON: {e}")
        await finalizar_processo()
        return None



@app.post("/capturar-ir/{nano}")
async def capturar_ir_endpoint(nano: str):
    """Endpoint para CAPTURAR dados IR (apenas leitura)"""
    try:
        result = await capturar_dados_ir(nano=nano, salvar_captura=True)
        
        if result.get('success'):
            return {
                "status": "success",
                "message": f"Dados IR capturados do {nano}",
                "nano": nano,
                "timestamp": result.get('timestamp'),
                "request_id": result.get('request_id'),
                "saved_file": result.get('saved_file')
            }
        else:
            return {
                "status": "error", 
                "message": result.get('error', 'Erro desconhecido'),
                "nano": nano
            }
            
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/status-nanos")
async def status_nanos_endpoint():
    """Verifica status dos Nanos via Node.js (apenas leitura)"""
    try:
        async with IRReader() as reader:
            status = await reader.get_nano_status()
            return status
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/testar-captura-ir")
async def testar_captura_ir():
    """Testa a captura IR de ambos os Nanos"""
    try:
        resultados = {}
        
        # Testa Nano 1
        async with IRReader() as reader:
            resultado_nano1 = await reader.capture_ir_data('nano1', timeout=5000)
            resultados['nano1'] = resultado_nano1
            
            # Pequena pausa
            await asyncio.sleep(1)
            
            # Testa Nano 2
            resultado_nano2 = await reader.capture_ir_data('nano2', timeout=5000)
            resultados['nano2'] = resultado_nano2
        
        return {
            "status": "success",
            "message": "Teste de captura IR concluído",
            "resultados": resultados,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {"status": "error", "message": str(e)}




@app.post("/emergency_stop")
async def emergency_stop_endpoint():
    """Endpoint para parada de emergência"""
    await emergency_stop()
    return {"status": "success", "message": "Emergency stop executado"}

@app.post("/reset_sequence")
async def reset_sequence():
    """Reinicia a sequência de comandos"""
    global linha_atual, libera_envio_comandos
    linha_atual = 0
    libera_envio_comandos = False
    await emergency_stop()
    return {"status": "success", "message": "Sequência reiniciada"}

@app.post("/start_complete_process")
async def start_complete_process():
    """Inicia o processo completo FingerDown + Início1"""
    try:
        result = await fingerdown()
        return {"status": "success", "message": "Processo completo iniciado", "data": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}

async def execute_start_with_photos():
    """Função interna para executar o processo completo com fotos"""
    global fingerdown_running, current_test_cycle
    
    if fingerdown_running:
        print("⚠️ Teste já em execução, ignorando comando START")
        return {"status": "error", "message": "FingerDown já em execução"}
    
    try:
        fingerdown_running = True
        current_test_cycle += 1
        
        # 🗑️ LIMPA IMAGENS DE TESTE DO CICLO ANTERIOR
        print("🗑️ Limpando imagens de teste do ciclo anterior...")
        limpar_imagens_teste()
        
        print("=== INICIANDO FINGERDOWN COM FOTOS ===")
        print(f"📦 Ciclo de teste: {current_test_cycle}")
        
        # Verificar portas conectadas
        port1_connected = serial_port1 and serial_port1.is_open
        port2_connected = serial_port2 and serial_port2.is_open
        
        print(f"🔌 Porta 1 conectada: {port1_connected}")
        print(f"🔌 Porta 2 conectada: {port2_connected}")
        
        if not port1_connected or not port2_connected:
            raise Exception("Portas necessárias não conectadas")
        
        # VERIFICAÇÃO INICIAL DE ESTADO
        await verificar_estado_inicial()
        
        # SEQUÊNCIA FINGERDOWN OTIMIZADA
        # 1. Avançar (Porta 1)
        await enviar_comando_porta(1, "K2_1", "Avançar", timeout=3.0)
        
        # 2. Mover na posição (Porta 2) - COM VERIFICAÇÃO
        await enviar_comando_porta(2, "G90 X29.787 Y82.987", "Mover para posição inicial", timeout=4.0)
        
        # 3. Pressionar (Porta 1)
        await enviar_comando_porta(1, "P_1", "Pressionar", timeout=1.5)
        
        # 4. Travar (Porta 1)
        await enviar_comando_porta(1, "K4_1", "Travar", timeout=1.0)
        
        # 5. Expandir a pilha (Porta 1) - COM CONTROLE
        await enviar_comando_porta(1, "K7_1", "Expandir pilha - 1º", timeout=0.8)
        await asyncio.sleep(0.2)  # Pequena pausa entre expansões
        await enviar_comando_porta(1, "K7_1", "Expandir pilha - 2º", timeout=0.8)
        
        # 6. Tirar o pressionamento (Porta 1)
        await enviar_comando_porta(1, "P_0", "Liberar pressão", timeout=1.0)
        
        print("✅ FINGERDOWN COM FOTOS CONCLUÍDO")

        # Inicia sequência principal COM FOTOS
        await inicio1_com_fotos()

        return {
            "status": "success", 
            "message": "FingerDown com fotos executado com sucesso",
            "cycle": current_test_cycle,
            "timestamp": datetime.now().isoformat(),
            "port1_connected": port1_connected,
            "port2_connected": port2_connected
        }
        
    except Exception as e:
        error_msg = f"❌ Erro crítico no FingerDown com fotos: {str(e)}"
        print(error_msg)
        await emergency_stop()
        return {"status": "error", "message": error_msg}
    finally:
        fingerdown_running = False

@app.post("/start_complete_process_with_photos")
async def start_complete_process_with_photos():
    """Inicia o processo completo FingerDown + Início1 COM CAPTURA DE FOTOS a cada botão pressionado"""
    print("🎯 ENDPOINT /start_complete_process_with_photos ACESSADO!")
    
    if fingerdown_running:
        raise HTTPException(status_code=400, detail="FingerDown já em execução")
    
    result = await execute_start_with_photos()
    
    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result.get("message", "Erro desconhecido"))
    
    return result

@app.post("/stop_process")
async def stop_process():
    """Para o processo em execução"""
    global libera_envio_comandos, process_running, fingerdown_running
    try:
        libera_envio_comandos = False
        process_running = False
        fingerdown_running = False
        await emergency_stop()
        return {"status": "success", "message": "Processo parado"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/reset_system")
async def reset_system():
    """Reseta o sistema"""
    global linha_atual, libera_envio_comandos, process_running, fingerdown_running, current_test_cycle
    try:
        linha_atual = 0
        libera_envio_comandos = False
        process_running = False
        fingerdown_running = False
        current_test_cycle = 0
        await emergency_stop()
        return {"status": "success", "message": "Sistema resetado"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/test_ir_sequence")
async def test_ir_sequence():
    """Testa a sequência IR"""
    try:
        result = await testar_captura_ir()
        return {"status": "success", "message": "Teste IR iniciado", "data": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# Mantém a escuta IR
async def listen_ir_data():
    """Escuta dados da porta IR (Nano)"""
    try:
        if serial_port3 and serial_port3.is_open:
            while serial_port3.is_open:
                if serial_port3.in_waiting > 0:
                    data = serial_port3.readline().decode().strip()
                    if data:
                        print(f"📟 DADO IR RECEBIDO: {data}")
                await asyncio.sleep(0.1)
    except Exception as e:
        print(f"Erro na escuta IR: {e}")

# Escuta comando START via pneumática (Porta 1)
async def listen_pneumatic_start():
    """Escuta comando START via pneumática na Porta 1"""
    global fingerdown_running, serial_port1, serial_port2, last_pneumatic_message
    
    print("🔌 Iniciando escuta de comando START via pneumática (Porta 1)...")
    
    while True:
        try:
            # Verifica se as portas 1 e 2 estão conectadas
            port1_connected = serial_port1 and serial_port1.is_open
            port2_connected = serial_port2 and serial_port2.is_open
            
            if port1_connected and port2_connected:
                # Verifica se há dados na porta 1
                if serial_port1.in_waiting > 0:
                    # Lê o comando
                    data = serial_port1.readline().decode().strip()
                    
                    if data:
                        print(f"📥 DADO RECEBIDO DA PNEUMÁTICA: {data}")
                        
                        # Verifica se é o comando START (case-insensitive)
                        if data.upper() == "START":
                            print("🚀 COMANDO START RECEBIDO VIA PNEUMÁTICA!")
                            
                            # Atualiza mensagem para a dashboard
                            last_pneumatic_message = "🚀 START recebido via pneumática! Iniciando teste..."
                            
                            # Verifica se já não está executando
                            if not fingerdown_running:
                                # Limpa o buffer completamente antes de processar
                                try:
                                    serial_port1.reset_input_buffer()  # Limpa buffer de entrada
                                    serial_port1.reset_output_buffer()  # Limpa buffer de saída
                                    # Garante que não há dados pendentes
                                    while serial_port1.in_waiting > 0:
                                        serial_port1.read(serial_port1.in_waiting)
                                    print("🧹 Buffer da Porta 1 completamente limpo")
                                except Exception as e:
                                    print(f"⚠️ Erro ao limpar buffer: {e}")
                                
                                # Executa o teste com fotos
                                print("🎯 Iniciando teste via pneumática...")
                                try:
                                    # Executa o teste diretamente
                                    asyncio.create_task(execute_start_with_photos())
                                except Exception as e:
                                    print(f"❌ Erro ao iniciar teste via pneumática: {e}")
                                    last_pneumatic_message = f"❌ Erro ao iniciar teste: {str(e)}"
                            else:
                                print("⚠️ Teste já em execução, ignorando comando START")
                                last_pneumatic_message = "⚠️ Teste já em execução, comando START ignorado"
                                # Limpa o buffer mesmo se o teste estiver rodando
                                try:
                                    serial_port1.reset_input_buffer()
                                    while serial_port1.in_waiting > 0:
                                        serial_port1.read(serial_port1.in_waiting)
                                except:
                                    pass
                        else:
                            print(f"📝 Comando recebido (não é START): {data}")
                            last_pneumatic_message = f"📝 Comando recebido (não é START): {data}"
                            
                            # Limpa o buffer mesmo se não for START
                            try:
                                serial_port1.reset_input_buffer()
                                while serial_port1.in_waiting > 0:
                                    serial_port1.read(serial_port1.in_waiting)
                            except:
                                pass
            else:
                # Se as portas não estiverem conectadas, limpa a mensagem
                if not port1_connected or not port2_connected:
                    last_pneumatic_message = None
            
            # Aguarda um pouco antes de verificar novamente
            await asyncio.sleep(0.1)
            
        except Exception as e:
            print(f"❌ Erro na escuta pneumática: {e}")
            last_pneumatic_message = f"❌ Erro na escuta pneumática: {str(e)}"
            await asyncio.sleep(1.0)  # Aguarda mais tempo em caso de erro











# SEUS OUTROS ENDPOINTS (mantenha os que você já tem)
@app.get("/get_serial_ports")
async def get_serial_ports():
    """Retorna lista de portas seriais disponíveis"""
    try:
        ports = list(serial.tools.list_ports.comports())
        port_list = []
        
        for port in ports:
            port_info = {
                "device": port.device,
                "description": port.description,
                "hwid": port.hwid,
            }
            port_list.append(port_info)
        
        print(f"Portas encontradas: {[port['device'] for port in port_list]}")
        
        return {
            "status": "success", 
            "ports": port_list,
            "count": len(port_list)
        }
        
    except Exception as e:
        print(f"Erro ao listar portas: {e}")
        return {
            "status": "error", 
            "message": str(e),
            "ports": []
        }

@app.get("/connect_port/{port_number}")
async def connect_serial_port(port_number: int, port_name: str, baud_rate: int = None):
    """Conecta a uma porta serial"""
    global serial_port1, serial_port2, serial_port3, serial_port4
    
    try:
        # Define baud rate padrão se não fornecido
        if baud_rate is None:
            if port_number == 3:
                baud_rate = 9600
            else:
                baud_rate = 115200
        
        print(f"Tentando conectar porta {port_number}: {port_name} @ {baud_rate} baud")
        
        if port_number == 1:
            if serial_port1 and serial_port1.is_open:
                serial_port1.close()
            serial_port1 = serial.Serial(port_name, baud_rate, timeout=1)
            return {"status": "success", "message": f"Porta 1 conectada: {port_name} @ {baud_rate} baud"}
        elif port_number == 2:
            if serial_port2 and serial_port2.is_open:
                serial_port2.close()
            serial_port2 = serial.Serial(port_name, baud_rate, timeout=1)
            return {"status": "success", "message": f"Porta 2 conectada: {port_name} @ {baud_rate} baud"}
        elif port_number == 3:
            if serial_port3 and serial_port3.is_open:
                serial_port3.close()
            serial_port3 = serial.Serial(port_name, baud_rate, timeout=1)
            return {"status": "success", "message": f"Porta 3 conectada: {port_name} @ {baud_rate} baud"}
        elif port_number == 4:
            if serial_port4 and serial_port4.is_open:
                serial_port4.close()
            serial_port4 = serial.Serial(port_name, baud_rate, timeout=1)
            return {"status": "success", "message": f"Porta 4 conectada: {port_name} @ {baud_rate} baud"}
        else:
            return {"status": "error", "message": "Número de porta inválido"}
    except Exception as e:
        print(f"Erro ao conectar porta {port_number}: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/disconnect_port/{port_number}")
async def disconnect_serial_port(port_number: int):
    """Desconecta uma porta serial"""
    global serial_port1, serial_port2, serial_port3, serial_port4
    
    try:
        print(f"Desconectando porta {port_number}")
        
        if port_number == 1:
            if serial_port1 and serial_port1.is_open:
                serial_port1.close()
                serial_port1 = None
            return {"status": "success", "message": "Porta 1 desconectada"}
        elif port_number == 2:
            if serial_port2 and serial_port2.is_open:
                serial_port2.close()
                serial_port2 = None
            return {"status": "success", "message": "Porta 2 desconectada"}
        elif port_number == 3:
            if serial_port3 and serial_port3.is_open:
                serial_port3.close()
                serial_port3 = None
            return {"status": "success", "message": "Porta 3 desconectada"}
        elif port_number == 4:
            if serial_port4 and serial_port4.is_open:
                serial_port4.close()
                serial_port4 = None
            return {"status": "success", "message": "Porta 4 desconectada"}
        else:
            return {"status": "error", "message": "Número de porta inválido"}
    except Exception as e:
        print(f"Erro ao desconectar porta {port_number}: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/send_home/{port_number}")
async def send_home_command(port_number: int):
    """Envia comando $H (Home)"""
    global serial_port1, serial_port2
    
    try:
        if port_number == 1:
            if not serial_port1 or not serial_port1.is_open:
                return {"status": "error", "message": "Porta 1 não está conectada"}
            print("Enviando comando $H (Home) para Porta 1")
            serial_port1.write(b"$H\n")
            
        elif port_number == 2:
            if not serial_port2 or not serial_port2.is_open:
                return {"status": "error", "message": "Porta 2 não está conectada"}
            print("Enviando comando $H (Home) para Porta 2")
            serial_port2.write(b"$H\n")
            
        else:
            return {"status": "error", "message": "Número de porta inválido"}
        
        return {"status": "success", "message": f"Comando $H (Home) enviado para Porta {port_number}"}
        
    except Exception as e:
        print(f"Erro ao enviar comando Home: {e}")
        return {"status": "error", "message": str(e)}

# =========================
# ENDPOINTS DE CÂMERAS
# =========================

@app.get("/stream/{camera_id}")
async def stream_camera(camera_id: int):
    """Stream de vídeo de uma câmera específica"""
    if camera_id < 0 or camera_id >= MAX_CAMERAS:
        raise HTTPException(status_code=404, detail=f"Câmera {camera_id} não existe")
    
    manager = camera_managers.get(camera_id)
    if manager is None:
        raise HTTPException(status_code=404, detail=f"Gerenciador de câmera {camera_id} não encontrado")
    
    return StreamingResponse(
        generate_frame(camera_id),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@app.get("/camera_status")
async def get_camera_status():
    """Status de todas as câmeras"""
    status = {}
    for camera_id, manager in camera_managers.items():
        status[camera_id] = {
            "connected": manager.is_connected(),
            "running": manager.is_running,
            "has_frame": manager.get_frame() is not None,
            "reconnect_attempts": manager.reconnect_attempts
        }
    return status

@app.get("/camera_status/{camera_id}")
async def get_single_camera_status(camera_id: int):
    """Status de uma câmera específica"""
    if camera_id < 0 or camera_id >= MAX_CAMERAS:
        raise HTTPException(status_code=404, detail=f"Câmera {camera_id} não existe")
    
    manager = camera_managers.get(camera_id)
    if manager is None:
        raise HTTPException(status_code=404, detail=f"Gerenciador de câmera {camera_id} não encontrado")
    
    return {
        "camera_id": camera_id,
        "connected": manager.is_connected(),
        "running": manager.is_running,
        "has_frame": manager.get_frame() is not None,
        "reconnect_attempts": manager.reconnect_attempts
    }

@app.post("/reconnect_camera/{camera_id}")
async def reconnect_camera(camera_id: int):
    """Força reconexão de uma câmera"""
    if camera_id < 0 or camera_id >= MAX_CAMERAS:
        raise HTTPException(status_code=404, detail=f"Câmera {camera_id} não existe")
    
    manager = camera_managers.get(camera_id)
    if manager is None:
        raise HTTPException(status_code=404, detail=f"Gerenciador de câmera {camera_id} não encontrado")
    
    # Parar e reiniciar
    manager.stop()
    await asyncio.sleep(1)
    manager.start()
    
    return {"message": f"Câmera {camera_id} reconectada", "connected": manager.is_connected()}

@app.get("/capture_frame/{camera_id}")
async def capture_frame(camera_id: int):
    """Captura um frame da câmera e retorna como imagem"""
    from fastapi.responses import Response
    
    if camera_id < 0 or camera_id >= MAX_CAMERAS:
        raise HTTPException(status_code=404, detail=f"Câmera {camera_id} não existe")
    
    manager = camera_managers.get(camera_id)
    if manager is None:
        raise HTTPException(status_code=404, detail=f"Gerenciador de câmera {camera_id} não encontrado")
    
    frame = manager.get_frame()
    
    if frame is None:
        raise HTTPException(status_code=404, detail=f"Câmera {camera_id} não tem frame disponível")
    
    # Codificar frame como JPEG
    ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
    if not ret:
        raise HTTPException(status_code=500, detail="Erro ao codificar frame")
    
    frame_bytes = buffer.tobytes()
    
    return Response(content=frame_bytes, media_type="image/jpeg")

@app.post("/save_camera_frame/{camera_id}")
async def save_camera_frame(camera_id: int, filename: Optional[str] = None):
    """Captura e salva um frame da câmera no servidor"""
    if camera_id < 0 or camera_id >= MAX_CAMERAS:
        raise HTTPException(status_code=404, detail=f"Câmera {camera_id} não existe")
    
    manager = camera_managers.get(camera_id)
    if manager is None:
        raise HTTPException(status_code=404, detail=f"Gerenciador de câmera {camera_id} não encontrado")
    
    frame = manager.get_frame()
    
    if frame is None:
        raise HTTPException(status_code=404, detail=f"Câmera {camera_id} não tem frame disponível")
    
    # Criar diretório de fotos se não existir
    photos_dir = Path("camera_photos")
    photos_dir.mkdir(exist_ok=True)
    
    # Nome do arquivo
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"camera_{camera_id}_{timestamp}.jpg"
    
    filepath = photos_dir / filename
    
    # Salvar frame
    cv2.imwrite(str(filepath), frame)
    
    return {
        "status": "success",
        "message": f"Foto salva com sucesso",
        "filename": filename,
        "filepath": str(filepath),
        "camera_id": camera_id
    }

# Endpoint para listar todas as rotas
@app.get("/get_test_report")
async def get_test_report():
    """Retorna o último relatório de validação dos testes"""
    global last_test_report
    if last_test_report is None:
        return {
            "status": "no_data",
            "message": "Nenhum teste foi executado ainda",
            "relatorio": None
        }
    return {
        "status": "success",
        "relatorio": last_test_report
    }

@app.get("/get_pneumatic_message")
async def get_pneumatic_message():
    """Retorna a última mensagem recebida via pneumática"""
    global last_pneumatic_message, serial_port1, serial_port2
    
    port1_connected = serial_port1 and serial_port1.is_open
    port2_connected = serial_port2 and serial_port2.is_open
    
    return {
        "status": "success",
        "message": last_pneumatic_message,
        "port1_connected": port1_connected,
        "port2_connected": port2_connected,
        "ready": port1_connected and port2_connected
    }

@app.get("/routes")
async def list_routes():
    routes = []
    for route in app.routes:
        if hasattr(route, "methods") and hasattr(route, "path"):
            routes.append({
                "path": route.path,
                "methods": list(route.methods)
            })
    return {"routes": routes}

if __name__ == "__main__":
    print("=== SERVIDOR INICIADO ===")
    print("Acesse: http://localhost:8000")
    print("=== CONFIGURAÇÃO CORS ===")
    print("Origins permitidos: http://localhost:8080, http://127.0.0.1:8080")
    print("====================")
    
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
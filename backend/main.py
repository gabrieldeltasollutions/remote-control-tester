from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import serial
import serial.tools.list_ports
import asyncio
import time
from datetime import datetime
import os
from fastapi import HTTPException
import json

app = FastAPI()

# CONFIGURAÇÃO CORS CORRIGIDA - DEVE VIR ANTES DE TODAS AS ROTAS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://127.0.0.1:8080", "http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


import threading
import time
from concurrent.futures import ThreadPoolExecutor
from enum import Enum



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

# Variáveis de controle
process_running = False
linha_atual = 0
libera_envio_comandos = False

# Variáveis específicas do FingerDown
fingerdown_running = False
current_test_cycle = 0



test_coordinates = [
    {"command": "G90", "x": 41, "y": 135},     # BOTAO POWER
    {"command": "G90", "x": 14, "y": 135},     # BOTAO FUNÇAO
    {"command": "G90", "x": 41, "y": 114},     # BOTAO TEMPORIZADO
    {"command": "G90", "x": 14, "y": 114},     # BOTAO VELOCIDADE
    {"command": "G90", "x": 28, "y": 127},     # BOTAO TEMP MAX
    {"command": "G90", "x": 28, "y": 102},     # BOTAO TEMP DOWN
    {"command": "G90", "x": 42, "y": 96},      # OCULTO ABAIXO TEMPORIZADOR
    {"command": "G90", "x": 14, "y": 94},      # OSCILAR
    {"command": "G90", "x": 14, "y": 71},      # TURBO
    {"command": "G90", "x": 24, "y": 71},      # CONFORTO
    {"command": "G90", "x": 34, "y": 71},      # LIMPAR
    {"command": "G90", "x": 44, "y": 71},      # IONAIR
    {"command": "G90", "x": 44, "y": 55},      # OCULTO ABAIXO IONAIR
    {"command": "G90", "x": 34, "y": 55},      # ANTIMORFO
    {"command": "G90", "x": 24, "y": 55},      # VISOR
    {"command": "G90", "x": 14, "y": 55}       # DORMIR
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

async def executar_sequencia_comandos():
    """Executa a sequência completa de comandos com controle robusto"""
    global linha_atual, libera_envio_comandos
    
    try:
        print(f"🎯 INICIANDO SEQUÊNCIA DE {len(test_coordinates)} COMANDOS")
        
        for i, coord in enumerate(test_coordinates):
            if not libera_envio_comandos:
                print("⏸️ Sequência interrompida")
                break
                
            linha_atual = i
            print(f"🔹 Comando {i+1}/{len(test_coordinates)}")
            
            # Envia movimento
            command = f"{coord['command']} X{coord['x']} Y{coord['y']}"
            await enviar_comando_porta(2, command, f"Movimento {i+1}", timeout=1.5)
            
            # Pressiona botão
            await pressionar_botao_otimizado(i+1)
            
            # Pequena pausa entre comandos
            if i < len(test_coordinates) - 1:  # Não espera após o último
                await asyncio.sleep(1.0)
        
        print("✅ SEQUÊNCIA DE COMANDOS CONCLUÍDA")
        await ler_json_diretorio()
    
    except Exception as e:
        print(f"❌ Erro na sequência de comandos: {e}")
        await emergency_stop()

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
async def connect_serial_port(port_number: int, port_name: str):
    """Conecta a uma porta serial"""
    global serial_port1, serial_port2, serial_port3
    
    try:
        print(f"Tentando conectar porta {port_number}: {port_name}")
        
        if port_number == 1:
            if serial_port1 and serial_port1.is_open:
                serial_port1.close()
            serial_port1 = serial.Serial(port_name, 115200, timeout=1)
            return {"status": "success", "message": f"Porta 1 conectada: {port_name}"}
        elif port_number == 2:
            if serial_port2 and serial_port2.is_open:
                serial_port2.close()
            serial_port2 = serial.Serial(port_name, 115200, timeout=1)
            return {"status": "success", "message": f"Porta 2 conectada: {port_name}"}
        elif port_number == 3:
            if serial_port3 and serial_port3.is_open:
                serial_port3.close()
            serial_port3 = serial.Serial(port_name, 9600, timeout=1)
            return {"status": "success", "message": f"Porta 3 conectada: {port_name}"}
        else:
            return {"status": "error", "message": "Número de porta inválido"}
    except Exception as e:
        print(f"Erro ao conectar porta {port_number}: {e}")
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

# Endpoint para listar todas as rotas
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
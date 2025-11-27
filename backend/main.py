from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import serial
import serial.tools.list_ports
import asyncio
import time

app = FastAPI()

# Configuração CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Variáveis globais para as portas seriais
serial_port1 = None  # Porta para comandos K/P (Arduino/Relés)
serial_port2 = None  # Porta para comandos G-code (GRBL)
serial_port3 = None  # Porta para receber dados IR (Nano)

# Variáveis de controle
process_running = False
linha_atual = 0
libera_envio_comandos = False

# Dados de teste (coordenadas)
test_coordinates = [
    {"command": "G90", "x": "10", "y": "10"},
    {"command": "G90", "x": "20", "y": "20"},
    {"command": "G90", "x": "30", "y": "30"},
    {"command": "G90", "x": "40", "y": "40"},
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
            <button onclick="sendCommand(1, 'K4_1')" class="command-btn">K4_1 (Travar)</button>
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
            serial_port3 = serial.Serial(port_name, 9600, timeout=1)  # Nano geralmente usa 9600
            return {"status": "success", "message": f"Porta 3 conectada: {port_name}"}
        else:
            return {"status": "error", "message": "Número de porta inválido"}
    except Exception as e:
        print(f"Erro ao conectar porta {port_number}: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/disconnect_port/{port_number}")
async def disconnect_serial_port(port_number: int):
    """Desconecta uma porta serial"""
    global serial_port1, serial_port2, serial_port3
    
    try:
        if port_number == 1 and serial_port1:
            serial_port1.close()
            serial_port1 = None
            print("Porta 1 desconectada")
        elif port_number == 2 and serial_port2:
            serial_port2.close()
            serial_port2 = None
            print("Porta 2 desconectada")
        elif port_number == 3 and serial_port3:
            serial_port3.close()
            serial_port3 = None
            print("Porta 3 desconectada")
            
        return {"status": "success", "message": f"Porta {port_number} desconectada"}
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

@app.post("/send_command/{port_number}")
async def send_custom_command(port_number: int, command: str):
    """Envia um comando customizado"""
    global serial_port1, serial_port2, serial_port3
    
    try:
        port = None
        if port_number == 1:
            port = serial_port1
        elif port_number == 2:
            port = serial_port2
        elif port_number == 3:
            port = serial_port3
            
        if not port or not port.is_open:
            return {"status": "error", "message": f"Porta {port_number} não está conectada"}
        
        print(f"Enviando comando para Porta {port_number}: {command}")
        
        # Adiciona quebra de linha se necessário
        if not command.endswith('\n'):
            command += '\n'
            
        port.write(command.encode())
        
        return {"status": "success", "message": f"Comando enviado para Porta {port_number}: {command}"}
        
    except Exception as e:
        print(f"Erro ao enviar comando: {e}")
        return {"status": "error", "message": str(e)}

async def fingerdown1():
    """Sequência FingerDown 1"""
    try:
        print("=== INICIANDO FINGERDOWN 1 ===")
        
        # Verificar portas conectadas
        port1_connected = serial_port1 and serial_port1.is_open
        port2_connected = serial_port2 and serial_port2.is_open
        
        if not port1_connected:
            print("⚠️ Aviso: Porta 1 não conectada")
        if not port2_connected:
            print("⚠️ Aviso: Porta 2 não conectada")
        
        # 1. Avançar (Porta 1)
        if port1_connected:
            serial_port1.write(b"K2_1\n")
            print("Enviado: K2_1 (Avançar)")
            await asyncio.sleep(2)

        # 2. Mover na posição (Porta 2)  
        if port2_connected:
            command = "G90 X29.787 Y82.987\n"
            serial_port2.write(command.encode())
            print(f"Enviado: {command.strip()} (Mover para posição)")
            await asyncio.sleep(3)

        await asyncio.sleep(0.2)

        # 3. Pressionar (Porta 1)
        if port1_connected:
            serial_port1.write(b"P_1\n")
            print("Enviado: P_1 (Pressionar)")
            await asyncio.sleep(1)

        # 4. Travar (Porta 1)
        if port1_connected:
            serial_port1.write(b"K4_1\n")
            print("Enviado: K4_1 (Travar)")
            await asyncio.sleep(0.5)

        # 5. Expandir a pilha (Porta 1)
        if port1_connected:
            serial_port1.write(b"K7_1\n")
            print("Enviado: K7_1 (Expandir pilha - 1º)")
            await asyncio.sleep(0.3)
            serial_port1.write(b"K7_1\n")
            print("Enviado: K7_1 (Expandir pilha - 2º)")
            await asyncio.sleep(0.5)

        # 6. Tirar o pressionamento (Porta 1)
        if port1_connected:
            serial_port1.write(b"P_0\n")
            print("Enviado: P_0 (Liberar pressão)")
            await asyncio.sleep(1.5)

        print("✅ FINGERDOWN 1 CONCLUÍDO")
        return {"status": "success", "message": "FingerDown executado"}
        
    except Exception as e:
        print(f"❌ Erro no FingerDown: {e}")
        return {"status": "error", "message": str(e)}

async def inicio1():
    """Início do teste real - sequência de comandos"""
    global linha_atual, libera_envio_comandos
    
    try:
        print("=== INICIANDO INÍCIO1 (TESTE REAL) ===")
        
        # Libera envio de comandos
        libera_envio_comandos = True
        linha_atual = 0
        
        # Envia comando para iniciar IR
        if serial_port1 and serial_port1.is_open:
            serial_port1.write(b"B1_1\n")
            print("Enviado: B1_1 (Iniciar IR)")
            await asyncio.sleep(0.1)
            serial_port1.write(b"B1_1\n")  # Duplo comando
            print("Enviado: B1_1 (Iniciar IR - 2º)")
            await asyncio.sleep(2.9)
        
        # Inicia sequência de comandos
        await enviar_proximo_comando()
        
        return {"status": "success", "message": "Início1 executado"}
        
    except Exception as e:
        print(f"❌ Erro no Início1: {e}")
        return {"status": "error", "message": str(e)}

async def enviar_proximo_comando():
    """Envia próximo comando da sequência"""
    global linha_atual, libera_envio_comandos
    
    try:
        if not libera_envio_comandos:
            return
            
        if linha_atual < len(test_coordinates):
            coord = test_coordinates[linha_atual]
            command = f"{coord['command']} X{coord['x']} Y{coord['y']}\n"
            
            if serial_port2 and serial_port2.is_open:
                serial_port2.write(command.encode())
                print(f"Enviado comando {linha_atual + 1}: {command.strip()}")
                
                # Solicita dados IR após movimento
                if serial_port3 and serial_port3.is_open:
                    await asyncio.sleep(0.5)
                    serial_port3.write(b"GET\n")
                    print("Solicitado dados IR: GET")
            
            linha_atual += 1
            
            # Agenda próximo comando
            await asyncio.sleep(2)
            await enviar_proximo_comando()
            
        else:
            print("✅ SEQUÊNCIA DE COMANDOS CONCLUÍDA")
            libera_envio_comandos = False
            
            # Finaliza processo
            if serial_port1 and serial_port1.is_open:
                serial_port1.write(b"P_0\n")
                serial_port1.write(b"B1_0\n")
                serial_port1.write(b"K2_0\n")
                serial_port1.write(b"ENA\n")
                print("Processo finalizado - Comandos de reset enviados")
                
    except Exception as e:
        print(f"❌ Erro ao enviar comando: {e}")

async def listen_ir_data():
    """Escuta dados da porta IR (Nano)"""
    try:
        if serial_port3 and serial_port3.is_open:
            while serial_port3.is_open:
                if serial_port3.in_waiting > 0:
                    data = serial_port3.readline().decode().strip()
                    if data:
                        print(f"📟 DADO IR RECEBIDO: {data}")
                        # Aqui você processaria os dados IR
                await asyncio.sleep(0.1)
    except Exception as e:
        print(f"Erro na escuta IR: {e}")

@app.post("/start_complete_process")
async def start_complete_process(background_tasks: BackgroundTasks):
    """Inicia o processo completo: FingerDown + Início1"""
    try:
        print("🚀 INICIANDO PROCESSO COMPLETO")
        
        # Executa FingerDown primeiro
        fingerdown_result = await fingerdown1()
        if fingerdown_result["status"] == "error":
            return fingerdown_result
            
        # Aguarda um pouco e inicia o teste real
        await asyncio.sleep(1)
        inicio_result = await inicio1()
        
        # Inicia escuta de dados IR em background
        background_tasks.add_task(listen_ir_data)
        
        return {"status": "success", "message": "Processo completo iniciado"}
        
    except Exception as e:
        print(f"❌ Erro no processo completo: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/test_ir_sequence")
async def test_ir_sequence(background_tasks: BackgroundTasks):
    """Testa apenas a sequência IR"""
    try:
        print("🧪 TESTANDO SEQUÊNCIA IR")
        
        # Inicia escuta IR
        background_tasks.add_task(listen_ir_data)
        
        # Envia comando para iniciar IR
        if serial_port1 and serial_port1.is_open:
            serial_port1.write(b"B1_1\n")
            await asyncio.sleep(0.1)
            serial_port1.write(b"B1_1\n")
            
        # Executa sequência de teste
        global linha_atual, libera_envio_comandos
        linha_atual = 0
        libera_envio_comandos = True
        await enviar_proximo_comando()
        
        return {"status": "success", "message": "Teste IR iniciado"}
        
    except Exception as e:
        print(f"❌ Erro no teste IR: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/stop_process")
async def stop_process():
    """Para o processo em execução"""
    global libera_envio_comandos
    libera_envio_comandos = False
    
    # Envia comandos de parada
    if serial_port1 and serial_port1.is_open:
        serial_port1.write(b"P_0\n")
        serial_port1.write(b"B1_0\n")
        serial_port1.write(b"K2_0\n")
        serial_port1.write(b"ENA\n")
    
    print("⏹️ PROCESSO PARADO")
    return {"status": "success", "message": "Processo parado"}

@app.post("/reset_system")
async def reset_system():
    """Reseta o sistema"""
    global linha_atual, libera_envio_comandos
    linha_atual = 0
    libera_envio_comandos = False
    
    print("🔄 SISTEMA RESETADO")
    return {"status": "success", "message": "Sistema resetado"}

if __name__ == "__main__":
    print("=== SERVIDOR INICIADO ===")
    print("Acesse: http://localhost:8000")
    print("=== CONFIGURAÇÃO ===")
    print("Porta 1: Comandos K/P (Arduino/Relés)")
    print("Porta 2: Comandos G-code (GRBL)") 
    print("Porta 3: Dados IR (Nano)")
    print("====================")
    
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
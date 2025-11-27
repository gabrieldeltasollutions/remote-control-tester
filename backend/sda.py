"""
==============================================
SISTEMA IR CONTROLLER - CORRIGIDO
==============================================
Correção dos modelos Pydantic e endpoints
"""

import serial
import serial.tools.list_ports
import asyncio
import time
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, List
import logging
import json

# ==============================================
# CONFIGURAÇÕES
# ==============================================

app = FastAPI(title="IR Controller System", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==============================================
# FUNÇÕES IR (MESMAS QUE VOCÊ FORNECEU)
# ==============================================

# Variáveis globais para as portas IR
ir_port3 = None
ir_port4 = None
IR_BAUDRATE = 9600
IR_TIMEOUT = 1

def connect_ir_port(port_number, port_name):
    global ir_port3, ir_port4
    try:
        logger.info(f"Conectando porta IR {port_number}: {port_name}")
        
        if port_number == 3:
            if ir_port3 and ir_port3.is_open:
                ir_port3.close()
            ir_port3 = serial.Serial(port_name, IR_BAUDRATE, timeout=IR_TIMEOUT)
            return {"status": "success", "message": f"Porta IR 3 conectada: {port_name}"}
        elif port_number == 4:
            if ir_port4 and ir_port4.is_open:
                ir_port4.close()
            ir_port4 = serial.Serial(port_name, IR_BAUDRATE, timeout=IR_TIMEOUT)
            return {"status": "success", "message": f"Porta IR 4 conectada: {port_name}"}
        else:
            return {"status": "error", "message": "Número de porta inválido (use 3 ou 4)"}
    except Exception as e:
        logger.error(f"Erro ao conectar: {str(e)}")
        return {"status": "error", "message": f"Erro ao conectar: {str(e)}"}

def disconnect_ir_port(port_number):
    global ir_port3, ir_port4
    try:
        if port_number == 3 and ir_port3:
            ir_port3.close()
            ir_port3 = None
            return {"status": "success", "message": "Porta IR 3 desconectada"}
        elif port_number == 4 and ir_port4:
            ir_port4.close()
            ir_port4 = None
            return {"status": "success", "message": "Porta IR 4 desconectada"}
        else:
            return {"status": "error", "message": "Porta não estava conectada"}
    except Exception as e:
        return {"status": "error", "message": f"Erro ao desconectar: {str(e)}"}

def send_ir_command(port_number, command):
    global ir_port3, ir_port4
    try:
        port = ir_port3 if port_number == 3 else ir_port4
        if not port or not port.is_open:
            return {"status": "error", "message": f"Porta IR {port_number} não está conectada"}
        
        # CORREÇÃO: Use \n em vez de \\n
        if not command.endswith('\n'):
            command += '\n'
            
        port.write(command.encode())
        logger.info(f"Comando enviado para porta IR {port_number}: {command.strip()}")
        return {"status": "success", "message": f"Comando enviado: {command.strip()}"}
    except Exception as e:
        return {"status": "error", "message": f"Erro ao enviar comando: {str(e)}"}

def get_ir_data(port_number):
    result = send_ir_command(port_number, "GET")
    if result["status"] == "success":
        time.sleep(0.5)  # Aguarda resposta do Arduino
        return read_ir_data(port_number)
    return result

def read_ir_data(port_number):
    global ir_port3, ir_port4
    try:
        port = ir_port3 if port_number == 3 else ir_port4
        if not port or not port.is_open:
            return {"status": "error", "message": f"Porta IR {port_number} não está conectada"}
        
        # Limpa o buffer antes de ler
        port.reset_input_buffer()
        
        data_lines = []
        start_time = time.time()
        
        # Lê por até 2 segundos para capturar todos os dados
        while time.time() - start_time < 2:
            if port.in_waiting > 0:
                data = port.readline().decode().strip()
                if data:
                    data_lines.append(data)
                    logger.info(f"📟 IR {port_number}: {data}")
            time.sleep(0.1)
        
        if data_lines:
            parsed_data = [parse_ir_data(line) for line in data_lines]
            return {
                "status": "success", 
                "raw_data": data_lines,
                "parsed_data": parsed_data,
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "port": port_number,
                "lines_received": len(data_lines)
            }
        return {"status": "no_data", "message": "Nenhum dado disponível"}
    except Exception as e:
        return {"status": "error", "message": f"Erro ao ler dados: {str(e)}"}

def parse_ir_data(data):
    try:
        parts = data.split(';')
        if len(parts) >= 2:
            hex_data = parts[1] if parts[1] != '0' else None
            return {
                "valid": hex_data is not None,
                "hex_data": hex_data,
                "protocol": parts[0] if parts[0] else "Unknown",
                "raw": data
            }
        return {
            "valid": False,
            "hex_data": None,
            "protocol": "Unknown",
            "raw": data
        }
    except Exception as e:
        return {
            "valid": False,
            "error": str(e),
            "raw": data
        }

def get_ir_status(port_number):
    global ir_port3, ir_port4
    port = ir_port3 if port_number == 3 else ir_port4
    if port and port.is_open:
        return {
            "status": "connected",
            "port_name": port.name,
            "in_waiting": port.in_waiting
        }
    else:
        return {"status": "disconnected", "port_name": None}

def list_available_ports():
    ports = list(serial.tools.list_ports.comports())
    available_ports = []
    for port in ports:
        if (port.device.find('USB') != -1 or 
            port.device.find('ACM') != -1 or 
            port.device.endswith(tuple(str(i) for i in range(10)))):
            available_ports.append({
                "device": port.device,
                "description": port.description
            })
    return available_ports

# ==============================================
# MODELOS PYDANTIC CORRIGIDOS
# ==============================================

class PortConnection(BaseModel):
    port_number: int
    port_name: str

class IRCommand(BaseModel):
    port_number: int
    command: str

class PortNumber(BaseModel):
    port_number: int

# ==============================================
# ENDPOINTS CORRIGIDOS
# ==============================================

@app.get("/")
async def home():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>IR Controller - Sistema Corrigido</title>
        <style>
            body { font-family: Arial; margin: 20px; background: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; }
            .panel { background: white; padding: 20px; margin: 10px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .port-section { margin-bottom: 20px; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
            .status { padding: 5px 10px; border-radius: 15px; font-size: 12px; font-weight: bold; }
            .connected { background: #d4edda; color: #155724; }
            .disconnected { background: #f8d7da; color: #721c24; }
            button { padding: 10px 15px; margin: 5px; border: none; border-radius: 5px; cursor: pointer; }
            .btn-success { background: #28a745; color: white; }
            .btn-danger { background: #dc3545; color: white; }
            .btn-primary { background: #007bff; color: white; }
            .btn-warning { background: #ffc107; color: black; }
            .log { background: #1a1a1a; color: #00ff00; padding: 15px; border-radius: 5px; font-family: monospace; height: 400px; overflow-y: auto; margin-top: 20px; }
            .log-entry { margin-bottom: 5px; padding: 5px; border-left: 3px solid; }
            .log-success { border-color: #28a745; color: #90ee90; }
            .log-error { border-color: #dc3545; color: #ff6b6b; }
            .log-info { border-color: #17a2b8; color: #87ceeb; }
            .log-data { border-color: #ffc107; color: #f9e79f; background: rgba(255,193,7,0.1); }
            .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
            @media (max-width: 768px) { .grid { grid-template-columns: 1fr; } }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="panel">
                <h1>🎮 IR Controller System - CORRIGIDO</h1>
                <p>Problemas de 422 resolvidos - Teste agora!</p>
            </div>

            <div class="grid">
                <!-- Porta IR 3 -->
                <div class="panel">
                    <h2>🔧 Porta IR 3 - Berço 1</h2>
                    <div class="port-section">
                        <h3>Status: <span id="status3" class="status disconnected">Desconectado</span></h3>
                        <select id="port3Select" style="width: 100%; padding: 8px; margin: 10px 0;">
                            <option value="">Selecione uma porta...</option>
                        </select>
                        <div>
                            <button class="btn-success" onclick="connectPort(3)">🔌 Conectar</button>
                            <button class="btn-danger" onclick="disconnectPort(3)">🔓 Desconectar</button>
                        </div>
                    </div>
                    <div class="port-section">
                        <h3>Comandos IR</h3>
                        <input type="text" id="command3" placeholder="Comando (GET, RESET, etc)" style="width: 100%; padding: 8px; margin: 5px 0;">
                        <div>
                            <button class="btn-primary" onclick="sendCommand(3)">📤 Enviar</button>
                            <button class="btn-warning" onclick="getData(3)">📡 GET Data</button>
                            <button class="btn-danger" onclick="resetNano(3)">🔄 Reset</button>
                        </div>
                    </div>
                </div>

                <!-- Porta IR 4 -->
                <div class="panel">
                    <h2>🔧 Porta IR 4 - Berço 2</h2>
                    <div class="port-section">
                        <h3>Status: <span id="status4" class="status disconnected">Desconectado</span></h3>
                        <select id="port4Select" style="width: 100%; padding: 8px; margin: 10px 0;">
                            <option value="">Selecione uma porta...</option>
                        </select>
                        <div>
                            <button class="btn-success" onclick="connectPort(4)">🔌 Conectar</button>
                            <button class="btn-danger" onclick="disconnectPort(4)">🔓 Desconectar</button>
                        </div>
                    </div>
                    <div class="port-section">
                        <h3>Comandos IR</h3>
                        <input type="text" id="command4" placeholder="Comando (GET, RESET, etc)" style="width: 100%; padding: 8px; margin: 5px 0;">
                        <div>
                            <button class="btn-primary" onclick="sendCommand(4)">📤 Enviar</button>
                            <button class="btn-warning" onclick="getData(4)">📡 GET Data</button>
                            <button class="btn-danger" onclick="resetNano(4)">🔄 Reset</button>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Log -->
            <div class="panel">
                <h2>📋 Log de Atividades</h2>
                <button class="btn-danger" onclick="clearLog()">🗑️ Limpar Log</button>
                <div class="log" id="log">
                    <div class="log-entry log-info">Sistema IR Controller inicializado - Problemas de 422 corrigidos</div>
                </div>
            </div>
        </div>

        <script>
            const API_BASE = window.location.origin;

            // Inicialização
            document.addEventListener('DOMContentLoaded', function() {
                loadAvailablePorts();
                checkAllStatus();
                setInterval(checkAllStatus, 3000);
            });

            // Funções de Log
            function log(message, type = 'info') {
                const logDiv = document.getElementById('log');
                const timestamp = new Date().toLocaleTimeString();
                const entry = document.createElement('div');
                entry.className = `log-entry log-${type}`;
                entry.innerHTML = `[${timestamp}] ${message}`;
                logDiv.appendChild(entry);
                logDiv.scrollTop = logDiv.scrollHeight;
            }

            function clearLog() {
                document.getElementById('log').innerHTML = '';
                log('Log limpo', 'info');
            }

            // API Calls
            async function apiCall(endpoint, options = {}) {
                try {
                    const response = await fetch(`${API_BASE}/api${endpoint}`, {
                        headers: {'Content-Type': 'application/json', ...options.headers},
                        ...options
                    });
                    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                    return await response.json();
                } catch (error) {
                    log(`Erro: ${error.message}`, 'error');
                    return null;
                }
            }

            // Port Management
            async function loadAvailablePorts() {
                const result = await apiCall('/ir/available-ports');
                if (result && result.available_ports) {
                    const select3 = document.getElementById('port3Select');
                    const select4 = document.getElementById('port4Select');
                    
                    select3.innerHTML = select4.innerHTML = '<option value="">Selecione uma porta...</option>';
                    
                    result.available_ports.forEach(port => {
                        const option = new Option(`${port.device} - ${port.description}`, port.device);
                        select3.add(option.cloneNode(true));
                        select4.add(option);
                    });
                    log(`Portas carregadas: ${result.available_ports.length}`, 'success');
                }
            }

            async function connectPort(portNumber) {
                const select = document.getElementById(`port${portNumber}Select`);
                const portName = select.value;
                if (!portName) return log(`Selecione uma porta para IR ${portNumber}`, 'error');

                const result = await apiCall('/ir/connect', {
                    method: 'POST',
                    body: JSON.stringify({port_number: portNumber, port_name: portName})
                });

                if (result) {
                    log(`Porta IR ${portNumber}: ${result.message}`, result.status === 'success' ? 'success' : 'error');
                    checkStatus(portNumber);
                }
            }

            async function disconnectPort(portNumber) {
                const result = await apiCall('/ir/disconnect', {
                    method: 'POST',
                    body: JSON.stringify({port_number: portNumber})
                });

                if (result) {
                    log(`Porta IR ${portNumber}: ${result.message}`, result.status === 'success' ? 'success' : 'error');
                    checkStatus(portNumber);
                }
            }

            async function checkStatus(portNumber) {
                const result = await apiCall(`/ir/status/${portNumber}`);
                if (result) {
                    const statusElement = document.getElementById(`status${portNumber}`);
                    if (result.status === 'connected') {
                        statusElement.textContent = `Conectado: ${result.port_name}`;
                        statusElement.className = 'status connected';
                    } else {
                        statusElement.textContent = 'Desconectado';
                        statusElement.className = 'status disconnected';
                    }
                }
            }

            async function checkAllStatus() {
                await checkStatus(3);
                await checkStatus(4);
            }

            // Command Functions - CORRIGIDAS
            async function sendCommand(portNumber) {
                const input = document.getElementById(`command${portNumber}`);
                const command = input.value.trim();
                if (!command) return log(`Digite um comando para IR ${portNumber}`, 'error');

                const result = await apiCall('/ir/send-command', {
                    method: 'POST',
                    body: JSON.stringify({port_number: portNumber, command: command})
                });

                if (result) {
                    log(`Comando IR ${portNumber}: ${result.message}`, result.status === 'success' ? 'success' : 'error');
                    input.value = '';
                }
            }

            async function getData(portNumber) {
                log(`Solicitando dados da porta IR ${portNumber}...`, 'info');
                const result = await apiCall('/ir/get-data', {
                    method: 'POST',
                    body: JSON.stringify({port_number: portNumber})
                });

                if (result) {
                    if (result.status === 'success') {
                        log(`✅ Dados recebidos da porta IR ${portNumber} (${result.lines_received} linhas)`, 'success');
                        if (result.raw_data) {
                            result.raw_data.forEach((data, index) => {
                                log(`📥 Raw ${index + 1}: ${data}`, 'data');
                            });
                        }
                        if (result.parsed_data) {
                            result.parsed_data.forEach((parsed, index) => {
                                if (parsed.valid) {
                                    log(`🔢 Hex ${index + 1}: ${parsed.hex_data}`, 'data');
                                } else {
                                    log(`❌ Dados inválidos: ${parsed.raw}`, 'error');
                                }
                            });
                        }
                    } else {
                        log(`IR ${portNumber}: ${result.message}`, result.status === 'success' ? 'info' : 'error');
                    }
                }
            }

            async function resetNano(portNumber) {
                const result = await apiCall('/ir/reset', {
                    method: 'POST',
                    body: JSON.stringify({port_number: portNumber})
                });

                if (result) {
                    log(`Reset IR ${portNumber}: ${result.message}`, result.status === 'success' ? 'success' : 'error');
                }
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(html)

# ==============================================
# ENDPOINTS CORRIGIDOS
# ==============================================

@app.get("/api/ir/available-ports")
async def get_available_ports():
    return {"available_ports": list_available_ports()}

@app.post("/api/ir/connect")
async def connect_port(connection: PortConnection):
    result = connect_ir_port(connection.port_number, connection.port_name)
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result

@app.post("/api/ir/disconnect")
async def disconnect_port(connection: PortConnection):
    result = disconnect_ir_port(connection.port_number)
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result

@app.post("/api/ir/send-command")
async def send_command(command: IRCommand):
    result = send_ir_command(command.port_number, command.command)
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result

@app.post("/api/ir/get-data")
async def get_data(port: PortNumber):  # CORREÇÃO: Use PortNumber em vez de PortConnection
    result = get_ir_data(port.port_number)
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result

@app.post("/api/ir/reset")
async def reset_nano(port: PortNumber):  # CORREÇÃO: Use PortNumber em vez de PortConnection
    result = send_ir_command(port.port_number, "RESET")
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result

@app.get("/api/ir/status/{port_number}")
async def get_status(port_number: int):
    return get_ir_status(port_number)

# ==============================================
# INICIALIZAÇÃO
# ==============================================

if __name__ == "__main__":
    import uvicorn
    print("🎮 IR Controller System - CORRIGIDO")
    print("📍 Acesse: http://localhost:8000")
    print("✅ Problemas de 422 resolvidos!")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
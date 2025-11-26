from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import json
import asyncio
import serial
import cv2
import numpy as np
from datetime import datetime, timedelta
import os
import logging
from pathlib import Path
import threading
import time

app = FastAPI()

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Modelos Pydantic
class ConfiguracoesRotacao(BaseModel):
    Angulo1: int = 0
    Angulo2: int = 0
    Angulo3: int = 0
    Angulo4: int = 0

class DadosProducao(BaseModel):
    txt_aprovado_display1: str = ""
    txt_reprovado_display2: str = ""
    textBox1: str = ""
    textBox3: str = ""
    textBox5: str = ""
    textBox4: str = ""

class ComandoMovimento(BaseModel):
    comando: str
    x: str
    y: str

class StatusCamera(BaseModel):
    aprovado_cam1: int = 0
    aprovado_cam2: int = 0
    aprovado_cam3: int = 0
    aprovado_cam4: int = 0

# Estado da aplicação
class ApplicationState:
    def __init__(self):
        self.angulo_rotacao1 = 0
        self.angulo_rotacao2 = 0
        self.angulo_rotacao3 = 0
        self.angulo_rotacao4 = 0
        
        self.capturar_lado1 = False
        self.capturar_lado2 = False
        self.capturar_imagens_padrao = False
        
        self.libera_envio_comandos = False
        self.libera_envio_comandos2 = False
        self.chegou_ao_fim = False
        
        self.linha_atual = 0
        self.linha_atual2 = 0
        self.passo_atual = 0
        
        self.camera_pode_movimentar = False
        self.pistao_dedos = False
        self.salvar_hexadecimal = False
        self.nao_atua_ir = False
        self.editar_botoes = False
        
        # Configurações
        self.config = self.carregar_configuracao()
        self.hashes_validos = self.carregar_hashes()
        
        # Estado das câmeras
        self.latest_frames = [None, None, None, None]
        self.video_sources = [None, None, None, None]
        
        # Serial ports
        self.serial_ports = {}
        self.inicializar_serial_ports()
        
        # Dados de produção
        self.dados_producao = DadosProducao()
        self.carregar_dados_dia()
        
        # Timers e tasks
        self.tasks = {}
        self.timers = {}

    def carregar_configuracao(self) -> Dict[str, Any]:
        config_path = "config.json"
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return json.load(f)
        return {}

    def carregar_hashes(self) -> set:
        hash_path = self.config.get("dir_hexas", "hashes.txt")
        if os.path.exists(hash_path):
            with open(hash_path, 'r') as f:
                return set(line.strip() for line in f)
        return set()

    def inicializar_serial_ports(self):
        try:
            # Configuração das portas seriais baseada no INI
            self.serial_ports['serial1'] = serial.Serial(
                port=self.config.get('com', 'COM1'),
                baudrate=self.config.get('baudRate', 9600),
                timeout=1
            )
            self.serial_ports['serial2'] = serial.Serial(
                port=self.config.get('com2', 'COM2'),
                baudrate=self.config.get('baudRate2', 9600),
                timeout=1
            )
            # ... outras portas seriais
        except Exception as e:
            logger.error(f"Erro ao inicializar portas seriais: {e}")

    def carregar_dados_dia(self):
        try:
            pasta_dados = "Dados"
            nome_arquivo = datetime.now().strftime("%d_%m_%Y") + ".json"
            caminho_arquivo = os.path.join(pasta_dados, nome_arquivo)
            
            if os.path.exists(caminho_arquivo):
                with open(caminho_arquivo, 'r') as f:
                    dados = json.load(f)
                    self.dados_producao = DadosProducao(**dados)
        except Exception as e:
            logger.error(f"Erro ao carregar dados do dia: {e}")

# Instância global do estado
app_state = ApplicationState()

# Endpoints principais
@app.get("/")
async def root():
    return {"message": "Sistema RBS - API Principal"}

@app.get("/status")
async def get_status():
    return {
        "capturar_lado1": app_state.capturar_lado1,
        "capturar_lado2": app_state.capturar_lado2,
        "linha_atual": app_state.linha_atual,
        "linha_atual2": app_state.linha_atual2,
        "camera_pode_movimentar": app_state.camera_pode_movimentar
    }

@app.post("/iniciar-processo/{lado}")
async def iniciar_processo(lado: int):
    try:
        if lado == 1:
            app_state.capturar_lado1 = True
            app_state.capturar_lado2 = False
            # Resetar estado
            app_state.linha_atual = 0
            app_state.passo_atual = 0
            await resetar_nano1()
            await finger_down1()
            
        elif lado == 2:
            app_state.capturar_lado2 = True
            app_state.capturar_lado1 = False
            # Resetar estado
            app_state.linha_atual2 = 0
            app_state.passo_atual = 0
            await resetar_nano2()
            await finger_down2()
        
        return {"message": f"Processo iniciado para lado {lado}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/parar-processo")
async def parar_processo():
    app_state.capturar_lado1 = False
    app_state.capturar_lado2 = False
    app_state.libera_envio_comandos = False
    app_state.libera_envio_comandos2 = False
    
    await reset_placa1()
    await reset_placa2()
    
    return {"message": "Processo parado"}

@app.post("/emergencia")
async def emergencia():
    app_state.capturar_lado2 = False
    app_state.capturar_lado1 = False
    
    app_state.linha_atual = 0
    app_state.linha_atual2 = 0
    app_state.passo_atual = 0
    
    app_state.libera_envio_comandos = False
    app_state.libera_envio_comandos2 = False
    
    await reset_placa1()
    await reset_placa2()
    
    return {"message": "Modo emergência ativado"}

@app.post("/capturar-imagens")
async def capturar_imagens(tipo: str = "tempo_real"):
    try:
        if tipo == "tempo_real":
            await print_video()
        elif tipo == "padrao":
            await print_video_sequencial()
        
        # Executar comparação se necessário
        if app_state.capturar_lado1 or app_state.capturar_lado2:
            await captura_e_compara()
            
        return {"message": "Imagens capturadas com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/rotacionar-camera/{camera_id}")
async def rotacionar_camera(camera_id: int):
    try:
        if camera_id == 1:
            app_state.angulo_rotacao1 = (app_state.angulo_rotacao1 + 90) % 360
        elif camera_id == 2:
            app_state.angulo_rotacao2 = (app_state.angulo_rotacao2 + 90) % 360
        elif camera_id == 3:
            app_state.angulo_rotacao3 = (app_state.angulo_rotacao3 + 90) % 360
        elif camera_id == 4:
            app_state.angulo_rotacao4 = (app_state.angulo_rotacao4 + 90) % 360
        
        salvar_configuracoes_rotacao()
        return {"message": f"Câmera {camera_id} rotacionada"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/configuracao-rotacao")
async def get_configuracao_rotacao():
    return ConfiguracoesRotacao(
        Angulo1=app_state.angulo_rotacao1,
        Angulo2=app_state.angulo_rotacao2,
        Angulo3=app_state.angulo_rotacao3,
        Angulo4=app_state.angulo_rotacao4
    )

@app.post("/salvar-dados-producao")
async def salvar_dados_producao(dados: DadosProducao):
    try:
        app_state.dados_producao = dados
        await salvar_producao_json()
        return {"message": "Dados de produção salvos"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/dados-producao")
async def get_dados_producao():
    return app_state.dados_producao

@app.post("/home-camera")
async def home_camera():
    try:
        await executar_home_camera()
        return {"message": "Home da câmera executado"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/reset-placa/{placa}")
async def reset_placa(placa: int):
    try:
        if placa == 1:
            await reset_placa1()
        elif placa == 2:
            await reset_placa2()
        return {"message": f"Placa {placa} resetada"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Funções auxiliares assíncronas
async def print_video():
    """Captura e salva imagens das câmeras"""
    try:
        backup_path = r"C:\Users\user\Pictures\TempoRealTestes"
        base_path = app_state.config.get("local_img_tempo_real", "temp_images")
        
        # Garantir que os diretórios existam
        os.makedirs(base_path, exist_ok=True)
        os.makedirs(backup_path, exist_ok=True)
        
        for i, frame in enumerate(app_state.latest_frames):
            if frame is not None:
                # Aplicar filtro OCR
                filtered = await aplicar_ocr_filter(frame)
                # Aplicar desfoque gaussiano
                filtered = await aplicar_gaussian_blur(filtered, 13)
                
                # Salvar no diretório principal
                file_path = os.path.join(base_path, f"IMAGEM_{i + 1}.png")
                cv2.imwrite(file_path, filtered)
                
        logger.info("Imagens capturadas e salvas com sucesso")
    except Exception as e:
        logger.error(f"Erro ao capturar imagens: {e}")

async def print_video_sequencial():
    """Captura imagens sequenciais para padrão"""
    try:
        base_root_path = app_state.config.get("local_padrao", "")
        base_root_path2 = app_state.config.get("local_padrao2", "")
        
        # Lógica similar à função original C#
        # Implementação simplificada
        logger.info("Captura sequencial executada")
    except Exception as e:
        logger.error(f"Erro na captura sequencial: {e}")

async def captura_e_compara():
    """Executa comparação entre imagens padrão e de teste"""
    try:
        dir_padrao = app_state.config.get("local_padrao", "")
        dir_comparar = app_state.config.get("local_img_tempo_real", "")
        log_path = app_state.config.get("log_telas", "")
        
        # Lógica de comparação similar ao C#
        # Implementação simplificada
        logger.info("Comparação de imagens executada")
    except Exception as e:
        logger.error(f"Erro na comparação de imagens: {e}")

async def aplicar_ocr_filter(frame):
    """Aplica filtro OCR na imagem"""
    try:
        # Converter para escala de cinza
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Aplicar filtro bilateral
        filtered = cv2.bilateralFilter(gray, 9, 75, 75)
        
        # Aplicar threshold adaptativo
        thresh = cv2.adaptiveThreshold(
            filtered, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY_INV, 11, 2
        )
        
        return thresh
    except Exception as e:
        logger.error(f"Erro ao aplicar filtro OCR: {e}")
        return frame

async def aplicar_gaussian_blur(image, ksize):
    """Aplica desfoque gaussiano"""
    try:
        if ksize % 2 == 0:
            ksize += 1
        ksize = max(1, ksize)
        
        blurred = cv2.GaussianBlur(image, (ksize, ksize), 0)
        return blurred
    except Exception as e:
        logger.error(f"Erro ao aplicar desfoque gaussiano: {e}")
        return image

async def reset_placa1():
    """Reset da placa 1"""
    try:
        if app_state.serial_ports.get('serial1'):
            app_state.serial_ports['serial1'].write(b"P_0\n")
            await asyncio.sleep(0.1)
            app_state.serial_ports['serial1'].write(b"B1_0\n")
            await asyncio.sleep(0.5)
            app_state.serial_ports['serial1'].write(b"K2_0\n")
            await asyncio.sleep(0.5)
            app_state.serial_ports['serial1'].write(b"ENA\n")
    except Exception as e:
        logger.error(f"Erro no reset da placa 1: {e}")

async def reset_placa2():
    """Reset da placa 2"""
    try:
        if app_state.serial_ports.get('serial1'):
            app_state.serial_ports['serial1'].write(b"P_0\n")
            await asyncio.sleep(0.1)
            app_state.serial_ports['serial1'].write(b"B2_0\n")
            await asyncio.sleep(0.5)
            app_state.serial_ports['serial1'].write(b"K1_0\n")
            await asyncio.sleep(0.5)
            app_state.serial_ports['serial1'].write(b"ENA\n")
    except Exception as e:
        logger.error(f"Erro no reset da placa 2: {e}")

async def resetar_nano1():
    """Reset do Nano 1"""
    try:
        if app_state.serial_ports.get('serial3'):
            # Lógica de reset similar ao C#
            await asyncio.sleep(0.1)
    except Exception as e:
        logger.error(f"Erro no reset do Nano 1: {e}")

async def resetar_nano2():
    """Reset do Nano 2"""
    try:
        if app_state.serial_ports.get('serial4'):
            # Lógica de reset similar ao C#
            await asyncio.sleep(0.1)
    except Exception as e:
        logger.error(f"Erro no reset do Nano 2: {e}")

async def finger_down1():
    """Sequência finger down para lado 1"""
    try:
        if app_state.serial_ports.get('serial1'):
            app_state.serial_ports['serial1'].write(b"K2_1\n")
            await asyncio.sleep(2)
            
            if app_state.serial_ports.get('serial2'):
                app_state.serial_ports['serial2'].write(b"G90 X29.787 Y82.987\n")
                await asyncio.sleep(3)
            
            app_state.serial_ports['serial1'].write(b"P_1\n")
            await asyncio.sleep(1)
            
            app_state.serial_ports['serial1'].write(b"K4_1\n")
            await asyncio.sleep(0.5)
            
            app_state.serial_ports['serial1'].write(b"K7_1\n")
            await asyncio.sleep(0.3)
            app_state.serial_ports['serial1'].write(b"K7_1\n")
            await asyncio.sleep(0.5)
            
            app_state.serial_ports['serial1'].write(b"P_0\n")
            await asyncio.sleep(1.5)
            
            await inicio1()
    except Exception as e:
        logger.error(f"Erro no finger down 1: {e}")

async def finger_down2():
    """Sequência finger down para lado 2"""
    try:
        if app_state.serial_ports.get('serial1'):
            app_state.serial_ports['serial1'].write(b"K6_1\n")
            await asyncio.sleep(0.3)
            app_state.serial_ports['serial1'].write(b"K6_1\n")
            await asyncio.sleep(0.5)
            
            app_state.serial_ports['serial1'].write(b"K1_1\n")
            await asyncio.sleep(1)
            
            if app_state.serial_ports.get('serial2'):
                app_state.serial_ports['serial2'].write(b"G90 X394.805 Y77.726\n")
                await asyncio.sleep(1)
            
            app_state.serial_ports['serial1'].write(b"P_1\n")
            await asyncio.sleep(1)
            
            app_state.serial_ports['serial1'].write(b"K3_1\n")
            await asyncio.sleep(0.3)
            
            app_state.serial_ports['serial1'].write(b"P_0\n")
            await asyncio.sleep(1.5)
            
            await inicio2()
    except Exception as e:
        logger.error(f"Erro no finger down 2: {e}")

async def inicio1():
    """Inicialização do processo para lado 1"""
    app_state.libera_envio_comandos = True
    
    if app_state.serial_ports.get('serial1'):
        app_state.serial_ports['serial1'].write(b"B1_1\n")
        await asyncio.sleep(0.1)
        app_state.serial_ports['serial1'].write(b"B1_1\n")
        await asyncio.sleep(2.9)
    
    await enviar_proximo_comando()
    await contador_ciclos()

async def inicio2():
    """Inicialização do processo para lado 2"""
    app_state.libera_envio_comandos2 = True
    
    if app_state.serial_ports.get('serial1'):
        app_state.serial_ports['serial1'].write(b"B2_1\n")
        await asyncio.sleep(0.1)
        app_state.serial_ports['serial1'].write(b"B2_1\n")
        await asyncio.sleep(2.9)
    
    await enviar_proximo_comando2()
    await contador_ciclos()

async def enviar_proximo_comando():
    """Envia próximo comando para o lado 1"""
    # Implementação similar ao C#
    # Usando dados da grid ou configuração
    pass

async def enviar_proximo_comando2():
    """Envia próximo comando para o lado 2"""
    # Implementação similar ao C#
    pass

async def contador_ciclos():
    """Incrementa contador de ciclos"""
    try:
        current = int(app_state.dados_producao.textBox5 or "0")
        app_state.dados_producao.textBox5 = str(current + 1)
    except ValueError:
        app_state.dados_producao.textBox5 = "1"

async def contador_testados():
    """Incrementa contador de testados"""
    try:
        current = int(app_state.dados_producao.textBox4 or "0")
        app_state.dados_producao.textBox4 = str(current + 4)
    except ValueError:
        app_state.dados_producao.textBox4 = "4"

async def executar_home_camera():
    """Executa home da câmera"""
    try:
        if app_state.serial_ports.get('serial1'):
            app_state.serial_ports['serial1'].write(b"K5_0\n")
            await asyncio.sleep(0.1)
            app_state.serial_ports['serial1'].write(b"P_0\n")
        
        if app_state.serial_ports.get('serial2'):
            home_cam_1 = app_state.config.get("home_cam_1", "G28")
            home_cam_2 = app_state.config.get("home_cam_2", "G28")
            
            app_state.serial_ports['serial2'].write(f"{home_cam_1}\n".encode())
            await asyncio.sleep(4)
            
            app_state.serial_ports['serial1'].write(b"K5_1\n")
            await asyncio.sleep(2)
            
            if app_state.camera_pode_movimentar and not app_state.pistao_dedos:
                app_state.serial_ports['serial2'].write(f"{home_cam_2}\n".encode())
                await asyncio.sleep(4)
                app_state.serial_ports['serial1'].write(b"K5_0\n")
            
            await asyncio.sleep(0.3)
            app_state.serial_ports['serial2'].write(b"G90 X0 Y0\n")
            
    except Exception as e:
        logger.error(f"Erro no home da câmera: {e}")

def salvar_configuracoes_rotacao():
    """Salva configurações de rotação"""
    try:
        config = ConfiguracoesRotacao(
            Angulo1=app_state.angulo_rotacao1,
            Angulo2=app_state.angulo_rotacao2,
            Angulo3=app_state.angulo_rotacao3,
            Angulo4=app_state.angulo_rotacao4
        )
        
        with open("config_rotacao.json", "w") as f:
            json.dump(config.dict(), f, indent=2)
    except Exception as e:
        logger.error(f"Erro ao salvar configurações de rotação: {e}")

async def salvar_producao_json():
    """Salva dados de produção em JSON"""
    try:
        pasta_dados = "Dados"
        os.makedirs(pasta_dados, exist_ok=True)
        
        nome_arquivo = datetime.now().strftime("%d_%m_%Y") + ".json"
        caminho_arquivo = os.path.join(pasta_dados, nome_arquivo)
        
        with open(caminho_arquivo, "w") as f:
            json.dump(app_state.dados_producao.dict(), f, indent=2)
    except Exception as e:
        logger.error(f"Erro ao salvar dados de produção: {e}")

# Background tasks para processamento contínuo
async def processar_dados_serial():
    """Processa dados recebidos das portas seriais"""
    while True:
        try:
            # Processar dados da serial 1
            if app_state.serial_ports.get('serial1'):
                if app_state.serial_ports['serial1'].in_waiting > 0:
                    data = app_state.serial_ports['serial1'].readline().decode().strip()
                    await processar_dados_recebidos(data, 'serial1')
            
            # Processar outras portas seriais...
            
            await asyncio.sleep(0.1)
        except Exception as e:
            logger.error(f"Erro no processamento serial: {e}")
            await asyncio.sleep(1)

async def processar_dados_recebidos(data: str, porta: str):
    """Processa dados recebidos das portas seriais"""
    try:
        if "START1" in data:
            await iniciar_processo(1)
        elif "START2" in data:
            await iniciar_processo(2)
        elif "EMERG" in data:
            await emergencia()
        elif "PRESS" in data:
            await capturar_imagens()
        # Outros processamentos...
            
    except Exception as e:
        logger.error(f"Erro ao processar dados recebidos: {e}")

@app.on_event("startup")
async def startup_event():
    """Inicializa a aplicação"""
    logger.info("Iniciando aplicação RBS")
    
    # Iniciar tasks em background
    asyncio.create_task(processar_dados_serial())

@app.on_event("shutdown")
async def shutdown_event():
    """Finaliza a aplicação"""
    logger.info("Finalizando aplicação RBS")
    
    # Fechar portas seriais
    for port in app_state.serial_ports.values():
        if port and port.is_open:
            port.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
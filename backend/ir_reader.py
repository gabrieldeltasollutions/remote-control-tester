import aiohttp
import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IRReader:
    """Classe simplificada apenas para LEITURA de dados IR do servidor Node.js"""
    
    def __init__(self, base_url: str = "http://localhost:3001"):
        self.base_url = base_url
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15))
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def check_nodejs_status(self) -> bool:
        """Verifica se o servidor Node.js está rodando"""
        try:
            async with self.session.get(f"{self.base_url}/status") as response:
                return response.status == 200
        except:
            return False
    
    async def get_nano_status(self) -> Dict[str, Any]:
        """Obtém status dos Nanos - apenas para verificação"""
        try:
            async with self.session.get(f"{self.base_url}/status") as response:
                if response.status == 200:
                    return await response.json()
                return {"success": False, "error": f"HTTP {response.status}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def capture_ir_data(self, nano: str = 'nano1', timeout: int = 10000) -> Dict[str, Any]:
        """
        CAPTURA dados IR do Nano (APENAS LEITURA)
        
        Args:
            nano: 'nano1' ou 'nano2'
            timeout: timeout em ms
            
        Returns:
            Dict com dados IR capturados
        """
        try:
            logger.info(f"📡 Solicitando captura IR do {nano}...")
            
            payload = {
                "timeout": timeout,
                "trigger_source": "PYTHON_MAIN_READER"
            }
            
            async with self.session.post(
                f"{self.base_url}/get-nano/{nano}", 
                json=payload
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"✅ Dados IR capturados do {nano}")
                    return result
                    
                elif response.status == 408:
                    return {"success": False, "error": f"Timeout - {nano} não respondeu"}
                    
                elif response.status == 503:
                    return {"success": False, "error": f"{nano} não está conectado"}
                    
                else:
                    error_text = await response.text()
                    return {"success": False, "error": f"HTTP {response.status}: {error_text}"}
                    
        except asyncio.TimeoutError:
            return {"success": False, "error": "Timeout na conexão com Node.js"}
        except Exception as e:
            return {"success": False, "error": f"Erro na captura: {str(e)}"}
    
    async def save_ir_capture(self, data: Dict[str, Any], prefix: str = "ir_capture") -> str:
        """
        Salva os dados IR capturados em arquivo
        """
        try:
            # Diretório para capturas
            capture_dir = Path("ir_captures")
            capture_dir.mkdir(exist_ok=True)
            
            # Nome do arquivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{prefix}_{timestamp}.json"
            filepath = capture_dir / filename
            
            # Estrutura dos dados
            save_data = {
                "metadata": {
                    "captured_at": datetime.now().isoformat(),
                    "source": "python_ir_reader",
                    "filename": filename
                },
                "ir_data": data
            }
            
            # Salva arquivo
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"💾 Captura salva: {filename}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar captura: {e}")
            return ""

# Instância global
ir_reader = IRReader()
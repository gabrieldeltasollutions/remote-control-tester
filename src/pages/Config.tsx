import { useState, useEffect } from 'react';
import { RBSButton, RBSTextBox, RBSGroupBox, RBSSelect, RBSCircularBtn } from '@/components/RBSUi';
import { Image as ImageIcon, ArrowUp, ArrowDown, ArrowLeft, ArrowRight, Camera, Video, Crop, Save, Upload } from 'lucide-react';
import { sendCommand, getSerialPorts, connectPort, disconnectPort } from '@/services/api';

// Componente de Grid Personalizado para o Fundo Azul Escuro
const DarkBlueGrid = () => (
  <div className="border border-[#014E7F] bg-[#003366] text-xs h-full overflow-hidden flex flex-col">
    {/* Cabeçalho Branco/Cinza */}
    <div className="bg-[#F0F0F0] text-black font-bold grid grid-cols-4 p-1 text-center border-b border-slate-400">
      <span className="border-r border-slate-300 col-span-1">G90</span>
      <span className="border-r border-slate-300 col-span-1">X</span>
      <span className="col-span-2">Y</span>
    </div>
    {/* Corpo Azul Escuro */}
    <div className="overflow-y-auto flex-1 bg-[#004080]">
      {/* Linhas vazias para simular o grid */}
      {[...Array(6)].map((_, i) => (
        <div key={i} className="border-b border-[#005599] h-6"></div>
      ))}
    </div>
  </div>
);

const Config = () => {
  const [tabLeft, setTabLeft] = useState<'Serial' | 'Controle'>('Controle');
  const [tabRight, setTabRight] = useState<'Serial' | 'Cameras'>('Cameras');
  const [tabBottom, setTabBottom] = useState<'Padrao' | 'Comparar' | 'Testar'>('Padrao');

  // Estados para controle dos atuadores (toggle)
  const [actuatorState, setActuatorState] = useState({
    P: false,      // Pressor Finger
    K5: false,     // Pistão Câmera
    K15: false,    // LED
    B1: false,     // Alimentação B1
    B2: false,     // Alimentação B2
    K2: false,     // Move Berço 1
    K7: false,     // Pilha 1
    K4: false,     // Trava Berço 1
    K1: false,     // Move Berço 2
    K6: false,     // Pilha 2
    K3: false,     // Trava Berço 2
  });

  // Estado para tamanho do passo do movimento
  const [stepSize, setStepSize] = useState(10);

  // Estados para comunicação serial (IR)
  const [serialLogs, setSerialLogs] = useState({
    port1: '',
    port2: '',
    port3: '',
  });

  // Estados de conectividade das portas seriais
  const [portConnections, setPortConnections] = useState({
    port1: false,
    port2: false,
    port3: false,
    port4: false,
  });

  // Estados para portas seriais disponíveis
  const [availablePorts, setAvailablePorts] = useState([]);
  const [selectedPorts, setSelectedPorts] = useState({
    port1: '',
    port2: '',
    port3: '',
    port4: '',
  });
  const [isLoadingPorts, setIsLoadingPorts] = useState(false);

  // Dados IR recebidos
  const [irData, setIrData] = useState('');

  // Estados para inputs de comando serial
  const [serialInputs, setSerialInputs] = useState({
    port1: '',
    port2: '',
    port3: '',
  });

  // Função para carregar portas seriais disponíveis
  const loadSerialPorts = async () => {
    setIsLoadingPorts(true);
    try {
      const response = await getSerialPorts();
      // Filtrar apenas portas USB/ACM e algumas seriais principais
      const filteredPorts = (response.ports || []).filter(port => 
        port.device.includes('USB') || 
        port.device.includes('ACM') || 
        port.device.match(/ttyS[0-9]$/) // apenas ttyS0-ttyS9
      );
      setAvailablePorts(filteredPorts);
      console.log(`Encontradas ${filteredPorts.length} portas seriais relevantes:`, filteredPorts);
    } catch (error) {
      console.error('Erro ao carregar portas seriais:', error);
      setAvailablePorts([]);
    } finally {
      setIsLoadingPorts(false);
    }
  };

  // Função para conectar uma porta
  const handleConnectPort = async (portNumber) => {
    const selectedPort = selectedPorts[`port${portNumber}`];
    
    if (!selectedPort) {
      alert('Por favor, selecione uma porta serial');
      return;
    }

    try {
      const response = await connectPort(portNumber, selectedPort);
      
      if (response.status === 'success') {
        setPortConnections(prev => ({
          ...prev,
          [`port${portNumber}`]: true
        }));
        
        // Se for porta IR (3 ou 4), executar reset automático
        if (portNumber === 3 || portNumber === 4) {
          console.log(`🔄 Executando reset automático na porta IR ${portNumber}...`);
          await resetArduinoNano(portNumber);
        }
        
        console.log(`Porta ${portNumber} conectada: ${selectedPort}`);
      }
    } catch (error) {
      console.error(`Erro ao conectar porta ${portNumber}:`, error);
      alert(`Erro ao conectar porta ${portNumber}: ${error.message}`);
    }
  };

  // Função para reset do Arduino Nano (portas IR)
  const resetArduinoNano = async (portNumber) => {
    try {
      console.log(`🔄 Resetando Arduino Nano na porta ${portNumber}...`);
      
      // Enviar comando de reset via backend
      const response = await sendCommand(portNumber, 'RESET');
      
      if (response.status === 'success') {
        console.log(`✅ Reset executado na porta ${portNumber}`);
        
        // Aguardar estabilização
        await new Promise(resolve => setTimeout(resolve, 500));
        
        // Enviar comando GET automático após reset
        await sendIRGetCommand(portNumber);
      } else {
        console.log(`⚠️ Reset manual necessário na porta ${portNumber}`);
      }
    } catch (error) {
      console.error(`❌ Erro no reset da porta ${portNumber}:`, error);
    }
  };

  // Função para enviar comando GET para IR
  const sendIRGetCommand = async (portNumber) => {
    try {
      const response = await sendCommand(portNumber, 'GET');
      
      if (response.status === 'success') {
        console.log(`→ GET enviado para porta IR ${portNumber}`);
        addToSerialLog(`port${portNumber}`, `TX: GET`);
      } else {
        console.error(`Erro ao enviar GET para porta ${portNumber}:`, response.message);
      }
    } catch (error) {
      console.error(`Erro na comunicação GET porta ${portNumber}:`, error);
    }
  };

  // Função para desconectar uma porta
  const handleDisconnectPort = async (portNumber) => {
    try {
      const response = await disconnectPort(portNumber);
      
      if (response.status === 'success') {
        setPortConnections(prev => ({
          ...prev,
          [`port${portNumber}`]: false
        }));
        console.log(`Porta ${portNumber} desconectada`);
      }
    } catch (error) {
      console.error(`Erro ao desconectar porta ${portNumber}:`, error);
      alert(`Erro ao desconectar porta ${portNumber}: ${error.message}`);
    }
  };

  // Carregar portas ao montar o componente
  useEffect(() => {
    loadSerialPorts();
  }, []);

  // Função auxiliar para filtrar dados IR
  const filterIRData = (data) => {
    return data.includes(';') || data.includes('FF') || data.includes('X') || data.includes('-');
  };

  // Função para toggle de atuadores (Porta 1)
  const toggleActuator = async (actuatorKey) => {
    try {
      const currentState = actuatorState[actuatorKey];
      const newState = !currentState;
      const command = `${actuatorKey}_${newState ? '1' : '0'}`;
      
      const response = await sendCommand(1, command);
      
      if (response.status === 'success') {
        setActuatorState(prev => ({
          ...prev,
          [actuatorKey]: newState
        }));
        console.log(`${actuatorKey} ${newState ? 'LIGADO' : 'DESLIGADO'}`);
      } else {
        console.error('Erro ao enviar comando:', response.message);
      }
    } catch (error) {
      console.error('Erro na comunicação com API:', error);
    }
  };

  // Função para comandos GRBL (Porta 2)
  const sendGRBLCommand = async (command) => {
    try {
      const response = await sendCommand(2, command);
      
      if (response.status === 'success') {
        console.log(`Comando GRBL enviado: ${command}`);
        addToSerialLog('port2', `TX: ${command}`);
      } else {
        console.error('Erro ao enviar comando GRBL:', response.message);
      }
    } catch (error) {
      console.error('Erro na comunicação GRBL:', error);
    }
  };

  // Função para movimento relativo
  const sendMovementCommand = async (direction) => {
    let command = '';
    
    switch (direction) {
      case 'X+':
        command = `G91 X${stepSize}\nG90`;
        break;
      case 'X-':
        command = `G91 X-${stepSize}\nG90`;
        break;
      case 'Y+':
        command = `G91 Y${stepSize}\nG90`;
        break;
      case 'Y-':
        command = `G91 Y-${stepSize}\nG90`;
        break;
      default:
        return;
    }
    
    await sendGRBLCommand(command);
  };

  // Função para comandos IR (Porta 3 e 4) - Atualizada
  const sendIRCommand = async (portNumber, command = 'GET') => {
    try {
      const response = await sendCommand(portNumber, command);
      
      if (response.status === 'success') {
        console.log(`Comando IR enviado para porta ${portNumber}:`, command);
        addToSerialLog(`port${portNumber}`, `TX: ${command}`);
      } else {
        console.error(`Erro ao enviar comando IR para porta ${portNumber}:`, response.message);
      }
    } catch (error) {
      console.error(`Erro na comunicação IR porta ${portNumber}:`, error);
    }
  };

  // Função para adicionar entrada no log serial
  const addToSerialLog = (port, message) => {
    const timestamp = new Date().toLocaleTimeString();
    const logEntry = `[${timestamp}] ${message}\n`;
    
    setSerialLogs(prev => ({
      ...prev,
      [port]: prev[port] + logEntry
    }));
  };

  // Função para enviar comando manual por porta
  const sendManualCommand = async (portNumber) => {
    const command = serialInputs[`port${portNumber}`];
    if (!command.trim()) return;

    try {
      const response = await sendCommand(portNumber, command);
      
      if (response.status === 'success') {
        addToSerialLog(`port${portNumber}`, `TX: ${command}`);
        // Limpar input após envio bem-sucedido
        setSerialInputs(prev => ({
          ...prev,
          [`port${portNumber}`]: ''
        }));
      } else {
        console.error('Erro ao enviar comando:', response.message);
      }
    } catch (error) {
      console.error('Erro na comunicação:', error);
    }
  };

  // Função para limpar log de porta específica
  const clearSerialLog = (port) => {
    setSerialLogs(prev => ({
      ...prev,
      [port]: ''
    }));
  };

  return (
    <div className="p-2 h-full w-full bg-[#F8F9FA] font-sans text-xs overflow-hidden flex gap-2">
      
      {/* ===================================================================================== */}
      {/* COLUNA ESQUERDA (Com scroll vertical se necessário) */}
      {/* ===================================================================================== */}
      <div className="w-[45%] flex flex-col gap-2 h-full overflow-y-auto pr-1">
        
        {/* --- PARTE SUPERIOR (ABAS) --- */}
        <div className="flex-none flex flex-col">
            <div className="flex">
                {['Serial', 'Controle'].map(t => (
                <button
                    key={t}
                    onClick={() => setTabLeft(t as any)}
                    className={`px-6 py-1 text-xs rounded-t-sm border border-b-0 ${tabLeft === t ? 'bg-white font-bold text-black z-10 -mb-[1px] border-slate-400' : 'bg-[#E1E1E1] text-slate-600 border-slate-300'}`}
                >
                    {t}
                </button>
                ))}
                <div className="flex-1 border-b border-slate-400"></div>
            </div>

            {/* CONTEÚDO DA ABA */}
            <div className="bg-white border border-slate-400 p-3 border-t-0">
                
                {/* ABA SERIAL */}
                {tabLeft === 'Serial' && (
                <div className="flex flex-col gap-2 h-[350px]">
                    <div className="grid grid-cols-4 gap-2">
                    {[1, 2, 3, 4].map(num => (
                        <div key={num} className="flex flex-col gap-1">
                        <div className="flex items-center justify-between">
                            <label className="font-bold text-[#014E7F]">Porta {num}:</label>
                            <RBSSelect 
                                value={selectedPorts[`port${num}`]}
                                onChange={(e) => setSelectedPorts(prev => ({
                                    ...prev,
                                    [`port${num}`]: e.target.value
                                }))}
                                disabled={portConnections[`port${num}`]}
                            >
                                <option value="">Selecione...</option>
                                {availablePorts.map((port, index) => (
                                    <option key={index} value={port.device}>
                                        {port.device}
                                    </option>
                                ))}
                            </RBSSelect>
                        </div>
                        <div className="flex items-center justify-between">
                            <label className="font-bold text-[#014E7F]">Taxa:</label>
                            <RBSSelect>
                                <option>{(num === 3 || num === 4) ? '9600' : '115200'}</option>
                            </RBSSelect>
                        </div>
                        <RBSButton 
                            className="h-6 text-[10px]" 
                            variant={portConnections[`port${num}`] ? "red" : "blue"}
                            onClick={() => portConnections[`port${num}`] 
                                ? handleDisconnectPort(num) 
                                : handleConnectPort(num)
                            }
                            disabled={!portConnections[`port${num}`] && !selectedPorts[`port${num}`]}
                        >
                            {portConnections[`port${num}`] ? 'Desconectar' : 'Conectar'}
                        </RBSButton>
                        </div>
                    ))}
                    </div>
                    <div className="flex-1 bg-black border-2 border-slate-500 p-1 font-mono text-green-500 text-[10px] overflow-y-auto">
                        {availablePorts.length > 0 
                            ? availablePorts.map((port, i) => 
                                `${port.device} - ${port.description}\n`
                              ).join('')
                            : isLoadingPorts 
                                ? 'Buscando portas...\n' 
                                : 'Nenhuma porta encontrada. Clique em "Atualizar Lista".\n'
                        }
                    </div>
                    <div className="flex gap-2">
                        <RBSButton 
                            className="flex-1"
                            onClick={loadSerialPorts}
                            disabled={isLoadingPorts}
                        >
                            {isLoadingPorts ? 'Carregando...' : 'Atualizar Lista'}
                        </RBSButton>
                        <RBSButton className="flex-1">Salvar Porta/Taxa</RBSButton>
                    </div>
                </div>
                )}

                {/* ABA CONTROLE (LAYOUT FIEL AO PRINT) */}
                {tabLeft === 'Controle' && (
                <div className="flex gap-4 h-[350px]">
                    
                    {/* Coluna Botões Azuis (Esquerda) */}
                    <div className="w-1/3 flex flex-col gap-3">
                        {/* Bloco Home */}
                        <div className="bg-[#BFCDDB] p-2 rounded-xl flex gap-2 h-28 items-stretch shadow-sm border border-slate-300">
                            <RBSButton 
                                className="flex-1 h-full text-xs whitespace-normal leading-4" 
                                rounded="xl"
                                onClick={() => sendGRBLCommand('$H')}
                            >
                                Home - Todos os Eixos
                            </RBSButton>
                            <RBSButton 
                                className="w-16 h-full text-xs whitespace-normal leading-4" 
                                rounded="xl"
                                onClick={() => sendGRBLCommand('$X')}
                            >
                                Libera Home
                            </RBSButton>
                        </div>

                        {/* Bloco Ações */}
                        <div className="bg-[#BFCDDB] p-2 rounded-xl flex flex-col gap-2 shadow-sm border border-slate-300">
                            <div className="grid grid-cols-3 gap-2">
                                <RBSButton 
                                    className="h-12 text-[10px] whitespace-normal leading-3" 
                                    rounded="xl"
                                    variant={actuatorState.P ? "green" : "blue"}
                                    onClick={() => toggleActuator('P')}
                                >
                                    Pressor Finger
                                </RBSButton>
                                <RBSButton 
                                    className="h-12 text-[10px] whitespace-normal leading-3" 
                                    rounded="xl"
                                    variant={actuatorState.K5 ? "green" : "blue"}
                                    onClick={() => toggleActuator('K5')}
                                >
                                    Pistão Camera
                                </RBSButton>
                                <RBSButton 
                                    variant={actuatorState.K15 ? "green" : "darkBlue"} 
                                    className="h-12 text-[10px] whitespace-normal leading-3" 
                                    rounded="xl"
                                    onClick={() => toggleActuator('K15')}
                                >
                                    {actuatorState.K15 ? 'Led On' : 'Led Off'}
                                </RBSButton>
                            </div>
                            <div className="grid grid-cols-2 gap-2">
                                <RBSButton 
                                    variant={actuatorState.B1 ? "green" : "darkBlue"} 
                                    className="h-8 text-[10px]" 
                                    rounded="xl"
                                    onClick={() => toggleActuator('B1')}
                                >
                                    Alimentação B1
                                </RBSButton>
                                <RBSButton 
                                    variant={actuatorState.B2 ? "green" : "darkBlue"} 
                                    className="h-8 text-[10px]" 
                                    rounded="xl"
                                    onClick={() => toggleActuator('B2')}
                                >
                                    Alimentação B2
                                </RBSButton>
                            </div>
                        </div>

                        {/* Bloco Passos */}
                        <div className="bg-[#BFCDDB] p-3 rounded-xl shadow-sm border border-slate-300">
                            <label className="text-[11px] font-bold text-[#014E7F] block mb-1">QTD. Passos</label>
                            <input 
                                className="w-full h-10 rounded-lg border border-[#014E7F] px-2 text-lg font-bold" 
                                type="number"
                                value={stepSize}
                                onChange={(e) => setStepSize(Number(e.target.value))}
                            />
                        </div>
                    </div>

                    {/* Painel Movimentação (Direita) */}
                    <div className="flex-1 bg-[#E8E8E8] rounded-xl p-2 relative flex flex-col">
                        
                        {/* Topo: Botões Berço */}
                        <div className="flex justify-between px-2 mt-2 z-10 relative">
                            <div className="flex flex-col gap-2">
                                <RBSButton 
                                    className="w-20 h-10 text-[10px] whitespace-normal leading-3" 
                                    rounded="xl"
                                    variant={actuatorState.K2 ? "green" : "blue"}
                                    onClick={() => toggleActuator('K2')}
                                >
                                    Move Berço 1
                                </RBSButton>
                                <RBSButton 
                                    className="w-20 h-10 text-[10px]" 
                                    rounded="xl"
                                    variant={actuatorState.K7 ? "green" : "blue"}
                                    onClick={() => toggleActuator('K7')}
                                >
                                    Pilha 1
                                </RBSButton>
                                <RBSButton 
                                    className="w-20 h-10 text-[10px] whitespace-normal leading-3" 
                                    rounded="xl"
                                    variant={actuatorState.K4 ? "green" : "blue"}
                                    onClick={() => toggleActuator('K4')}
                                >
                                    Trava Berço 1
                                </RBSButton>
                            </div>
                            <div className="flex flex-col gap-2">
                                <RBSButton 
                                    className="w-20 h-10 text-[10px] whitespace-normal leading-3" 
                                    rounded="xl"
                                    variant={actuatorState.K1 ? "green" : "blue"}
                                    onClick={() => toggleActuator('K1')}
                                >
                                    Move Berço 2
                                </RBSButton>
                                <RBSButton 
                                    className="w-20 h-10 text-[10px]" 
                                    rounded="xl"
                                    variant={actuatorState.K6 ? "green" : "blue"}
                                    onClick={() => toggleActuator('K6')}
                                >
                                    Pilha 2
                                </RBSButton>
                                <RBSButton 
                                    className="w-20 h-10 text-[10px] whitespace-normal leading-3" 
                                    rounded="xl"
                                    variant={actuatorState.K3 ? "green" : "blue"}
                                    onClick={() => toggleActuator('K3')}
                                >
                                    Trava Berço 2
                                </RBSButton>
                            </div>
                        </div>

                        {/* Centro: Direcional */}
                        <div className="absolute top-[38%] left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-0">
                            <div className="grid grid-cols-3 grid-rows-3 gap-2 place-items-center">
                                {/* Labels */}
                                <span className="col-start-2 row-start-1 text-[#014E7F] font-bold -ml-8 text-[10px]">Y +</span>
                                <span className="col-start-3 row-start-2 text-[#014E7F] font-bold -mt-8 text-[10px]">X +</span>
                                <span className="col-start-1 row-start-2 text-[#014E7F] font-bold -mt-8 text-[10px]">X -</span>
                                <span className="col-start-2 row-start-3 text-[#014E7F] font-bold -mr-8 text-[10px]">Y -</span>

                                {/* Botões Verdes */}
                                <div className="col-start-2 row-start-1">
                                    <RBSCircularBtn 
                                        variant="green" 
                                        size="w-10 h-10" 
                                        icon={<ArrowUp size={20} strokeWidth={3} />} 
                                        onClick={() => sendMovementCommand('Y+')}
                                    />
                                </div>
                                <div className="col-start-1 row-start-2">
                                    <RBSCircularBtn 
                                        variant="green" 
                                        size="w-10 h-10" 
                                        icon={<ArrowLeft size={20} strokeWidth={3} />} 
                                        onClick={() => sendMovementCommand('X-')}
                                    />
                                </div>
                                <div className="col-start-3 row-start-2">
                                    <RBSCircularBtn 
                                        variant="green" 
                                        size="w-10 h-10" 
                                        icon={<ArrowRight size={20} strokeWidth={3} />} 
                                        onClick={() => sendMovementCommand('X+')}
                                    />
                                </div>
                                <div className="col-start-2 row-start-3">
                                    <RBSCircularBtn 
                                        variant="green" 
                                        size="w-10 h-10" 
                                        icon={<ArrowDown size={20} strokeWidth={3} />} 
                                        onClick={() => sendMovementCommand('Y-')}
                                    />
                                </div>
                            </div>
                        </div>

                        {/* Base: Displays X/Y */}
                        <div className="mt-auto flex flex-col gap-2 px-4 mb-2">
                            <div className="bg-[#014E7F] h-8 rounded-full flex items-center justify-between px-8 relative shadow-md border-2 border-white">
                                <span className="text-white font-bold text-lg">X {'->'}</span>
                                <span className="text-[#FFFF00] font-bold text-xl">0</span>
                            </div>
                            <div className="bg-[#014E7F] h-8 rounded-full flex items-center justify-between px-8 relative shadow-md border-2 border-white">
                                <span className="text-white font-bold text-lg">Y {'->'}</span>
                                <span className="text-[#FFFF00] font-bold text-xl">0</span>
                            </div>
                        </div>
                        <span className="text-[10px] text-[#014E7F] ml-1">Imagens serão salvas em:</span>
                    </div>
                </div>
                )}
            </div>
        </div>

        {/* --- PARTE INFERIOR (RODAPÉ - GRIDS) --- */}
        <div className="flex-1 flex flex-col gap-2">
            <div className="flex gap-2 h-full">
                
                {/* Grid Esquerda */}
                <div className="flex-1 flex flex-col gap-1">
                    <div className="flex items-center bg-[#FFA500] px-2 py-1 rounded-sm h-7">
                        <span className="font-bold text-white text-[10px] flex-1">Carregar arquivo</span>
                    </div>
                    <div className="flex gap-1 items-center">
                        <input className="flex-1 bg-[#E8E8E8] border border-slate-300 h-6 rounded-sm px-1" disabled />
                        <input type="checkbox" className="h-3 w-3" />
                        <span className="text-[10px] text-slate-600">Libera</span>
                    </div>
                    <div className="flex-1 min-h-[120px]"><DarkBlueGrid /></div>
                    <div className="flex gap-1 h-10">
                        <RBSButton variant="orange" className="flex-1 h-full text-[9px] leading-tight" rounded="none">MOVER (grade)</RBSButton>
                        <RBSButton variant="orange" className="flex-1 h-full text-[9px] leading-tight" rounded="none">SALVAR NA LINHA<br/>EXISTENTE</RBSButton>
                        <RBSButton variant="orange" className="flex-1 h-full text-[10px]" rounded="none">SALVAR</RBSButton>
                        <RBSButton variant="darkBlue" className="w-14 h-full text-[10px]" rounded="none">Fim POS</RBSButton>
                    </div>
                </div>

                {/* Grid Direita */}
                <div className="flex-1 flex flex-col gap-1">
                    <div className="flex items-center bg-[#FFA500] px-2 py-1 rounded-sm h-7">
                        <span className="font-bold text-white text-[10px] flex-1">Carregar arquivo</span>
                    </div>
                    <div className="flex gap-1 items-center">
                        <input className="flex-1 bg-[#E8E8E8] border border-slate-300 h-6 rounded-sm px-1" disabled />
                        <input type="checkbox" className="h-3 w-3" />
                        <span className="text-[10px] text-slate-600">Libera</span>
                    </div>
                    <div className="flex-1 min-h-[120px]"><DarkBlueGrid /></div>
                    <div className="flex gap-1 h-10">
                        <RBSButton variant="orange" className="flex-1 h-full text-[9px] leading-tight" rounded="none">MOVER (grade)</RBSButton>
                        <RBSButton variant="orange" className="flex-1 h-full text-[9px] leading-tight" rounded="none">SALVAR NA LINHA<br/>EXISTENTE</RBSButton>
                        <RBSButton variant="orange" className="flex-1 h-full text-[10px]" rounded="none">SALVAR</RBSButton>
                        <RBSButton variant="darkBlue" className="w-14 h-full text-[10px]" rounded="none">Fim POS</RBSButton>
                    </div>
                </div>
            </div>

            {/* Painel Arquivos (Canto Inferior) */}
            <div className="h-40 flex gap-2">
                <div className="w-64 flex flex-col h-full border border-slate-300 rounded">
                    {/* Header das Abas Pequenas */}
                    <div className="flex gap-1 text-[10px] border-b border-slate-300 bg-white px-1 pt-1">
                        {['Padrao', 'Comparar', 'Testar'].map(t => (
                            <button 
                            key={t}
                            onClick={() => setTabBottom(t as any)}
                            className={`px-2 py-1 ${tabBottom === t ? 'bg-white border border-b-0 border-slate-300 -mb-[1px] font-bold text-[#014E7F]' : 'bg-slate-100 text-slate-500 hover:bg-slate-200'}`}
                            >
                            {t === 'Testar' ? 'Testar comparação' : t}
                            </button>
                        ))}
                    </div>

                    {/* Conteúdo das Abas */}
                    <div className="bg-[#F0F0F0] p-2 flex-1 flex flex-col gap-2 overflow-hidden">
                        
                        {/* === ABA PADRÃO === */}
                        {tabBottom === 'Padrao' && (
                            <div className="flex gap-2 h-full">
                                <div className="w-1/2 bg-white border border-slate-300 h-full"></div>
                                <div className="w-1/2 flex flex-col gap-2">
                                    <div className="flex items-center gap-1">
                                        <input type="checkbox" className="h-3 w-3" />
                                        <span className="text-[9px] text-teal-600 font-bold">Diretório PADRÃO</span>
                                    </div>
                                    <RBSButton variant="darkBlue" className="w-full text-[9px] h-7" rounded="xl">Diretório Padrão</RBSButton>
                                    <RBSButton variant="darkBlue" className="w-full text-[9px] h-7" rounded="xl">Editar Arquivos</RBSButton>
                                    <RBSButton variant="darkBlue" className="w-full text-[9px] h-7" rounded="xl">Atualizar lista</RBSButton>
                                    <div className="mt-auto">
                                        <label className="text-[9px] text-[#014E7F]">Nome da Imagem</label>
                                        <RBSTextBox className="h-6 border-[#014E7F]" />
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* === ABA COMPARAR (Layout da Imagem 1) === */}
                        {tabBottom === 'Comparar' && (
                            <div className="flex gap-2 h-full">
                                {/* Lista vazia esquerda */}
                                <div className="w-1/2 bg-white border border-slate-300 h-full overflow-y-auto p-1">
                                    {/* Itens da lista apareceriam aqui */}
                                </div>
                                {/* Controles direita */}
                                <div className="w-1/2 flex flex-col gap-2">
                                    <div className="flex items-center gap-1">
                                        <input type="checkbox" className="h-3 w-3" />
                                        <span className="text-[9px] text-teal-600 font-bold">Diretório COMPARAR</span>
                                    </div>
                                    <RBSButton variant="darkBlue" className="w-full text-[9px] h-7" rounded="xl">Dir. Comparar</RBSButton>
                                    <RBSButton variant="darkBlue" className="w-full text-[9px] h-7" rounded="xl">Editar Arquivos</RBSButton>
                                    <RBSButton variant="darkBlue" className="w-full text-[9px] h-7" rounded="xl">Atualizar lista</RBSButton>
                                    <div className="mt-auto">
                                        <label className="text-[9px] text-[#014E7F]">Nome da Imagem</label>
                                        <RBSTextBox className="h-6 border-[#014E7F]" />
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* === ABA TESTAR COMPARAÇÃO (Layout da Imagem 2) === */}
                        {tabBottom === 'Testar' && (
                            <div className="flex flex-col gap-1 h-full justify-between py-1">
                                {/* Linha 1 */}
                                <div className="flex justify-between items-start">
                                    <div className="flex flex-col">
                                        <span className="text-[#014E7F] text-[10px] font-bold">Escolher o diretório com os Padrões</span>
                                        <span className="text-slate-500 text-[9px] italic">Caminho diretório</span>
                                    </div>
                                    <RBSButton variant="darkBlue" className="w-20 h-6 text-[9px]" rounded="xl">Caminho</RBSButton>
                                </div>

                                {/* Linha 2 */}
                                <div className="flex justify-between items-start mt-1">
                                    <div className="flex flex-col">
                                        <span className="text-[#014E7F] text-[10px] font-bold">Escolher o diretório do Teste</span>
                                        <span className="text-slate-500 text-[9px] italic">Caminho diretório</span>
                                    </div>
                                    <RBSButton variant="darkBlue" className="w-20 h-6 text-[9px]" rounded="xl">Caminho</RBSButton>
                                </div>

                                {/* Botão Grande */}
                                <div className="mt-auto">
                                    <RBSButton variant="darkBlue" className="w-full h-10 text-[11px]" rounded="xl">Iniciar a comparação</RBSButton>
                                </div>
                            </div>
                        )}

                    </div>
                </div>
                
                {/* Botão Espelhar (Opcional, se estiver no layout original) */}
                <div className="flex-1"></div> 
            </div>
        </div>

      </div>

      {/* ===================================================================================== */}
      {/* COLUNA DIREITA (55% da tela) - SERIAL / CAMERAS */}
      {/* ===================================================================================== */}
      <div className="w-[55%] flex flex-col h-full">
           <div className="flex">
              {['Serial', 'Cameras'].map(t => (
                <button
                  key={t}
                  onClick={() => setTabRight(t as any)}
                  className={`px-4 py-1 text-xs rounded-t-sm border border-b-0 ${tabRight === t ? 'bg-white font-bold text-black z-10 -mb-[1px] border-slate-400' : 'bg-[#E1E1E1] text-slate-600 border-slate-300'}`}
                >
                  {t === 'Cameras' ? 'Câmeras' : t}
                </button>
              ))}
              <div className="flex-1 border-b border-slate-400"></div>
           </div>

           <div className="bg-white border border-slate-400 p-2 flex-1 flex gap-2 border-t-0 overflow-hidden">
              
              {/* --- ABA SERIAL DIREITA --- */}
              {tabRight === 'Serial' && (
                <div className="flex-1 flex gap-2 overflow-hidden">
                  <div className="flex-1 flex flex-col gap-1 overflow-y-auto pr-2">
                    
                    <RBSGroupBox title="Enviar Comandos {Acionamentos} - Serial 1">
                      <div className="flex flex-col gap-1">
                        <input 
                          className="w-full bg-[#BFCDDB] border-none h-6 text-xs px-1 outline-none font-bold text-[#014E7F]" 
                          placeholder="Ex: P_1, K5_1, B1_0..."
                          value={serialInputs.port1}
                          onChange={(e) => setSerialInputs(prev => ({...prev, port1: e.target.value}))}
                          onKeyPress={(e) => e.key === 'Enter' && sendManualCommand(1)}
                        />
                        <div className="h-24 bg-[#014E7F] w-full border border-[#003355] p-1 font-mono text-green-400 text-[9px] overflow-y-auto">
                          {serialLogs.port1 || 'Aguardando comandos...'}
                        </div>
                        <div className="flex justify-between mt-1">
                          <RBSButton 
                            variant="orange" 
                            className="w-28 text-[10px]"
                            onClick={() => sendIRGetCommand(3)}
                          >
                            Teste GET (IR)
                          </RBSButton>
                          <div className="flex gap-1">
                            <RBSButton 
                              variant="orange" 
                              className="w-16 text-[10px]"
                              onClick={() => clearSerialLog('port1')}
                            >
                              Limpar
                            </RBSButton>
                            <RBSButton 
                              variant="orange" 
                              className="w-16 text-[10px]"
                              onClick={() => sendManualCommand(1)}
                            >
                              Enviar
                            </RBSButton>
                          </div>
                        </div>
                      </div>
                    </RBSGroupBox>

                    <RBSGroupBox title="Enviar Comandos {Motores} - Serial 2">
                      <div className="flex flex-col gap-1">
                        <input 
                          className="w-full bg-[#BFCDDB] border-none h-6 text-xs px-1 outline-none font-bold text-[#014E7F]" 
                          placeholder="Ex: G90 X100 Y200, $H, $X..."
                          value={serialInputs.port2}
                          onChange={(e) => setSerialInputs(prev => ({...prev, port2: e.target.value}))}
                          onKeyPress={(e) => e.key === 'Enter' && sendManualCommand(2)}
                        />
                        <div className="h-24 bg-[#014E7F] w-full border border-[#003355] p-1 font-mono text-green-400 text-[9px] overflow-y-auto">
                          {serialLogs.port2 || 'Aguardando comandos GRBL...'}
                        </div>
                        <div className="flex justify-between mt-1">
                          <RBSButton 
                            variant="orange" 
                            className="w-28 text-[10px]"
                            onClick={() => sendGRBLCommand('$?')}
                          >
                            Status GRBL
                          </RBSButton>
                          <div className="flex gap-1">
                            <RBSButton 
                              variant="orange" 
                              className="w-16 text-[10px]"
                              onClick={() => clearSerialLog('port2')}
                            >
                              Limpar
                            </RBSButton>
                            <RBSButton 
                              variant="orange" 
                              className="w-16 text-[10px]"
                              onClick={() => sendManualCommand(2)}
                            >
                              Enviar
                            </RBSButton>
                          </div>
                        </div>
                      </div>
                    </RBSGroupBox>

                    <RBSGroupBox title="Enviar Comandos {IR} - Serial 3">
                      <div className="flex flex-col gap-1">
                        <input 
                          className="w-full bg-[#BFCDDB] border-none h-6 text-xs px-1 outline-none font-bold text-[#014E7F]" 
                          placeholder="Ex: GET (Arduino Nano IR)"
                          value={serialInputs.port3}
                          onChange={(e) => setSerialInputs(prev => ({...prev, port3: e.target.value}))}
                          onKeyPress={(e) => e.key === 'Enter' && sendManualCommand(3)}
                        />
                        <div className="h-24 bg-[#014E7F] w-full border border-[#003355] p-1 font-mono text-green-400 text-[9px] overflow-y-auto">
                          {serialLogs.port3 || 'Aguardando dados IR...'}
                        </div>
                        <div className="flex justify-between mt-1">
                          <RBSButton 
                            variant="orange" 
                            className="w-28 text-[10px]"
                            onClick={() => resetArduinoNano(3)}
                          >
                            Reset Nano
                          </RBSButton>
                          <div className="flex gap-1">
                            <RBSButton 
                              variant="orange" 
                              className="w-16 text-[10px]"
                              onClick={() => clearSerialLog('port3')}
                            >
                              Limpar
                            </RBSButton>
                            <RBSButton 
                              variant="orange" 
                              className="w-16 text-[10px]"
                              onClick={() => sendManualCommand(3)}
                            >
                              Enviar
                            </RBSButton>
                          </div>
                        </div>
                      </div>
                    </RBSGroupBox>

                    <RBSGroupBox title="Status IR - Dados Recebidos">
                      <div className="flex flex-col gap-1">
                        <div className="text-[10px] text-slate-600 mb-1">
                          Últimos dados IR recebidos:
                        </div>
                        <div className="h-24 bg-yellow-50 border border-yellow-300 p-1 font-mono text-orange-600 text-[9px] overflow-y-auto">
                          {irData || 'Nenhum dado IR recebido ainda...'}
                        </div>
                        <div className="flex justify-between mt-1">
                          <div className="text-[9px] text-slate-500">
                            Arduino Nano: {portConnections.port3 ? '🟢 Online' : '🔴 Offline'}
                          </div>
                          <RBSButton 
                            variant="blue" 
                            className="w-20 text-[9px]"
                            onClick={() => sendIRGetCommand(3)}
                          >
                            GET IR
                          </RBSButton>
                        </div>
                      </div>
                    </RBSGroupBox>
                  </div>

                  <div className="w-40 flex flex-col items-center justify-center border border-slate-200 bg-slate-50 relative">
                     <div className="absolute top-2 right-2 text-[#014E7F]"><ImageIcon /></div>
                     <div className="text-slate-400 text-center px-4">
                        <div className="h-64 w-16 border border-slate-300 rounded-full mx-auto flex items-center justify-center bg-white shadow-sm">
                           <span className="text-[10px]">Controle</span>
                        </div>
                     </div>
                  </div>
                </div>
              )}

              {/* --- ABA CÂMERAS --- */}
              {tabRight === 'Cameras' && (
                <div className="flex-1 flex flex-col h-full">
                  <div className="flex-1 flex gap-2 min-h-0">
                    <div className="flex-1 grid grid-cols-2 grid-rows-2 gap-2">
                      <div className="bg-[#DDEEFF] border border-slate-300 p-1 text-[#014E7F]">Câmera 1</div>
                      <div className="bg-[#DDEEFF] border border-slate-300 p-1 text-[#014E7F]">Câmera 2</div>
                      <div className="bg-[#DDEEFF] border border-slate-300 p-1 text-[#014E7F]">Câmera 3</div>
                      <div className="bg-[#DDEEFF] border border-slate-300 p-1 text-[#014E7F]">Câmera 4</div>
                    </div>

                    <div className="w-20 flex flex-col items-center gap-4 py-2">
                       <div className="flex flex-col items-center gap-1">
                          <RBSCircularBtn variant="green" size="w-12 h-12" icon={<Crop size={20} />} />
                          <span className="text-[10px] text-center leading-tight text-[#014E7F]">Salvar ROI</span>
                       </div>
                       <div className="flex flex-col items-center gap-1">
                          <RBSCircularBtn variant="green" size="w-12 h-12" icon={<Camera size={20} />} />
                          <span className="text-[10px] text-center leading-tight text-[#014E7F]">Captura Imagem</span>
                       </div>
                       <div className="flex flex-col items-center gap-1">
                          <RBSCircularBtn variant="green" size="w-12 h-12" icon={<Video size={20} />} />
                          <span className="text-[10px] text-center leading-tight text-[#014E7F]">Iniciar Câmeras</span>
                       </div>
                       
                       <div className="mt-auto flex flex-col gap-2 items-center">
                          <div className="flex flex-col items-center gap-1">
                             <RBSCircularBtn variant="red" size="w-12 h-12" icon={<Crop size={20} />} />
                             <span className="text-[10px] text-center leading-tight text-[#014E7F]">ROI 1</span>
                          </div>
                          <div className="flex flex-col items-center gap-1">
                             <RBSCircularBtn variant="red" size="w-12 h-12" icon={<Crop size={20} />} />
                             <span className="text-[10px] text-center leading-tight text-[#014E7F]">ROI 2</span>
                          </div>
                       </div>
                    </div>
                  </div>

                  {/* Busca de Guias */}
                  <div className="h-24 mt-2 flex gap-2 text-[10px]">
                    <div className="flex-1 flex flex-col gap-1">
                       <span className="text-[#014E7F]">Buscar guia das Câmeras 1</span>
                       <div className="flex gap-1"><RBSTextBox placeholder="G90 X0 Y110.000" /><RBSButton className="w-28 h-6" variant="darkBlue">Do ponto 1 ao 2</RBSButton></div>
                       <span className="text-[#014E7F] mt-1">Buscar guia das Câmeras 2</span>
                       <div className="flex gap-1"><RBSTextBox placeholder="G90 X362.296 Y110.000" /><RBSButton className="w-28 h-6" variant="darkBlue">Do ponto 2 ao 1</RBSButton></div>
                    </div>
                    <div className="w-48 flex flex-col gap-1">
                       <span className="text-[#014E7F]">% Similaridade</span>
                       <div className="flex gap-1">
                          <RBSTextBox className="text-center" placeholder="90" />
                          <RBSTextBox className="text-center" placeholder="90" />
                          <RBSTextBox className="text-center" placeholder="90" />
                          <RBSTextBox className="text-center" placeholder="90" />
                       </div>
                       <RBSButton className="w-full h-6 mt-1" variant="darkBlue">Definir valor Similaridade</RBSButton>
                    </div>
                  </div>
                </div>
              )}
           </div>
        </div>

    </div>
  );
};

export default Config;
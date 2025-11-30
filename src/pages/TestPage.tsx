import { useState, useEffect } from 'react';
import TopBar from "@/components/TopBar";
import StatusCard from "@/components/StatusCard";
import ControlPanel from "@/components/ControlPanel";
import CameraView from "@/components/CameraView";
import RemoteControlContainer from "@/components/RemoteControlContainer";
import ImageCapture from "@/components/ImageCapture";
import InfoPanel from "@/components/InfoPanel";
import { apiService } from '@/services/api';

const TestPage = () => {
  const [testTime, setTestTime] = useState(0);
  const [isTestRunning, setIsTestRunning] = useState(false);
  const [serverStatus, setServerStatus] = useState('checking');
  const [testStatus, setTestStatus] = useState('idle');
  const [message, setMessage] = useState('');
  const [cameraPositions, setCameraPositions] = useState<number[]>([0, 1, 2, 3]);
  const [approvedCount, setApprovedCount] = useState(0);
  const [rejectedCount, setRejectedCount] = useState(0);
  const [testReport, setTestReport] = useState<any>(null);

  useEffect(() => {
    checkServerStatus();
    loadCameraPositions();
    
    // Listener para mudanças no localStorage (quando trocar posições nas configurações)
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === 'cameraPositions') {
        loadCameraPositions();
      }
    };
    
    // Listener para evento customizado (mudanças na mesma aba)
    const handleCameraPositionsChanged = () => {
      loadCameraPositions();
    };
    
    window.addEventListener('storage', handleStorageChange);
    window.addEventListener('cameraPositionsChanged', handleCameraPositionsChanged);
    
    // Também verificar mudanças periodicamente (fallback)
    const interval = setInterval(() => {
      loadCameraPositions();
    }, 1000);
    
    return () => {
      window.removeEventListener('storage', handleStorageChange);
      window.removeEventListener('cameraPositionsChanged', handleCameraPositionsChanged);
      clearInterval(interval);
    };
  }, []);
  
  const loadCameraPositions = () => {
    try {
      const saved = localStorage.getItem('cameraPositions');
      if (saved) {
        const positions = JSON.parse(saved);
        setCameraPositions(positions);
      }
    } catch (error) {
      console.error('Erro ao carregar posições das câmeras:', error);
    }
  };

  const checkServerStatus = async () => {
    setServerStatus('checking');
    const isOnline = await apiService.checkServerStatus();
    setServerStatus(isOnline ? 'online' : 'offline');
  };

  useEffect(() => {
    let interval;

    if (isTestRunning) {
      interval = setInterval(() => {
        setTestTime((prevTime) => prevTime + 1);
      }, 1000);
    }

    return () => interval && clearInterval(interval);
  }, [isTestRunning]);

  // Busca o relatório de validação periodicamente
  useEffect(() => {
    const fetchReport = async () => {
      try {
        const response = await apiService.getTestReport();
        if (response.status === 'success' && response.relatorio) {
          setTestReport(response.relatorio);
          
          // Atualiza contadores
          const resumo = response.relatorio.resumo || {};
          setApprovedCount(resumo.controles_aprovados || 0);
          setRejectedCount(resumo.controles_reprovados || 0);
        }
      } catch (error) {
        console.error('Erro ao buscar relatório:', error);
      }
    };

    // Busca imediatamente e depois a cada 2 segundos
    fetchReport();
    const interval = setInterval(fetchReport, 2000);

    return () => clearInterval(interval);
  }, []);

  // Busca mensagens da pneumática periodicamente
  useEffect(() => {
    const fetchPneumaticMessage = async () => {
      try {
        const response = await apiService.getPneumaticMessage();
        if (response.status === 'success') {
          if (response.message) {
            // Atualiza a mensagem na dashboard
            setMessage(response.message);
            
            // Se recebeu START e está pronto, atualiza o status
            if (response.message.includes('START recebido') && response.ready) {
              setIsTestRunning(true);
              setTestStatus('running');
            }
          } else if (response.ready) {
            // Se as portas estão conectadas mas não há mensagem, mostra status pronto
            // Só atualiza se não houver uma mensagem importante
            setMessage((prevMessage) => {
              if (!prevMessage || 
                  prevMessage === '⏹️ Teste interrompido' ||
                  prevMessage.includes('Pronto para receber')) {
                return '🟢 Pronto para receber START via pneumática';
              }
              return prevMessage;
            });
          }
        }
      } catch (error) {
        console.error('Erro ao buscar mensagem pneumática:', error);
      }
    };

    // Busca imediatamente e depois a cada 1 segundo (mais frequente para mensagens)
    fetchPneumaticMessage();
    const interval = setInterval(fetchPneumaticMessage, 1000);

    return () => clearInterval(interval);
  }, []);

  const formatTime = (totalSeconds) => {
    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = totalSeconds % 60;

    return `${hours.toString().padStart(2, '0')}:${minutes
      .toString()
      .padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
  };

  const executeFingerDown = async () => {
    if (serverStatus !== 'online') {
      setMessage('❌ Servidor offline - Não foi possível iniciar o teste');
      return;
    }

    try {
      setIsTestRunning(true);
      setTestStatus('running');
      setMessage('🔄 Iniciando sequência FingerDown...');

      const result = await apiService.executeFingerDown();

      setTestStatus('success');
      setMessage('✅ FingerDown executado com sucesso!');
      console.log('FINGERDOWN executado:', result);
    } catch (error) {
      console.error('Erro no FingerDown:', error);
      setTestStatus('error');
      setMessage('❌ Erro ao executar FingerDown');
      setIsTestRunning(false);
    }
  };

  const executeFingerDownWithPhotos = async () => {
    if (serverStatus !== 'online') {
      setMessage('❌ Servidor offline - Não foi possível iniciar o teste');
      return;
    }

    try {
      setIsTestRunning(true);
      setTestStatus('running');
      setMessage('📸 Iniciando sequência FingerDown COM FOTOS...');

      const result = await apiService.executeFingerDownWithPhotos();

      setTestStatus('success');
      setMessage('✅ FingerDown com fotos executado com sucesso!');
      console.log('FINGERDOWN COM FOTOS executado:', result);
    } catch (error) {
      console.error('Erro no FingerDown com fotos:', error);
      setTestStatus('error');
      setMessage('❌ Erro ao executar FingerDown com fotos');
      setIsTestRunning(false);
    }
  };

  const handleInputChange = (value) => {
    const val = value.toLowerCase();

    if (val.includes('start') && !isTestRunning) {
      setTestTime(0);
      // Agora o "start" também executa com comparação de imagens
      executeFingerDownWithPhotos();
    }

    if (val.includes('stop') && isTestRunning) {
      handleStopTest();
    }
  };

  const handleStopTest = () => {
    setIsTestRunning(false);
    setTestStatus('idle');
    setMessage('⏹️ Teste interrompido');
  };

  return (
    <div className="flex h-screen overflow-hidden">
      <div className="flex-1 flex flex-col overflow-hidden">
        <TopBar />

        <main
          className="flex-1 overflow-auto"
          style={{ backgroundColor: 'hsla(0, 0%, 89%, 1.00)' }}
        >
          <div className="grid grid-cols-12 gap-4 h-full p-4">
            
            {/* LEFT SIDE */}
            <div className="col-span-5">

              {/* TOP BLOCK */}
              <div className="bg-secondary/20 rounded-lg p-4 border border-border mb-3">

                {/* NEW GRID */}
                <div className="grid grid-cols-4 gap-3 mb-4">

                  {/* APROVADO */}
                  <StatusCard title="Aprovado" value={approvedCount} variant="success" />

                  {/* REPROVADO */}
                  <StatusCard title="Reprovado" value={rejectedCount} variant="destructive" />

                  {/* CICLOS */}
                  <StatusCard title="Ciclos" value="" />

                  {/* MENSAGENS */}
                  <div className="bg-card rounded-lg p-3 border border-border">
                    <p className="text-xs font-medium text-muted-foreground mb-2">
                      Mensagens{' '}
                      {serverStatus === 'online'
                        ? '🟢'
                        : serverStatus === 'offline'
                        ? '🔴'
                        : '🟡'}
                    </p>

                    <input
                      type="text"
                      className="w-full p-2 border border-gray-300 rounded-md text-sm mb-1"
                      placeholder="Digite 'start'"
                      onChange={(e) => handleInputChange(e.target.value)}
                    />

                    <button
                      onClick={executeFingerDownWithPhotos}
                      disabled={isTestRunning || serverStatus !== 'online'}
                      className="w-full mt-2 px-3 py-2 bg-green-600 text-white text-xs font-semibold rounded hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                    >
                      <span>📸</span>
                      <span>Iniciar com Fotos</span>
                    </button>

                    {message && (
                      <p
                        className={`text-xs mt-1 ${
                          message.includes('❌')
                            ? 'text-destructive'
                            : message.includes('✅')
                            ? 'text-success'
                            : message.includes('🔄')
                            ? 'text-blue-500'
                            : message.includes('📸')
                            ? 'text-purple-500'
                            : 'text-muted-foreground'
                        }`}
                      >
                        {message}
                      </p>
                    )}
                  </div>

                  {/* LINHA 2 */}

                  {/* TEMPO */}
                  <div className="bg-card rounded-lg p-4 border border-border flex items-center justify-center">
                    <p
                      className={`text-3xl font-bold ${
                        isTestRunning
                          ? 'text-success'
                          : testStatus === 'success'
                          ? 'text-green-600'
                          : testStatus === 'error'
                          ? 'text-destructive'
                          : 'text-muted-foreground'
                      }`}
                    >
                      {formatTime(testTime)}
                    </p>
                  </div>

                  {/* TESTADOS */}
                  <div className="bg-card rounded-lg p-3 border border-border flex flex-col items-center justify-center">
                    <p className="text-xs font-medium text-muted-foreground">
                      Testados (UN.)
                    </p>
                  </div>

                  {/* STATUS HOME */}
                  <InfoPanel title="Status Home" />
                </div>
              </div>

              {/* REMOTE CONTROLS - NOW MOVED UP */}
              <RemoteControlContainer testReport={testReport} />
            </div>

            {/* CENTER */}
            <div className="col-span-1 flex flex-col justify-center gap-4">
              <ControlPanel />
              <ImageCapture />
            </div>

            {/* RIGHT SIDE */}
            <div className="col-span-6">
              <div className="grid grid-cols-2 gap-4 h-full">
                {[0, 1, 2, 3].map((displayIndex) => {
                  const cameraId = cameraPositions[displayIndex];
                  const actualCameraNumber = cameraId + 1; // cameraId é 0-3, cameraNumber é 1-4
                  return (
                    <CameraView 
                      key={displayIndex}
                      cameraNumber={actualCameraNumber} 
                      controlNumber={displayIndex + 1}
                      displayPosition={displayIndex + 1}
                    />
                  );
                })}
              </div>
            </div>

          </div>
        </main>
      </div>
    </div>
  );
};

export default TestPage;

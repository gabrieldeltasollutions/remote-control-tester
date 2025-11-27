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
  const [serverStatus, setServerStatus] = useState<'online' | 'offline' | 'checking'>('checking');
  const [testStatus, setTestStatus] = useState<'idle' | 'running' | 'success' | 'error'>('idle');
  const [message, setMessage] = useState('');

  // Verificar status do servidor
  useEffect(() => {
    checkServerStatus();
  }, []);

  const checkServerStatus = async () => {
    setServerStatus('checking');
    const isOnline = await apiService.checkServerStatus();
    setServerStatus(isOnline ? 'online' : 'offline');
  };

  // Efeito para o cronômetro
  useEffect(() => {
    let interval: NodeJS.Timeout;

    if (isTestRunning) {
      interval = setInterval(() => {
        setTestTime(prevTime => prevTime + 1);
      }, 1000);
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isTestRunning]);

  const formatTime = (totalSeconds: number) => {
    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = totalSeconds % 60;
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
  };

  // Função para executar o FingerDown
  const executeFingerDown = async () => {
    if (serverStatus !== 'online') {
      setMessage('❌ Servidor offline - Não foi possível iniciar o teste');
      return;
    }

    try {
      setIsTestRunning(true);
      setTestStatus('running');
      setMessage('🔄 Iniciando sequência FingerDown...');

      console.log('=== INICIANDO FINGERDOWN 1 ===');
      
      const result = await apiService.executeFingerDown();
      
      setTestStatus('success');
      setMessage('✅ FingerDown executado com sucesso!');
      console.log('✅ FINGERDOWN 1 CONCLUÍDO', result);
      
    } catch (error) {
      console.error('❌ Erro no FingerDown:', error);
      setTestStatus('error');
      setMessage('❌ Erro ao executar FingerDown');
      setIsTestRunning(false);
    }
  };

  // Função para lidar com o start
  const handleStartTest = () => {
    if (isTestRunning) {
      setMessage('⚠️ Teste já está em andamento');
      return;
    }

    setTestTime(0);
    executeFingerDown();
  };

  // Função para parar o teste
  const handleStopTest = () => {
    setIsTestRunning(false);
    setTestStatus('idle');
    setMessage('⏹️ Teste interrompido');
  };

  return (
    <div className="flex h-screen overflow-hidden">
      <div className="flex-1 flex flex-col overflow-hidden">
        <TopBar />
        
        <main className="flex-1 overflow-auto" style={{ backgroundColor: "hsla(0, 0%, 89%, 1.00)" }} p-4>
          <div className="grid grid-cols-12 gap-4 h-full">
            {/* Left Section - Stats and Remote Controls */}
            <div className="col-span-5 space-y-4">
              {/* Stats Section */}
              <div className="bg-secondary/20 rounded-lg p-4 border border-border">
                <div className="grid grid-cols-4 gap-3 mb-4">
                  <StatusCard 
                    title="Aprovado" 
                    value={0} 
                    variant="success"
                    subtitle=""
                  />
                  <StatusCard 
                    title="Reprovado" 
                    value={0} 
                    variant="destructive" 
                  />
                  <div className="space-y-3">
                    <StatusCard 
                      title="Ciclos" 
                      value="" 
                    />
                    <div className="bg-card rounded-lg p-3 border border-border">
                      <p className="text-xs font-medium text-muted-foreground">Testados (UN.)</p>
                    </div>
                  </div>
                  <div className="space-y-3">
                    {/* Box Mensagens com campo de start */}
                    <div className="bg-card rounded-lg p-3 border border-border">
                      <p className="text-xs font-medium text-muted-foreground mb-2">
                        Mensagens {serverStatus === 'online' ? '🟢' : serverStatus === 'offline' ? '🔴' : '🟡'}
                      </p>
                      <input 
                        type="text"
                        className="w-full p-2 border border-gray-300 rounded-md text-sm mb-1"
                        placeholder="Digite 'start' e pressione Enter"
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') {
                            const input = e.target as HTMLInputElement;
                            if (input.value.toLowerCase() === 'start') {
                              handleStartTest();
                              input.value = '';
                            } else if (input.value.toLowerCase() === 'stop') {
                              handleStopTest();
                              input.value = '';
                            }
                          }
                        }}
                      />
                      {message && (
                        <p className={`text-xs mt-1 ${
                          message.includes('❌') ? 'text-destructive' : 
                          message.includes('✅') ? 'text-success' : 
                          message.includes('🔄') ? 'text-blue-500' : 
                          'text-muted-foreground'
                        }`}>
                          {message}
                        </p>
                      )}
                    </div>
                    
                    <InfoPanel title="Status Home" />
                  </div>
                </div>
                
                <div className="bg-card rounded-lg p-4 border border-border">
                  <h3 className="text-sm font-medium text-muted-foreground mb-2">Tempo de Teste</h3>
                  <p className={`text-4xl font-bold ${
                    isTestRunning ? 'text-success' : 
                    testStatus === 'success' ? 'text-green-600' :
                    testStatus === 'error' ? 'text-destructive' : 
                    'text-muted-foreground'
                  }`}>
                    {formatTime(testTime)}
                  </p>
                  <div className="flex gap-2 mt-2">
                    <button
                      onClick={handleStartTest}
                      disabled={isTestRunning || serverStatus !== 'online'}
                      className="px-3 py-1 bg-green-600 text-white rounded text-sm disabled:bg-gray-400"
                    >
                      Start
                    </button>
                    <button
                      onClick={handleStopTest}
                      disabled={!isTestRunning}
                      className="px-3 py-1 bg-red-600 text-white rounded text-sm disabled:bg-gray-400"
                    >
                      Stop
                    </button>
                    <button
                      onClick={checkServerStatus}
                      className="px-3 py-1 bg-blue-600 text-white rounded text-sm"
                    >
                      {serverStatus === 'checking' ? '...' : '🔄'}
                    </button>
                  </div>
                </div>
              </div>
              
              {/* Remote Control Containers */}
              <RemoteControlContainer />
            </div>
            
            {/* Center Section - Control Panel */}
            <div className="col-span-1 flex flex-col justify-center gap-4">
              <ControlPanel />
              <ImageCapture />
            </div>
            
            {/* Right Section - Cameras 2x2 */}
            <div className="col-span-6">
              <div className="grid grid-cols-2 gap-4 h-full">
                <CameraView cameraNumber={1} controlNumber={1} />
                <CameraView cameraNumber={2} controlNumber={2} />
                <CameraView cameraNumber={3} controlNumber={3} />
                <CameraView cameraNumber={4} controlNumber={4} />
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

export default TestPage;
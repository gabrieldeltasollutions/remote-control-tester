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

  useEffect(() => {
    checkServerStatus();
  }, []);

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

  const handleInputChange = (value) => {
    const val = value.toLowerCase();

    if (val.includes('start') && !isTestRunning) {
      setTestTime(0);
      executeFingerDown();
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
                  <StatusCard title="Aprovado" value={0} variant="success" />

                  {/* REPROVADO */}
                  <StatusCard title="Reprovado" value={0} variant="destructive" />

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

                    {message && (
                      <p
                        className={`text-xs mt-1 ${
                          message.includes('❌')
                            ? 'text-destructive'
                            : message.includes('✅')
                            ? 'text-success'
                            : message.includes('🔄')
                            ? 'text-blue-500'
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
              <RemoteControlContainer />
            </div>

            {/* CENTER */}
            <div className="col-span-1 flex flex-col justify-center gap-4">
              <ControlPanel />
              <ImageCapture />
            </div>

            {/* RIGHT SIDE */}
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

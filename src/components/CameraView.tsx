import { useState, useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";

interface CameraViewProps {
  cameraNumber: number;
  controlNumber: number;
}

const API_BASE_URL = 'http://localhost:8000';

const CameraView = ({ cameraNumber, controlNumber }: CameraViewProps) => {
  const [cameraStatus, setCameraStatus] = useState<'connected' | 'disconnected' | 'loading'>('loading');
  const [hasFrame, setHasFrame] = useState(false);
  const [isReconnecting, setIsReconnecting] = useState(false);
  const imgRef = useRef<HTMLImageElement>(null);
  const statusCheckIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // ID da câmera (0-3) baseado no cameraNumber (1-4)
  const cameraId = cameraNumber - 1;

  // Verificar status da câmera
  const checkCameraStatus = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/camera_status/${cameraId}`);
      if (response.ok) {
        const data = await response.json();
        setCameraStatus(data.connected ? 'connected' : 'disconnected');
        setHasFrame(data.has_frame || false);
      } else {
        setCameraStatus('disconnected');
        setHasFrame(false);
      }
    } catch (error) {
      console.error(`Erro ao verificar status da câmera ${cameraId}:`, error);
      setCameraStatus('disconnected');
      setHasFrame(false);
    }
  };

  // Reconectar câmera
  const handleReconnect = async () => {
    setIsReconnecting(true);
    try {
      const response = await fetch(`${API_BASE_URL}/reconnect_camera/${cameraId}`, {
        method: 'POST',
      });
      
      if (response.ok) {
        const data = await response.json();
        setCameraStatus(data.connected ? 'connected' : 'disconnected');
        
        // Recarregar o stream
        if (imgRef.current) {
          const currentSrc = imgRef.current.src;
          imgRef.current.src = '';
          setTimeout(() => {
            if (imgRef.current) {
              imgRef.current.src = `${API_BASE_URL}/stream/${cameraId}?t=${Date.now()}`;
            }
          }, 100);
        }
      }
    } catch (error) {
      console.error(`Erro ao reconectar câmera ${cameraId}:`, error);
    } finally {
      setIsReconnecting(false);
      // Verificar status após 1 segundo
      setTimeout(checkCameraStatus, 1000);
    }
  };

  // Tratar erro de carregamento do stream
  const handleStreamError = () => {
    setHasFrame(false);
    // Tentar recarregar após 2 segundos
    setTimeout(() => {
      if (imgRef.current) {
        const src = imgRef.current.src;
        imgRef.current.src = '';
        setTimeout(() => {
          if (imgRef.current) {
            imgRef.current.src = `${API_BASE_URL}/stream/${cameraId}?t=${Date.now()}`;
          }
        }, 100);
      }
    }, 2000);
  };

  // Tratar carregamento bem-sucedido do stream
  const handleStreamLoad = () => {
    setHasFrame(true);
  };

  // Efeito para verificar status periodicamente
  useEffect(() => {
    checkCameraStatus();
    
    // Verificar status a cada 3 segundos
    statusCheckIntervalRef.current = setInterval(checkCameraStatus, 3000);

    return () => {
      if (statusCheckIntervalRef.current) {
        clearInterval(statusCheckIntervalRef.current);
      }
    };
  }, [cameraId]);

  return (
    <div className="
      bg-secondary/30 
      rounded-xl 
      p-3 
      border 
      border-black/30 
      flex 
      flex-col 
      w-[350px]
      h-[350px]
      max-h-[320px]
      min-h-[220px]
      aspect-video
    ">
      <div className="flex justify-between items-center mb-2">
        <div className="flex items-center gap-2">
          <h2 className="text-sm font-semibold">
            Câmera {cameraNumber} - Controle {controlNumber}
          </h2>
          <div className={`w-2 h-2 rounded-full ${
            cameraStatus === 'connected' ? 'bg-green-500' : 
            cameraStatus === 'loading' ? 'bg-yellow-500' : 
            'bg-red-500'
          }`} />
        </div>
        <Button 
          variant="default" 
          size="sm" 
          className="text-xs h-7"
          onClick={handleReconnect}
          disabled={isReconnecting}
        >
          {isReconnecting ? 'Reconectando...' : 'Reconectar'}
        </Button>
      </div>

      <div className="bg-black rounded-lg flex-1 flex items-center justify-center relative overflow-hidden">
        {cameraStatus === 'connected' ? (
          <>
            <img
              ref={imgRef}
              src={`${API_BASE_URL}/stream/${cameraId}`}
              alt={`Câmera ${cameraNumber}`}
              className="w-full h-full object-contain"
              onError={handleStreamError}
              onLoad={handleStreamLoad}
            />
            {!hasFrame && (
              <div className="absolute inset-0 flex items-center justify-center bg-black/80">
                <p className="text-white text-sm">Aguardando frame...</p>
              </div>
            )}
          </>
        ) : (
          <div className="absolute inset-0 flex items-center justify-center">
            <p className="text-muted-foreground text-sm">
              {cameraStatus === 'loading' ? 'Carregando...' : 'Câmera Desconectada'}
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default CameraView;

import { useState, useRef, useEffect } from 'react';
import { RotateCw, Download } from 'lucide-react';
import { apiService } from '@/services/api';

interface CameraConfigItemProps {
  cameraId: number;
  displayNumber: number;
  rotation: number;
  onRotate: (cameraId: number, rotation: number) => void;
  onSwap: (from: number, to: number) => void;
  onCapture: (cameraId: number) => void;
}

const API_BASE_URL = 'http://localhost:8000';

const CameraConfigItem = ({ 
  cameraId, 
  displayNumber, 
  rotation, 
  onRotate, 
  onSwap, 
  onCapture 
}: CameraConfigItemProps) => {
  const [isConnected, setIsConnected] = useState(false);
  const [hasFrame, setHasFrame] = useState(false);
  const imgRef = useRef<HTMLImageElement>(null);

  useEffect(() => {
    checkStatus();
    const interval = setInterval(checkStatus, 3000);
    return () => clearInterval(interval);
  }, [cameraId]);

  const checkStatus = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/camera_status/${cameraId}`);
      if (response.ok) {
        const data = await response.json();
        setIsConnected(data.connected);
        setHasFrame(data.has_frame);
      }
    } catch (error) {
      console.error(`Erro ao verificar status da câmera ${cameraId}:`, error);
    }
  };

  const handleRotate = () => {
    const newRotation = (rotation + 90) % 360;
    onRotate(cameraId, newRotation);
  };

  const handleCapture = async () => {
    try {
      await apiService.downloadCameraFrame(cameraId);
      onCapture(cameraId);
    } catch (error: any) {
      console.error('Erro ao capturar foto:', error);
      alert(`Erro ao capturar foto: ${error.message}`);
    }
  };

  return (
    <div className="relative bg-[#DDEEFF] border border-slate-300 rounded overflow-hidden">
      {/* Header */}
      <div className="bg-[#014E7F] text-white px-2 py-1 text-[10px] font-bold flex justify-between items-center">
        <span>Câmera {displayNumber}</span>
        <div className="flex gap-1 items-center">
          <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-400' : 'bg-red-400'}`} />
          <span className="text-[9px]">{isConnected ? 'Online' : 'Offline'}</span>
        </div>
      </div>
      
      {/* Video Stream */}
      <div className="relative bg-black aspect-video flex items-center justify-center">
        {isConnected ? (
          <>
            <img
              ref={imgRef}
              src={`${API_BASE_URL}/stream/${cameraId}`}
              alt={`Câmera ${displayNumber}`}
              className="w-full h-full object-contain"
              style={{ transform: `rotate(${rotation}deg)` }}
              onError={() => setHasFrame(false)}
              onLoad={() => setHasFrame(true)}
            />
            {!hasFrame && (
              <div className="absolute inset-0 flex items-center justify-center bg-black/80">
                <p className="text-white text-[10px]">Aguardando...</p>
              </div>
            )}
          </>
        ) : (
          <div className="absolute inset-0 flex items-center justify-center">
            <p className="text-white text-[10px]">Desconectada</p>
          </div>
        )}
      </div>
      
      {/* Controls */}
      <div className="p-1 flex gap-1 bg-white">
        <button
          onClick={handleRotate}
          className="flex-1 bg-[#014E7F] text-white text-[9px] px-2 py-1 rounded hover:bg-[#003366] flex items-center justify-center gap-1"
          title="Rotacionar 90°"
        >
          <RotateCw size={12} />
          <span>Rotacionar</span>
        </button>
        <button
          onClick={handleCapture}
          className="flex-1 bg-green-600 text-white text-[9px] px-2 py-1 rounded hover:bg-green-700 flex items-center justify-center gap-1"
          title="Capturar e baixar foto"
        >
          <Download size={12} />
          <span>Foto</span>
        </button>
      </div>
    </div>
  );
};

export default CameraConfigItem;


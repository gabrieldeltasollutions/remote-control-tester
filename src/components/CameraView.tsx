import { Button } from "@/components/ui/button";

interface CameraViewProps {
  cameraNumber: number;
  controlNumber: number;
}

const CameraView = ({ cameraNumber, controlNumber }: CameraViewProps) => {
  return (
    <div className="bg-secondary/30 rounded-lg p-3 border-2 border-black h-full flex flex-col">
      <div className="flex justify-between items-center mb-2">
        <h2 className="text-sm font-semibold">
          Câmera {cameraNumber} - Controle {controlNumber}
        </h2>
        <Button variant="default" size="sm" className="text-xs h-7">
          Rotacionar
        </Button>
      </div>
      <div className="bg-muted rounded flex-1 flex items-center justify-center">
        <p className="text-muted-foreground text-sm">Visualização da Câmera</p>
      </div>
    </div>
  );
};

export default CameraView;

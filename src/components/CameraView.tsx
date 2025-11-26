import { Button } from "@/components/ui/button";

interface CameraViewProps {
  cameraNumber: number;
  controlNumber: number;
}

const CameraView = ({ cameraNumber, controlNumber }: CameraViewProps) => {
  return (
    <div className="bg-secondary/30 rounded-lg p-4 min-h-[300px] border border-border">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-lg font-semibold">
          Câmera {cameraNumber} - Controle {controlNumber}
        </h2>
        <Button variant="default" size="sm">
          Rotacionar
        </Button>
      </div>
      <div className="bg-muted rounded h-64 flex items-center justify-center">
        <p className="text-muted-foreground">Visualização da Câmera</p>
      </div>
    </div>
  );
};

export default CameraView;

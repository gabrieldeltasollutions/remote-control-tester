import { Button } from "@/components/ui/button";

interface CameraViewProps {
  cameraNumber: number;
  controlNumber: number;
}

const CameraView = ({ cameraNumber, controlNumber }: CameraViewProps) => {
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
      max-h-[320px]       /* impede passar do footer */
      min-h-[220px]       /* mantém tamanho bonito */
      aspect-video        /* deixa a proporção perfeita */
    ">
      <div className="flex justify-between items-center mb-2">
        <h2 className="text-sm font-semibold">
          Câmera {cameraNumber} - Controle2 {controlNumber}
        </h2>
        <Button variant="default" size="sm" className="text-xs h-7">
          Rotacionar
        </Button>
      </div>

      <div className="bg-muted rounded-lg flex-1 flex items-center justify-center">
        <p className="text-muted-foreground text-sm">
          Visualização da Câmera
        </p>
      </div>
    </div>
  );
};

export default CameraView;

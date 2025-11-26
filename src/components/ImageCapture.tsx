import { Image } from "lucide-react";

const ImageCapture = () => {
  return (
    <div className="flex flex-col gap-3">
      <div className="grid grid-cols-2 gap-2">
        {[1, 2, 3, 4].map((num) => (
          <button
            key={num}
            className="bg-primary hover:bg-primary/90 rounded-full w-12 h-12 flex items-center justify-center text-white relative"
          >
            <Image size={20} />
            <span className="absolute -top-1 -left-1 bg-card text-foreground rounded-full w-5 h-5 flex items-center justify-center text-xs font-bold border border-border">
              {num}
            </span>
          </button>
        ))}
      </div>
      
      <button className="bg-card hover:bg-secondary border border-border text-foreground font-medium py-2 px-3 rounded-lg text-xs">
        Capturar Imagens
      </button>
    </div>
  );
};

export default ImageCapture;

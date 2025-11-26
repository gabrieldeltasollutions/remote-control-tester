import { Image } from "lucide-react";

const ImageCapture = () => {
  return (
    <div className="flex flex-col gap-4">
      <div className="grid grid-cols-2 gap-3">
        {[1, 2, 3, 4].map((num) => (
          <button
            key={num}
            className="bg-primary hover:bg-primary/90 rounded-full w-16 h-16 flex items-center justify-center text-white relative"
          >
            <Image size={28} />
            <span className="absolute -top-2 -left-2 bg-card text-foreground rounded-full w-6 h-6 flex items-center justify-center text-xs font-bold border border-border">
              {num}
            </span>
          </button>
        ))}
      </div>
      
      <button className="bg-card hover:bg-secondary border border-border text-foreground font-medium py-3 px-6 rounded-lg">
        Capturar Imagens
      </button>
    </div>
  );
};

export default ImageCapture;

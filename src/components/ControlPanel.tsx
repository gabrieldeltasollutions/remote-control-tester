import { Image, Lightbulb, Camera, Pause } from "lucide-react";

const ControlPanel = () => {
  return (
    <div className="flex flex-col items-center gap-4">
      <button className="w-16 h-16 bg-success hover:bg-success/90 rounded-full flex items-center justify-center text-white shadow-lg">
        <span className="text-2xl font-bold">1</span>
      </button>
      <button className="w-16 h-16 bg-success hover:bg-success/90 rounded-full flex items-center justify-center text-white shadow-lg">
        <Lightbulb size={28} />
      </button>
      <button className="w-16 h-16 bg-success hover:bg-success/90 rounded-full flex items-center justify-center text-white shadow-lg">
        <Camera size={28} />
      </button>
      <button className="w-16 h-16 bg-success hover:bg-success/90 rounded-full flex items-center justify-center text-white shadow-lg">
        <Pause size={28} />
      </button>
      
      <div className="flex gap-4 mt-4">
        <label className="flex items-center gap-2">
          <input type="checkbox" className="w-4 h-4" defaultChecked />
          <span className="text-sm">1</span>
        </label>
        <label className="flex items-center gap-2">
          <input type="checkbox" className="w-4 h-4" />
          <span className="text-sm">2</span>
        </label>
      </div>
    </div>
  );
};

export default ControlPanel;

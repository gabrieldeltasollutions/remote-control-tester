import { Lightbulb, Camera, Pause } from "lucide-react";

const ControlPanel = () => {
  return (
    <div className="flex flex-col items-center gap-3">
      <button className="w-14 h-14 bg-success hover:bg-success/90 rounded-full flex items-center justify-center text-white shadow-lg">
        <span className="text-xl font-bold">1</span>
      </button>
      <button className="w-14 h-14 bg-success hover:bg-success/90 rounded-full flex items-center justify-center text-white shadow-lg">
        <Lightbulb size={24} />
      </button>
      <button className="w-14 h-14 bg-success hover:bg-success/90 rounded-full flex items-center justify-center text-white shadow-lg">
        <Camera size={24} />
      </button>
      <button className="w-14 h-14 bg-success hover:bg-success/90 rounded-full flex items-center justify-center text-white shadow-lg">
        <Pause size={24} />
      </button>
      
      <div className="flex gap-3 mt-2">
        <label className="flex items-center gap-1">
          <input type="checkbox" className="w-3 h-3" defaultChecked />
          <span className="text-xs">1</span>
        </label>
        <label className="flex items-center gap-1">
          <input type="checkbox" className="w-3 h-3" />
          <span className="text-xs">2</span>
        </label>
      </div>
    </div>
  );
};

export default ControlPanel;

import { 
  MapPin, 
  Camera, 
  Home as HomeIcon, 
  Code2, 
  Settings, 
  ListChecks, 
  AlignJustify, 
  Info 
} from "lucide-react";

const TopBar = () => {
  return (
    <header className="bg-card border-b border-border py-3 px-6 flex items-center gap-4">
      <button className="p-2 hover:bg-secondary rounded">
        <MapPin className="text-primary" size={24} />
      </button>
      <button className="p-2 hover:bg-secondary rounded">
        <Camera className="text-primary" size={24} />
      </button>
      <button className="p-2 hover:bg-secondary rounded">
        <Camera className="text-primary" size={24} />
      </button>
      <button className="p-2 hover:bg-secondary rounded">
        <HomeIcon className="text-primary" size={24} />
      </button>
      <button className="p-2 hover:bg-secondary rounded">
        <Code2 className="text-primary" size={24} />
      </button>
      <button className="p-2 hover:bg-secondary rounded">
        <Code2 className="text-primary" size={24} />
      </button>
      <button className="p-2 hover:bg-secondary rounded">
        <Code2 className="text-primary" size={24} />
      </button>
      <button className="p-2 hover:bg-secondary rounded">
        <AlignJustify className="text-primary" size={24} />
      </button>
      <button className="p-2 hover:bg-secondary rounded">
        <ListChecks className="text-primary" size={24} />
      </button>
      <button className="p-2 hover:bg-secondary rounded">
        <Settings className="text-primary" size={24} />
      </button>
      <button className="p-2 hover:bg-secondary rounded">
        <Settings className="text-primary" size={24} />
      </button>
      <button className="p-2 hover:bg-secondary rounded">
        <Settings className="text-primary" size={24} />
      </button>
      <button className="p-2 hover:bg-secondary rounded">
        <Info className="text-primary" size={24} />
      </button>
    </header>
  );
};

export default TopBar;

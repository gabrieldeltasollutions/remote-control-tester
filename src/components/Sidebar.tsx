import { Home, Settings, Code, Smartphone, X, Menu } from "lucide-react";

const Sidebar = () => {
  return (
    <aside className="w-16 bg-sidebar flex flex-col items-center py-4 gap-6">
      <button className="text-sidebar-foreground hover:bg-sidebar-accent p-2 rounded">
        <Menu size={24} />
      </button>
      
      <div className="flex-1 flex flex-col gap-4">
        <button className="text-sidebar-foreground hover:bg-sidebar-accent p-2 rounded">
          <Home size={24} />
        </button>
        <button className="text-sidebar-foreground hover:bg-sidebar-accent p-2 rounded">
          <Settings size={24} />
        </button>
        <button className="text-sidebar-foreground hover:bg-sidebar-accent p-2 rounded">
          <Code size={24} />
        </button>
        <button className="text-sidebar-foreground hover:bg-sidebar-accent p-2 rounded">
          <Smartphone size={24} />
        </button>
      </div>
      
      <button className="text-sidebar-foreground hover:bg-sidebar-accent p-2 rounded">
        <X size={24} />
      </button>
    </aside>
  );
};

export default Sidebar;

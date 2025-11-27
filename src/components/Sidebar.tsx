import { Home, Settings, Code, Smartphone, X, Menu } from "lucide-react";
import { useNavigate, useLocation } from "react-router-dom";

const Sidebar = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const getButtonClass = (path: string) => {
    const isActive = location.pathname === path;
    return `p-2 rounded transition-colors ${
      isActive 
        ? "bg-sidebar-accent text-sidebar-foreground" 
        : "text-sidebar-foreground hover:bg-sidebar-accent"
    }`;
  };

  return (
    <aside className="w-16 bg-sidebar flex flex-col items-center py-4 gap-6 border-r border-sidebar-border h-screen sticky top-0">
      <button className="text-sidebar-foreground hover:bg-sidebar-accent p-2 rounded">
        <Menu size={24} />
      </button>
      
      <div className="flex-1 flex flex-col gap-4">
        {/* Botão Home -> Agora vai para a rota "/load" */}
        <button 
          onClick={() => navigate('/load')} 
          className={getButtonClass('/')}
          title="Dashboard"
        >
          <Home size={24} />
        </button>

        <button 
          onClick={() => navigate('/config')}
          className={getButtonClass('/config')}
          title="Configurações"
        >
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
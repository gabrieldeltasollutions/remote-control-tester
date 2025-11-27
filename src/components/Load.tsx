import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { startCalibration } from "../services/api"; // Serviço específico para calibração

const Load = () => {
  const navigate = useNavigate();
  const [status, setStatus] = useState("Executando Calibração!");

  useEffect(() => {
    const executeCalibration = async () => {
      try {
        setStatus("Iniciando calibração...");
        
        // O back-end sabe qual porta e comando usar
        const result = await startCalibration();
        
        if (result.status === "success") {
          setStatus("Calibração em andamento...");
          console.log("Calibração iniciada com sucesso:", result.message);
        } else {
          setStatus("Erro na calibração");
          console.error("Erro:", result.message);
        }
      } catch (error) {
        setStatus("Erro na comunicação");
        console.error("Erro ao executar calibração:", error);
      }
    };

    executeCalibration();

    const timer = setTimeout(() => {
      navigate('/');
    }, 3000);

    return () => clearTimeout(timer);
  }, [navigate]);

  return (
    <div className="flex items-center justify-center h-full w-full bg-background">
      <div className="text-center flex flex-col items-center gap-4">
        <div className="text-black text-6xl animate-camera">
          📷📷📷📷
        </div>
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-sidebar-accent"></div>
        <p className="text-black font-semibold">{status}</p>
      </div>
    </div>
  );
};

export default Load;
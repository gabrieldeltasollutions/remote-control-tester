import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Sidebar from "./components/Sidebar"; // <--- Seu Sidebar atual
import Index from "./pages/Index";
import NotFound from "./pages/NotFound";
import Config from "./pages/Config"; // <--- A página nova que criamos

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <BrowserRouter>
        {/* Container Principal FLEX: Coloca Sidebar ao lado do Conteúdo */}
        <div className="flex min-h-screen w-full bg-background">
          
          {/* 1. A Sidebar fica AQUI, fora das rotas */}
          <Sidebar />

          {/* 2. Onde o conteúdo das páginas muda */}
          <main className="flex-1 h-screen overflow-hidden bg-slate-50">
            <Routes>
              <Route path="/" element={<Index />} />
              <Route path="/config" element={<Config />} />
              <Route path="*" element={<NotFound />} />
            </Routes>
          </main>
          
        </div>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
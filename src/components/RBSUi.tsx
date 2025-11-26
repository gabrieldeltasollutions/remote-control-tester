import React from "react";
import { cn } from "@/lib/utils";

// --- Botão Retangular ---
interface RBSButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'blue' | 'darkBlue' | 'orange' | 'green' | 'red' | 'gray';
  rounded?: 'md' | 'full' | 'xl' | 'none' | 'sm';
}

export const RBSButton: React.FC<RBSButtonProps> = ({ 
  children, 
  variant = 'blue', 
  rounded = 'sm',
  className, 
  ...props 
}) => {
  const variants = {
    blue: "bg-[#014E7F] text-white hover:bg-[#013d63]",
    darkBlue: "bg-[#003355] text-white hover:bg-[#002244]",
    orange: "bg-[#FFA500] text-white hover:bg-orange-600 font-bold",
    green: "bg-[#008000] text-white hover:bg-green-700",
    red: "bg-red-600 text-white hover:bg-red-700",
    gray: "bg-slate-500 text-white hover:bg-slate-600"
  };

  const radius = {
    none: "rounded-none",
    sm: "rounded-sm",
    md: "rounded-md",
    xl: "rounded-xl",
    full: "rounded-full"
  };

  return (
    <button 
      className={cn(
        "font-bold transition-all active:scale-95 shadow-sm px-2 py-1 text-[11px] flex items-center justify-center leading-tight",
        variants[variant],
        radius[rounded],
        className
      )} 
      {...props}
    >
      {children}
    </button>
  );
};

// --- Input ---
export const RBSTextBox: React.FC<React.InputHTMLAttributes<HTMLInputElement>> = ({ className, ...props }) => {
  return (
    <input 
      className={cn(
        "w-full border border-slate-400 rounded-sm px-2 py-0 text-xs h-6 focus:outline-none focus:border-orange-500 bg-white",
        className
      )}
      {...props}
    />
  );
};

// --- Select ---
export const RBSSelect: React.FC<React.SelectHTMLAttributes<HTMLSelectElement>> = ({ className, children, ...props }) => {
  return (
    <select 
      className={cn(
        "w-full border border-slate-400 rounded-sm px-1 py-0 text-xs h-6 bg-white focus:outline-none focus:border-orange-500",
        className
      )}
      {...props}
    >
      {children}
    </select>
  );
}

// --- GroupBox ---
export const RBSGroupBox: React.FC<{ children: React.ReactNode; title?: string; className?: string }> = ({ children, title, className }) => {
  return (
    <div className={cn("relative border border-[#014E7F] rounded-sm mt-3 pt-4 pb-2 px-2 bg-transparent", className)}>
      {title && (
        <span className="absolute -top-2.5 left-2 bg-[#F8F9FA] px-1 text-[#014E7F] font-bold text-[11px]">
          {title}
        </span>
      )}
      {children}
    </div>
  );
};

// --- Botão Circular (Atualizado com cores da imagem) ---
interface RBSCircularBtnProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  icon?: React.ReactNode;
  variant?: 'green' | 'blue' | 'red'; // Novas variantes
  size?: string;
}

export const RBSCircularBtn: React.FC<RBSCircularBtnProps> = ({ 
  icon, 
  variant = 'green',
  size = 'w-12 h-12',
  className,
  ...props
}) => {
  const variants = {
    green: "bg-[#008000] hover:bg-green-700", // Verde Direcional/Câmera
    blue: "bg-[#014E7F] hover:bg-[#013d63]", // Azul padrão
    red: "bg-[#A52A2A] hover:bg-[#8b2323]" // Vermelho/Marrom ROI
  };

  return (
    <button 
      className={cn(
        "rounded-full flex items-center justify-center text-white shadow-lg hover:brightness-110 active:scale-90 transition-transform",
        variants[variant],
        size,
        className
      )}
      {...props}
    >
      {icon}
    </button>
  );
};

// --- Grid/Tabela ---
export const RBSGrid: React.FC<{ rows?: number }> = ({ rows = 5 }) => {
  return (
    <div className="border border-[#014E7F] bg-white text-[10px] h-full overflow-hidden flex flex-col font-bold">
      <div className="bg-[#014E7F] text-white grid grid-cols-3 p-1 text-center">
        <span className="border-r border-white/30">G90</span>
        <span className="border-r border-white/30">X</span>
        <span>Y</span>
      </div>
      <div className="overflow-y-auto flex-1 bg-white">
        {[...Array(rows)].map((_, i) => (
          <div key={i} className="grid grid-cols-3 border-b border-[#014E7F] h-5 items-center">
            <div className="border-r border-[#014E7F] h-full"></div>
            <div className="border-r border-[#014E7F] h-full"></div>
            <div></div>
          </div>
        ))}
      </div>
    </div>
  )
}
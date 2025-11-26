interface StatusCardProps {
  title: string;
  value: number | string;
  variant?: "success" | "destructive" | "default";
  subtitle?: string;
}

const StatusCard = ({ title, value, variant = "default", subtitle }: StatusCardProps) => {
  const getValueColor = () => {
    if (variant === "success") return "text-success";
    if (variant === "destructive") return "text-destructive";
    return "text-foreground";
  };

  return (
    <div className="bg-card rounded-lg p-4 border border-border">
      <h3 className="text-xs font-medium text-muted-foreground mb-2">{title}</h3>
      <p className={`text-5xl font-bold ${getValueColor()}`}>{value}</p>
      {subtitle && (
        <p className="text-[10px] text-muted-foreground mt-2 break-all leading-tight">{subtitle}</p>
      )}
    </div>
  );
};

export default StatusCard;

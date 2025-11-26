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
    <div className="bg-card rounded-lg p-6 border border-border">
      <h3 className="text-sm font-medium text-muted-foreground mb-3">{title}</h3>
      <p className={`text-6xl font-bold ${getValueColor()}`}>{value}</p>
      {subtitle && (
        <p className="text-xs text-muted-foreground mt-2 break-all">{subtitle}</p>
      )}
    </div>
  );
};

export default StatusCard;

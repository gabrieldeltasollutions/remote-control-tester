interface InfoPanelProps {
  title: string;
  content?: string;
}

const InfoPanel = ({ title, content }: InfoPanelProps) => {
  return (
    <div className="bg-card rounded-lg p-3 border border-border">
      <h3 className="text-xs font-medium text-muted-foreground mb-1">{title}</h3>
      <div className="bg-background rounded border border-input p-2 min-h-[30px]">
        <p className="text-xs text-foreground">{content || ""}</p>
      </div>
    </div>
  );
};

export default InfoPanel;

interface InfoPanelProps {
  title: string;
  content?: string;
}

const InfoPanel = ({ title, content }: InfoPanelProps) => {
  return (
    <div className="bg-card rounded-lg p-4 border border-border">
      <h3 className="text-sm font-medium text-muted-foreground mb-2">{title}</h3>
      <div className="bg-background rounded border border-input p-3 min-h-[40px]">
        <p className="text-sm text-foreground">{content || ""}</p>
      </div>
    </div>
  );
};

export default InfoPanel;

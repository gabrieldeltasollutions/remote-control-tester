const RemoteControlContainer = () => {
  return (
    <div className="grid grid-cols-4 gap-4">
      {[1, 2, 3, 4].map((num) => (
        <div
          key={num}
          className="bg-muted/50 rounded-lg h-64 border-2 border-dashed border-border flex items-center justify-center"
        >
          <span className="text-muted-foreground text-sm">Controle {num}</span>
        </div>
      ))}
    </div>
  );
};

export default RemoteControlContainer;

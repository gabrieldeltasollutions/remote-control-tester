import Sidebar from "@/components/Sidebar";
import TopBar from "@/components/TopBar";
import StatusCard from "@/components/StatusCard";
import ControlPanel from "@/components/ControlPanel";
import CameraView from "@/components/CameraView";
import RemoteControlContainer from "@/components/RemoteControlContainer";
import ImageCapture from "@/components/ImageCapture";
import InfoPanel from "@/components/InfoPanel";

const TestPage = () => {
  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      
      <div className="flex-1 flex flex-col overflow-hidden">
        <TopBar />
        
        <main className="flex-1 overflow-auto bg-background p-4">
          <div className="grid grid-cols-12 gap-4 h-full">
            {/* Left Section - Stats and Remote Controls */}
            <div className="col-span-6 space-y-4">
              {/* Stats Section */}
              <div className="bg-secondary/20 rounded-lg p-4 border border-border">
                <div className="grid grid-cols-4 gap-3 mb-4">
                  <StatusCard 
                    title="Aprovado" 
                    value={0} 
                    variant="success"
                    subtitle="Câmera 1: @device:pnp:\\?\usb#vid_5986&pid_2137&mi_00#6&27466063&0&0000 #{65e8773d-8f56-11d0-a3b9-00a0c9223196}\global"
                  />
                  <StatusCard 
                    title="Reprovado" 
                    value={0} 
                    variant="destructive" 
                  />
                  <div className="space-y-3">
                    <StatusCard 
                      title="Ciclos" 
                      value="" 
                    />
                    <div className="bg-card rounded-lg p-3 border border-border">
                      <p className="text-xs font-medium text-muted-foreground">Testados (UN.)</p>
                    </div>
                  </div>
                  <div className="space-y-3">
                    <InfoPanel title="Mensagens" />
                    <InfoPanel title="Status Home" />
                  </div>
                </div>
                
                <div className="bg-card rounded-lg p-4 border border-border">
                  <h3 className="text-sm font-medium text-muted-foreground mb-2">Tempo de Teste</h3>
                  <p className="text-4xl font-bold text-success">00:00:00</p>
                </div>
              </div>
              
              {/* Remote Control Containers */}
              <RemoteControlContainer />
            </div>
            
            {/* Right Section - Cameras and Control Panel */}
            <div className="col-span-6 grid grid-cols-12 gap-4">
              {/* Camera Views */}
              <div className="col-span-9 space-y-4">
                <CameraView cameraNumber={1} controlNumber={1} />
                <CameraView cameraNumber={2} controlNumber={2} />
                <CameraView cameraNumber={3} controlNumber={3} />
                <CameraView cameraNumber={4} controlNumber={4} />
              </div>
              
              {/* Control Panel */}
              <div className="col-span-3 flex flex-col gap-4">
                <ControlPanel />
                <ImageCapture />
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

export default TestPage;

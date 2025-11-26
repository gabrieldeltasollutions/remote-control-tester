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
        
        <main className="flex-1 overflow-auto bg-background p-6">
          <div className="grid grid-cols-12 gap-6">
            {/* Left Content Area */}
            <div className="col-span-9 space-y-6">
              {/* Camera Views */}
              <div className="grid grid-cols-2 gap-6">
                <CameraView cameraNumber={1} controlNumber={1} />
                <CameraView cameraNumber={2} controlNumber={2} />
              </div>
              
              {/* Stats Section */}
              <div className="bg-secondary/20 rounded-lg p-6 border border-border">
                <div className="grid grid-cols-4 gap-4 mb-6">
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
                  <div className="space-y-4">
                    <StatusCard 
                      title="Ciclos" 
                      value="" 
                    />
                    <div className="bg-card rounded-lg p-4 border border-border">
                      <p className="text-sm font-medium text-muted-foreground">Testados (UN.)</p>
                    </div>
                  </div>
                  <div className="space-y-4">
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
              
              {/* Camera 3 */}
              <CameraView cameraNumber={3} controlNumber={3} />
            </div>
            
            {/* Right Control Panel */}
            <div className="col-span-3 space-y-6">
              <ControlPanel />
              <ImageCapture />
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

export default TestPage;

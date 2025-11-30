import styles from '../styles/RemoteControlContainer.module.css';

interface RemoteControlContainerProps {
  testReport?: any;
}

// Mapeamento entre nomes dos botões no frontend e no backend
const buttonNameMap: { [key: string]: string } = {
  'FUNÇÃO': 'FUNCAO',
  'VELOCIDADE': 'VELOCIDADE',
  'OSCILAR': 'OSCILAR',
  'TURBO': 'TURBO',
  'CONFORTO': 'CONFORTO',
  'LIMPAR': 'LIMPAR',
  'IONAIR': 'IONAIR',
  'DORMIR': 'DORMIR',
  'VISOR': 'VISOR',
  'ANTI-MOFO': 'ANTIMORFO',
  'TEMPORIZADOR': 'TEMPORIZADOR',
  'ON/OFF': 'POWER',
};

const RemoteControlContainer: React.FC<RemoteControlContainerProps> = ({ testReport }) => {
  // Função para verificar se um botão foi aprovado
  const isButtonApproved = (controlNum: number, buttonName: string): boolean => {
    if (!testReport || !testReport.controles) return false;
    
    const controle = testReport.controles[controlNum];
    if (!controle || !controle.botoes) return false;
    
    // Mapeia o nome do botão do frontend para o backend
    const backendName = buttonNameMap[buttonName] || buttonName;
    
    // Procura o botão no relatório
    const botao = controle.botoes.find((b: any) => 
      b.nome === backendName || b.nome === buttonName
    );
    
    return botao ? botao.aprovado : false;
  };

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-6 p-6 -mt-20">
      {[1, 2, 3, 4].map((num) => (
        <div key={num} className="flex flex-col items-center">
          <div className="text-sm font-medium mb-2 text-gray-700"> </div>
           <div className="text-sm font-medium mb-2 text-gray-700"> </div>
                   <div className="text-sm font-medium mb-2 text-gray-700"> </div>

          <div className={`${styles.controle} w-full max-w-[2500px]`}>
            <div className={styles.tela}></div>

            <div className={styles.setaGrande} id={`seta-central-${num}`}>
              ▲
              <div className="h-1 w-4 bg-gray-500 rounded"></div>
              ▼
            </div>

            <div className={styles.linhaBotoes}>
              <div 
                className={`${styles.btn} ${isButtonApproved(num, 'FUNÇÃO') ? 'bg-green-500 border-green-600' : ''}`} 
                id={`btn-funcao-${num}`}
                style={isButtonApproved(num, 'FUNÇÃO') ? { backgroundColor: '#22c55e', borderColor: '#16a34a' } : {}}
              >
                FUNÇÃO
              </div>
              <div 
                className={`${styles.btn} ${isButtonApproved(num, 'VELOCIDADE') ? 'bg-green-500 border-green-600' : ''}`} 
                id={`btn-velocidade-${num}`}
                style={isButtonApproved(num, 'VELOCIDADE') ? { backgroundColor: '#22c55e', borderColor: '#16a34a' } : {}}
              >
                VELOCIDADE
              </div>
              <div 
                className={`${styles.btn} ${isButtonApproved(num, 'OSCILAR') ? 'bg-green-500 border-green-600' : ''}`} 
                id={`btn-oscilar-${num}`}
                style={isButtonApproved(num, 'OSCILAR') ? { backgroundColor: '#22c55e', borderColor: '#16a34a' } : {}}
              >
                OSCILAR
              </div>
            </div>

            <div className={styles.linhaBotoes}>
              <div 
                className={`${styles.btn} ${isButtonApproved(num, 'TURBO') ? 'bg-green-500 border-green-600' : ''}`} 
                id={`btn-turbo-${num}`}
                style={isButtonApproved(num, 'TURBO') ? { backgroundColor: '#22c55e', borderColor: '#16a34a' } : {}}
              >
                TURBO
              </div>
              <div 
                className={`${styles.btn} ${isButtonApproved(num, 'CONFORTO') ? 'bg-green-500 border-green-600' : ''}`} 
                id={`btn-conforto-${num}`}
                style={isButtonApproved(num, 'CONFORTO') ? { backgroundColor: '#22c55e', borderColor: '#16a34a' } : {}}
              >
                CONFORTO
              </div>
              <div 
                className={`${styles.btn} ${isButtonApproved(num, 'LIMPAR') ? 'bg-green-500 border-green-600' : ''}`} 
                id={`btn-limpar-${num}`}
                style={isButtonApproved(num, 'LIMPAR') ? { backgroundColor: '#22c55e', borderColor: '#16a34a' } : {}}
              >
                LIMPAR
              </div>
            </div>

            <div className={styles.linhaBotoes}>
              <div 
                className={`${styles.btn} ${isButtonApproved(num, 'IONAIR') ? 'bg-green-500 border-green-600' : ''}`} 
                id={`btn-ionair-${num}`}
                style={isButtonApproved(num, 'IONAIR') ? { backgroundColor: '#22c55e', borderColor: '#16a34a' } : {}}
              >
                IONAIR
              </div>
              <div 
                className={`${styles.btn} ${isButtonApproved(num, 'DORMIR') ? 'bg-green-500 border-green-600' : ''}`} 
                id={`btn-dormir-${num}`}
                style={isButtonApproved(num, 'DORMIR') ? { backgroundColor: '#22c55e', borderColor: '#16a34a' } : {}}
              >
                DORMIR
              </div>
              <div 
                className={`${styles.btn} ${isButtonApproved(num, 'VISOR') ? 'bg-green-500 border-green-600' : ''}`} 
                id={`btn-visor-${num}`}
                style={isButtonApproved(num, 'VISOR') ? { backgroundColor: '#22c55e', borderColor: '#16a34a' } : {}}
              >
                VISOR
              </div>
            </div>

            <div className={styles.linhaBotoes}>
              <div 
                className={`${styles.btn} ${isButtonApproved(num, 'ANTI-MOFO') ? 'bg-green-500 border-green-600' : ''}`} 
                id={`btn-antimofo-${num}`}
                style={isButtonApproved(num, 'ANTI-MOFO') ? { backgroundColor: '#22c55e', borderColor: '#16a34a' } : {}}
              >
                ANTI-MOFO
              </div>
              <div className={styles.btn} id={`btn-branco1-${num}`}></div>
              <div className={styles.btn} id={`btn-branco2}-${num}`}></div>
            </div>

            <div className={styles.linhaBotoes}>
              <div 
                className={`${styles.btn} ${isButtonApproved(num, 'TEMPORIZADOR') ? 'bg-green-500 border-green-600' : ''}`} 
                id={`btn-temporizador-${num}`}
                style={isButtonApproved(num, 'TEMPORIZADOR') ? { backgroundColor: '#22c55e', borderColor: '#16a34a' } : {}}
              >
                TEMPORIZADOR
              </div>
              <div 
                className={`${styles.btn} ${isButtonApproved(num, 'ON/OFF') ? 'bg-green-500 border-green-600' : ''}`} 
                id={`btn-power-${num}`}
                style={isButtonApproved(num, 'ON/OFF') ? { backgroundColor: '#22c55e', borderColor: '#16a34a' } : {}}
              >
                ON/OFF
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default RemoteControlContainer;

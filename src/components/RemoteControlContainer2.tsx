import styles from '../styles/RemoteControlContainer.module.css';

const RemoteControlContainer: React.FC = () => {
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
              <div className={styles.btn} id={`btn-funcao-${num}`}>FUNÇÃO</div>
              <div className={styles.btn} id={`btn-velocidade-${num}`}>VELOCIDADE</div>
              <div className={styles.btn} id={`btn-oscilar-${num}`}>OSCILAR</div>
            </div>

            <div className={styles.linhaBotoes}>
              <div className={styles.btn} id={`btn-turbo-${num}`}>TURBO</div>
              <div className={styles.btn} id={`btn-conforto-${num}`}>CONFORTO</div>
              <div className={styles.btn} id={`btn-limpar-${num}`}>LIMPAR</div>
            </div>

            <div className={styles.linhaBotoes}>
              <div className={styles.btn} id={`btn-ionair-${num}`}>IONAIR</div>
              <div className={styles.btn} id={`btn-dormir-${num}`}>DORMIR</div>
              <div className={styles.btn} id={`btn-visor-${num}`}>VISOR</div>
            </div>

            <div className={styles.linhaBotoes}>
              <div className={styles.btn} id={`btn-antimofo-${num}`}>ANTI-MOFO</div>
              <div className={styles.btn} id={`btn-branco1-${num}`}></div>
              <div className={styles.btn} id={`btn-branco2}-${num}`}></div>
            </div>

            <div className={styles.linhaBotoes}>
              <div className={styles.btn} id={`btn-temporizador-${num}`}>TEMPORIZADOR</div>
              <div className={styles.btn} id={`btn-power-${num}`}>ON/OFF</div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default RemoteControlContainer;

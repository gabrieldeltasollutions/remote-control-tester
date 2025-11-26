import { useState } from 'react';
import { RBSButton, RBSTextBox, RBSGroupBox, RBSSelect, RBSCircularBtn } from '@/components/RBSUi';
import { Image as ImageIcon, ArrowUp, ArrowDown, ArrowLeft, ArrowRight, Camera, Video, Crop, Save, Upload } from 'lucide-react';

// Componente de Grid Personalizado para o Fundo Azul Escuro
const DarkBlueGrid = () => (
  <div className="border border-[#014E7F] bg-[#003366] text-xs h-full overflow-hidden flex flex-col">
    {/* Cabeçalho Branco/Cinza */}
    <div className="bg-[#F0F0F0] text-black font-bold grid grid-cols-4 p-1 text-center border-b border-slate-400">
      <span className="border-r border-slate-300 col-span-1">G90</span>
      <span className="border-r border-slate-300 col-span-1">X</span>
      <span className="col-span-2">Y</span>
    </div>
    {/* Corpo Azul Escuro */}
    <div className="overflow-y-auto flex-1 bg-[#004080]">
      {/* Linhas vazias para simular o grid */}
      {[...Array(6)].map((_, i) => (
        <div key={i} className="border-b border-[#005599] h-6"></div>
      ))}
    </div>
  </div>
);

const Config = () => {
  const [tabLeft, setTabLeft] = useState<'Serial' | 'Controle'>('Controle');
  const [tabRight, setTabRight] = useState<'Serial' | 'Cameras'>('Cameras');
  const [tabBottom, setTabBottom] = useState<'Padrao' | 'Comparar' | 'Testar'>('Padrao');

  return (
    <div className="p-2 h-full w-full bg-[#F8F9FA] font-sans text-xs overflow-hidden flex gap-2">
      
      {/* ===================================================================================== */}
      {/* COLUNA ESQUERDA (Com scroll vertical se necessário) */}
      {/* ===================================================================================== */}
      <div className="w-[45%] flex flex-col gap-2 h-full overflow-y-auto pr-1">
        
        {/* --- PARTE SUPERIOR (ABAS) --- */}
        <div className="flex-none flex flex-col">
            <div className="flex">
                {['Serial', 'Controle'].map(t => (
                <button
                    key={t}
                    onClick={() => setTabLeft(t as any)}
                    className={`px-6 py-1 text-xs rounded-t-sm border border-b-0 ${tabLeft === t ? 'bg-white font-bold text-black z-10 -mb-[1px] border-slate-400' : 'bg-[#E1E1E1] text-slate-600 border-slate-300'}`}
                >
                    {t}
                </button>
                ))}
                <div className="flex-1 border-b border-slate-400"></div>
            </div>

            {/* CONTEÚDO DA ABA */}
            <div className="bg-white border border-slate-400 p-3 border-t-0">
                
                {/* ABA SERIAL */}
                {tabLeft === 'Serial' && (
                <div className="flex flex-col gap-2 h-[350px]">
                    <div className="grid grid-cols-4 gap-2">
                    {[1, 2, 3, 4].map(num => (
                        <div key={num} className="flex flex-col gap-1">
                        <div className="flex items-center justify-between"><label className="font-bold text-[#014E7F]">Porta {num}:</label><RBSSelect><option>COM{num}</option></RBSSelect></div>
                        <div className="flex items-center justify-between"><label className="font-bold text-[#014E7F]">Taxa:</label><RBSSelect><option>115200</option></RBSSelect></div>
                        <RBSButton className="h-6 text-[10px]">Conectar</RBSButton>
                        </div>
                    ))}
                    </div>
                    <div className="flex-1 bg-black border-2 border-slate-500 p-1 font-mono text-green-500 text-[10px] overflow-y-auto">_</div>
                    <RBSButton className="w-full">Salvar Porta/Taxa</RBSButton>
                </div>
                )}

                {/* ABA CONTROLE (LAYOUT FIEL AO PRINT) */}
                {tabLeft === 'Controle' && (
                <div className="flex gap-4 h-[350px]">
                    
                    {/* Coluna Botões Azuis (Esquerda) */}
                    <div className="w-1/3 flex flex-col gap-3">
                        {/* Bloco Home */}
                        <div className="bg-[#BFCDDB] p-2 rounded-xl flex gap-2 h-28 items-stretch shadow-sm border border-slate-300">
                            <RBSButton className="flex-1 h-full text-xs whitespace-normal leading-4" rounded="xl">Home - Todos os Eixos</RBSButton>
                            <RBSButton className="w-16 h-full text-xs whitespace-normal leading-4" rounded="xl">Libera Home</RBSButton>
                        </div>

                        {/* Bloco Ações */}
                        <div className="bg-[#BFCDDB] p-2 rounded-xl flex flex-col gap-2 shadow-sm border border-slate-300">
                            <div className="grid grid-cols-3 gap-2">
                                <RBSButton className="h-12 text-[10px] whitespace-normal leading-3" rounded="xl">Pressor Finger</RBSButton>
                                <RBSButton className="h-12 text-[10px] whitespace-normal leading-3" rounded="xl">Pistão Camera</RBSButton>
                                <RBSButton variant="darkBlue" className="h-12 text-[10px] whitespace-normal leading-3" rounded="xl">Led Off</RBSButton>
                            </div>
                            <div className="grid grid-cols-2 gap-2">
                                <RBSButton variant="darkBlue" className="h-8 text-[10px]" rounded="xl">Alimentação B1</RBSButton>
                                <RBSButton variant="darkBlue" className="h-8 text-[10px]" rounded="xl">Alimentação B2</RBSButton>
                            </div>
                        </div>

                        {/* Bloco Passos */}
                        <div className="bg-[#BFCDDB] p-3 rounded-xl shadow-sm border border-slate-300">
                            <label className="text-[11px] font-bold text-[#014E7F] block mb-1">QTD. Passos</label>
                            <input className="w-full h-10 rounded-lg border border-[#014E7F] px-2 text-lg font-bold" defaultValue="1" />
                        </div>
                    </div>

                    {/* Painel Movimentação (Direita) */}
                    <div className="flex-1 bg-[#E8E8E8] rounded-xl p-2 relative flex flex-col">
                        
                        {/* Topo: Botões Berço */}
                        <div className="flex justify-between px-2 mt-2 z-10 relative">
                            <div className="flex flex-col gap-2">
                                <RBSButton className="w-20 h-10 text-[10px] whitespace-normal leading-3" rounded="xl">Move Berço 1</RBSButton>
                                <RBSButton className="w-20 h-10 text-[10px]" rounded="xl">Pilha 1</RBSButton>
                                <RBSButton className="w-20 h-10 text-[10px] whitespace-normal leading-3" rounded="xl">Trava Berço 1</RBSButton>
                            </div>
                            <div className="flex flex-col gap-2">
                                <RBSButton className="w-20 h-10 text-[10px] whitespace-normal leading-3" rounded="xl">Move Berço 2</RBSButton>
                                <RBSButton className="w-20 h-10 text-[10px]" rounded="xl">Pilha 2</RBSButton>
                                <RBSButton className="w-20 h-10 text-[10px] whitespace-normal leading-3" rounded="xl">Trava Berço 2</RBSButton>
                            </div>
                        </div>

                        {/* Centro: Direcional */}
                        <div className="absolute top-[38%] left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-0">
                            <div className="grid grid-cols-3 grid-rows-3 gap-2 place-items-center">
                                {/* Labels */}
                                <span className="col-start-2 row-start-1 text-[#014E7F] font-bold -ml-8 text-[10px]">Y +</span>
                                <span className="col-start-3 row-start-2 text-[#014E7F] font-bold -mt-8 text-[10px]">X +</span>
                                <span className="col-start-1 row-start-2 text-[#014E7F] font-bold -mt-8 text-[10px]">X -</span>
                                <span className="col-start-2 row-start-3 text-[#014E7F] font-bold -mr-8 text-[10px]">Y -</span>

                                {/* Botões Verdes */}
                                <div className="col-start-2 row-start-1"><RBSCircularBtn variant="green" size="w-10 h-10" icon={<ArrowUp size={20} strokeWidth={3} />} /></div>
                                <div className="col-start-1 row-start-2"><RBSCircularBtn variant="green" size="w-10 h-10" icon={<ArrowLeft size={20} strokeWidth={3} />} /></div>
                                <div className="col-start-3 row-start-2"><RBSCircularBtn variant="green" size="w-10 h-10" icon={<ArrowRight size={20} strokeWidth={3} />} /></div>
                                <div className="col-start-2 row-start-3"><RBSCircularBtn variant="green" size="w-10 h-10" icon={<ArrowDown size={20} strokeWidth={3} />} /></div>
                            </div>
                        </div>

                        {/* Base: Displays X/Y */}
                        <div className="mt-auto flex flex-col gap-2 px-4 mb-2">
                            <div className="bg-[#014E7F] h-8 rounded-full flex items-center justify-between px-8 relative shadow-md border-2 border-white">
                                <span className="text-white font-bold text-lg">X {'->'}</span>
                                <span className="text-[#FFFF00] font-bold text-xl">0</span>
                            </div>
                            <div className="bg-[#014E7F] h-8 rounded-full flex items-center justify-between px-8 relative shadow-md border-2 border-white">
                                <span className="text-white font-bold text-lg">Y {'->'}</span>
                                <span className="text-[#FFFF00] font-bold text-xl">0</span>
                            </div>
                        </div>
                        <span className="text-[10px] text-[#014E7F] ml-1">Imagens serão salvas em:</span>
                    </div>
                </div>
                )}
            </div>
        </div>

        {/* --- PARTE INFERIOR (RODAPÉ - GRIDS) --- */}
        <div className="flex-1 flex flex-col gap-2">
            <div className="flex gap-2 h-full">
                
                {/* Grid Esquerda */}
                <div className="flex-1 flex flex-col gap-1">
                    <div className="flex items-center bg-[#FFA500] px-2 py-1 rounded-sm h-7">
                        <span className="font-bold text-white text-[10px] flex-1">Carregar arquivo</span>
                    </div>
                    <div className="flex gap-1 items-center">
                        <input className="flex-1 bg-[#E8E8E8] border border-slate-300 h-6 rounded-sm px-1" disabled />
                        <input type="checkbox" className="h-3 w-3" />
                        <span className="text-[10px] text-slate-600">Libera</span>
                    </div>
                    <div className="flex-1 min-h-[120px]"><DarkBlueGrid /></div>
                    <div className="flex gap-1 h-10">
                        <RBSButton variant="orange" className="flex-1 h-full text-[9px] leading-tight" rounded="none">MOVER (grade)</RBSButton>
                        <RBSButton variant="orange" className="flex-1 h-full text-[9px] leading-tight" rounded="none">SALVAR NA LINHA<br/>EXISTENTE</RBSButton>
                        <RBSButton variant="orange" className="flex-1 h-full text-[10px]" rounded="none">SALVAR</RBSButton>
                        <RBSButton variant="darkBlue" className="w-14 h-full text-[10px]" rounded="none">Fim POS</RBSButton>
                    </div>
                </div>

                {/* Grid Direita */}
                <div className="flex-1 flex flex-col gap-1">
                    <div className="flex items-center bg-[#FFA500] px-2 py-1 rounded-sm h-7">
                        <span className="font-bold text-white text-[10px] flex-1">Carregar arquivo</span>
                    </div>
                    <div className="flex gap-1 items-center">
                        <input className="flex-1 bg-[#E8E8E8] border border-slate-300 h-6 rounded-sm px-1" disabled />
                        <input type="checkbox" className="h-3 w-3" />
                        <span className="text-[10px] text-slate-600">Libera</span>
                    </div>
                    <div className="flex-1 min-h-[120px]"><DarkBlueGrid /></div>
                    <div className="flex gap-1 h-10">
                        <RBSButton variant="orange" className="flex-1 h-full text-[9px] leading-tight" rounded="none">MOVER (grade)</RBSButton>
                        <RBSButton variant="orange" className="flex-1 h-full text-[9px] leading-tight" rounded="none">SALVAR NA LINHA<br/>EXISTENTE</RBSButton>
                        <RBSButton variant="orange" className="flex-1 h-full text-[10px]" rounded="none">SALVAR</RBSButton>
                        <RBSButton variant="darkBlue" className="w-14 h-full text-[10px]" rounded="none">Fim POS</RBSButton>
                    </div>
                </div>
            </div>

            {/* Painel Arquivos (Canto Inferior) */}
            <div className="h-40 flex gap-2">
                <div className="w-64 flex flex-col h-full border border-slate-300 rounded">
                    {/* Header das Abas Pequenas */}
                    <div className="flex gap-1 text-[10px] border-b border-slate-300 bg-white px-1 pt-1">
                        {['Padrao', 'Comparar', 'Testar'].map(t => (
                            <button 
                            key={t}
                            onClick={() => setTabBottom(t as any)}
                            className={`px-2 py-1 ${tabBottom === t ? 'bg-white border border-b-0 border-slate-300 -mb-[1px] font-bold text-[#014E7F]' : 'bg-slate-100 text-slate-500 hover:bg-slate-200'}`}
                            >
                            {t === 'Testar' ? 'Testar comparação' : t}
                            </button>
                        ))}
                    </div>

                    {/* Conteúdo das Abas */}
                    <div className="bg-[#F0F0F0] p-2 flex-1 flex flex-col gap-2 overflow-hidden">
                        
                        {/* === ABA PADRÃO === */}
                        {tabBottom === 'Padrao' && (
                            <div className="flex gap-2 h-full">
                                <div className="w-1/2 bg-white border border-slate-300 h-full"></div>
                                <div className="w-1/2 flex flex-col gap-2">
                                    <div className="flex items-center gap-1">
                                        <input type="checkbox" className="h-3 w-3" />
                                        <span className="text-[9px] text-teal-600 font-bold">Diretório PADRÃO</span>
                                    </div>
                                    <RBSButton variant="darkBlue" className="w-full text-[9px] h-7" rounded="xl">Diretório Padrão</RBSButton>
                                    <RBSButton variant="darkBlue" className="w-full text-[9px] h-7" rounded="xl">Editar Arquivos</RBSButton>
                                    <RBSButton variant="darkBlue" className="w-full text-[9px] h-7" rounded="xl">Atualizar lista</RBSButton>
                                    <div className="mt-auto">
                                        <label className="text-[9px] text-[#014E7F]">Nome da Imagem</label>
                                        <RBSTextBox className="h-6 border-[#014E7F]" />
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* === ABA COMPARAR (Layout da Imagem 1) === */}
                        {tabBottom === 'Comparar' && (
                            <div className="flex gap-2 h-full">
                                {/* Lista vazia esquerda */}
                                <div className="w-1/2 bg-white border border-slate-300 h-full overflow-y-auto p-1">
                                    {/* Itens da lista apareceriam aqui */}
                                </div>
                                {/* Controles direita */}
                                <div className="w-1/2 flex flex-col gap-2">
                                    <div className="flex items-center gap-1">
                                        <input type="checkbox" className="h-3 w-3" />
                                        <span className="text-[9px] text-teal-600 font-bold">Diretório COMPARAR</span>
                                    </div>
                                    <RBSButton variant="darkBlue" className="w-full text-[9px] h-7" rounded="xl">Dir. Comparar</RBSButton>
                                    <RBSButton variant="darkBlue" className="w-full text-[9px] h-7" rounded="xl">Editar Arquivos</RBSButton>
                                    <RBSButton variant="darkBlue" className="w-full text-[9px] h-7" rounded="xl">Atualizar lista</RBSButton>
                                    <div className="mt-auto">
                                        <label className="text-[9px] text-[#014E7F]">Nome da Imagem</label>
                                        <RBSTextBox className="h-6 border-[#014E7F]" />
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* === ABA TESTAR COMPARAÇÃO (Layout da Imagem 2) === */}
                        {tabBottom === 'Testar' && (
                            <div className="flex flex-col gap-1 h-full justify-between py-1">
                                {/* Linha 1 */}
                                <div className="flex justify-between items-start">
                                    <div className="flex flex-col">
                                        <span className="text-[#014E7F] text-[10px] font-bold">Escolher o diretório com os Padrões</span>
                                        <span className="text-slate-500 text-[9px] italic">Caminho diretório</span>
                                    </div>
                                    <RBSButton variant="darkBlue" className="w-20 h-6 text-[9px]" rounded="xl">Caminho</RBSButton>
                                </div>

                                {/* Linha 2 */}
                                <div className="flex justify-between items-start mt-1">
                                    <div className="flex flex-col">
                                        <span className="text-[#014E7F] text-[10px] font-bold">Escolher o diretório do Teste</span>
                                        <span className="text-slate-500 text-[9px] italic">Caminho diretório</span>
                                    </div>
                                    <RBSButton variant="darkBlue" className="w-20 h-6 text-[9px]" rounded="xl">Caminho</RBSButton>
                                </div>

                                {/* Botão Grande */}
                                <div className="mt-auto">
                                    <RBSButton variant="darkBlue" className="w-full h-10 text-[11px]" rounded="xl">Iniciar a comparação</RBSButton>
                                </div>
                            </div>
                        )}

                    </div>
                </div>
                
                {/* Botão Espelhar (Opcional, se estiver no layout original) */}
                <div className="flex-1"></div> 
            </div>
        </div>

      </div>

      {/* ===================================================================================== */}
      {/* COLUNA DIREITA (55% da tela) - SERIAL / CAMERAS */}
      {/* ===================================================================================== */}
      <div className="w-[55%] flex flex-col h-full">
           <div className="flex">
              {['Serial', 'Cameras'].map(t => (
                <button
                  key={t}
                  onClick={() => setTabRight(t as any)}
                  className={`px-4 py-1 text-xs rounded-t-sm border border-b-0 ${tabRight === t ? 'bg-white font-bold text-black z-10 -mb-[1px] border-slate-400' : 'bg-[#E1E1E1] text-slate-600 border-slate-300'}`}
                >
                  {t === 'Cameras' ? 'Câmeras' : t}
                </button>
              ))}
              <div className="flex-1 border-b border-slate-400"></div>
           </div>

           <div className="bg-white border border-slate-400 p-2 flex-1 flex gap-2 border-t-0 overflow-hidden">
              
              {/* --- ABA SERIAL DIREITA --- */}
              {tabRight === 'Serial' && (
                <div className="flex-1 flex gap-2 overflow-hidden">
                  <div className="flex-1 flex flex-col gap-1 overflow-y-auto pr-2">
                    
                    <RBSGroupBox title="Enviar Comandos {Acionamentos} - Serial 1">
                      <div className="flex flex-col gap-1">
                        <input className="w-full bg-[#BFCDDB] border-none h-6 text-xs px-1 outline-none font-bold text-[#014E7F]" />
                        <div className="h-24 bg-[#014E7F] w-full border border-[#003355]"></div>
                        <div className="flex justify-between mt-1">
                          <RBSButton variant="orange" className="w-28 text-[10px]">Teclado Virtual</RBSButton>
                          <div className="flex gap-1">
                            <RBSButton variant="orange" className="w-16 text-[10px]">Limpar</RBSButton>
                            <RBSButton variant="orange" className="w-16 text-[10px]">Enviar</RBSButton>
                          </div>
                        </div>
                      </div>
                    </RBSGroupBox>

                    <RBSGroupBox title="Enviar Comandos {Motores} - Serial 2">
                      <div className="flex flex-col gap-1">
                        <input className="w-full bg-[#BFCDDB] border-none h-6 text-xs px-1 outline-none font-bold text-[#014E7F]" />
                        <div className="h-24 bg-[#014E7F] w-full border border-[#003355]"></div>
                        <div className="flex justify-between mt-1">
                          <RBSButton variant="orange" className="w-28 text-[10px]">Parâmetros GRBL</RBSButton>
                          <div className="flex gap-1">
                            <RBSButton variant="orange" className="w-16 text-[10px]">Limpar</RBSButton>
                            <RBSButton variant="orange" className="w-16 text-[10px]">Enviar</RBSButton>
                          </div>
                        </div>
                      </div>
                    </RBSGroupBox>

                    <RBSGroupBox title="Enviar Comandos {IR} - Serial 3">
                      <div className="flex flex-col gap-1">
                        <input className="w-full bg-[#BFCDDB] border-none h-6 text-xs px-1 outline-none font-bold text-[#014E7F]" />
                        <div className="h-24 bg-[#014E7F] w-full border border-[#003355]"></div>
                        <div className="flex justify-end gap-1 mt-1">
                          <RBSButton variant="orange" className="w-16 text-[10px]">Limpar</RBSButton>
                          <RBSButton variant="orange" className="w-16 text-[10px]">Enviar</RBSButton>
                        </div>
                      </div>
                    </RBSGroupBox>

                    <RBSGroupBox title="Enviar Comandos {IR} - Serial 4">
                      <div className="flex flex-col gap-1">
                        <input className="w-full bg-[#BFCDDB] border-none h-6 text-xs px-1 outline-none font-bold text-[#014E7F]" />
                        <div className="h-24 bg-[#014E7F] w-full border border-[#003355]"></div>
                        <div className="flex justify-end gap-1 mt-1">
                          <RBSButton variant="orange" className="w-16 text-[10px]">Limpar</RBSButton>
                          <RBSButton variant="orange" className="w-16 text-[10px]">Enviar</RBSButton>
                        </div>
                      </div>
                    </RBSGroupBox>
                  </div>

                  <div className="w-40 flex flex-col items-center justify-center border border-slate-200 bg-slate-50 relative">
                     <div className="absolute top-2 right-2 text-[#014E7F]"><ImageIcon /></div>
                     <div className="text-slate-400 text-center px-4">
                        <div className="h-64 w-16 border border-slate-300 rounded-full mx-auto flex items-center justify-center bg-white shadow-sm">
                           <span className="text-[10px]">Controle</span>
                        </div>
                     </div>
                  </div>
                </div>
              )}

              {/* --- ABA CÂMERAS --- */}
              {tabRight === 'Cameras' && (
                <div className="flex-1 flex flex-col h-full">
                  <div className="flex-1 flex gap-2 min-h-0">
                    <div className="flex-1 grid grid-cols-2 grid-rows-2 gap-2">
                      <div className="bg-[#DDEEFF] border border-slate-300 p-1 text-[#014E7F]">Câmera 1</div>
                      <div className="bg-[#DDEEFF] border border-slate-300 p-1 text-[#014E7F]">Câmera 2</div>
                      <div className="bg-[#DDEEFF] border border-slate-300 p-1 text-[#014E7F]">Câmera 3</div>
                      <div className="bg-[#DDEEFF] border border-slate-300 p-1 text-[#014E7F]">Câmera 4</div>
                    </div>

                    <div className="w-20 flex flex-col items-center gap-4 py-2">
                       <div className="flex flex-col items-center gap-1">
                          <RBSCircularBtn variant="green" size="w-12 h-12" icon={<Crop size={20} />} />
                          <span className="text-[10px] text-center leading-tight text-[#014E7F]">Salvar ROI</span>
                       </div>
                       <div className="flex flex-col items-center gap-1">
                          <RBSCircularBtn variant="green" size="w-12 h-12" icon={<Camera size={20} />} />
                          <span className="text-[10px] text-center leading-tight text-[#014E7F]">Captura Imagem</span>
                       </div>
                       <div className="flex flex-col items-center gap-1">
                          <RBSCircularBtn variant="green" size="w-12 h-12" icon={<Video size={20} />} />
                          <span className="text-[10px] text-center leading-tight text-[#014E7F]">Iniciar Câmeras</span>
                       </div>
                       
                       <div className="mt-auto flex flex-col gap-2 items-center">
                          <div className="flex flex-col items-center gap-1">
                             <RBSCircularBtn variant="red" size="w-12 h-12" icon={<Crop size={20} />} />
                             <span className="text-[10px] text-center leading-tight text-[#014E7F]">ROI 1</span>
                          </div>
                          <div className="flex flex-col items-center gap-1">
                             <RBSCircularBtn variant="red" size="w-12 h-12" icon={<Crop size={20} />} />
                             <span className="text-[10px] text-center leading-tight text-[#014E7F]">ROI 2</span>
                          </div>
                       </div>
                    </div>
                  </div>

                  {/* Busca de Guias */}
                  <div className="h-24 mt-2 flex gap-2 text-[10px]">
                    <div className="flex-1 flex flex-col gap-1">
                       <span className="text-[#014E7F]">Buscar guia das Câmeras 1</span>
                       <div className="flex gap-1"><RBSTextBox placeholder="G90 X0 Y110.000" /><RBSButton className="w-28 h-6" variant="darkBlue">Do ponto 1 ao 2</RBSButton></div>
                       <span className="text-[#014E7F] mt-1">Buscar guia das Câmeras 2</span>
                       <div className="flex gap-1"><RBSTextBox placeholder="G90 X362.296 Y110.000" /><RBSButton className="w-28 h-6" variant="darkBlue">Do ponto 2 ao 1</RBSButton></div>
                    </div>
                    <div className="w-48 flex flex-col gap-1">
                       <span className="text-[#014E7F]">% Similaridade</span>
                       <div className="flex gap-1">
                          <RBSTextBox className="text-center" placeholder="90" />
                          <RBSTextBox className="text-center" placeholder="90" />
                          <RBSTextBox className="text-center" placeholder="90" />
                          <RBSTextBox className="text-center" placeholder="90" />
                       </div>
                       <RBSButton className="w-full h-6 mt-1" variant="darkBlue">Definir valor Similaridade</RBSButton>
                    </div>
                  </div>
                </div>
              )}
           </div>
        </div>

    </div>
  );
};

export default Config;
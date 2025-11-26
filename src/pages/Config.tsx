import { useState } from 'react';
import { RBSButton, RBSTextBox, RBSGroupBox, RBSGrid, RBSSelect, RBSCircularBtn } from '@/components/RBSUi';
import { Image as ImageIcon, ArrowUp, ArrowDown, ArrowLeft, ArrowRight, Camera, Video, Crop, Save, Settings, Upload } from 'lucide-react';

const Config = () => {
  const [tabLeft, setTabLeft] = useState<'Serial' | 'Controle'>('Serial');
  const [tabRight, setTabRight] = useState<'Serial' | 'Cameras'>('Cameras');
  const [tabBottom, setTabBottom] = useState<'Padrao' | 'Comparar' | 'Testar'>('Padrao');

  return (
    <div className="p-2 h-full w-full bg-[#F8F9FA] font-sans text-xs overflow-hidden flex gap-2">
      
      {/* ===================================================================================== */}
      {/* COLUNA ESQUERDA (45% da tela) - Contém: Abas Superiores + GRADES/RODAPÉ */}
      {/* ===================================================================================== */}
      <div className="w-[45%] flex flex-col gap-2 h-full">
        
        {/* --- PARTE SUPERIOR ESQUERDA (ABAS) --- */}
        <div className="flex-none h-[450px] flex flex-col">
            <div className="flex">
                {['Serial', 'Controle'].map(t => (
                <button
                    key={t}
                    onClick={() => setTabLeft(t as any)}
                    className={`px-4 py-1 border border-b-0 text-xs ${tabLeft === t ? 'bg-white border-slate-400 font-bold text-black z-10 -mb-[1px]' : 'bg-slate-200 text-slate-500 border-slate-300'}`}
                >
                    {t}
                </button>
                ))}
                <div className="flex-1 border-b border-slate-400"></div>
            </div>

            {/* Conteúdo da Aba Superior Esquerda */}
            <div className="bg-white border border-slate-400 p-2 flex-1 flex flex-col gap-2 border-t-0 overflow-y-auto">
                
                {/* CONTEÚDO: SERIAL */}
                {tabLeft === 'Serial' && (
                <>
                    <div className="grid grid-cols-4 gap-2">
                    {[1, 2, 3, 4].map(num => (
                        <div key={num} className="flex flex-col gap-1">
                        <div className="flex items-center justify-between">
                            <label className="font-bold text-[#014E7F]">Porta {num}:</label>
                            <RBSSelect><option>COM{num}</option></RBSSelect>
                        </div>
                        <div className="flex items-center justify-between">
                            <label className="font-bold text-[#014E7F]">Taxa:</label>
                            <RBSSelect><option>115200</option></RBSSelect>
                        </div>
                        <RBSButton className="h-6 text-[10px]">Conectar</RBSButton>
                        </div>
                    ))}
                    </div>
                    <div className="flex-1 bg-black border-2 border-slate-500 p-1 font-mono text-green-500 text-[10px] overflow-y-auto">_</div>
                    <RBSButton className="w-full">Salvar Porta/Taxa</RBSButton>
                </>
                )}

                {/* CONTEÚDO: CONTROLE */}
                {tabLeft === 'Controle' && (
                <div className="flex gap-2 h-full">
                    <div className="w-1/3 flex flex-col gap-2">
                        <div className="bg-[#BFCDDB] p-2 rounded-md flex gap-2 h-24">
                            <RBSButton className="flex-1 h-full text-xs" rounded="md">Home - Todos os Eixos</RBSButton>
                            <RBSButton className="w-16 h-full text-xs" rounded="md">Libera Home</RBSButton>
                        </div>
                        <div className="bg-[#BFCDDB] p-2 rounded-md grid grid-cols-2 gap-2">
                            <RBSButton className="text-[10px] h-10" rounded="md">Pressor Finger</RBSButton>
                            <RBSButton className="text-[10px] h-10" rounded="md">Pistão Câmera</RBSButton>
                            <RBSButton variant="darkBlue" className="text-[10px] h-8" rounded="md">Alimentação B1</RBSButton>
                            <RBSButton variant="darkBlue" className="text-[10px] h-8" rounded="md">Alimentação B2</RBSButton>
                            <div className="col-span-2 flex justify-center">
                                <RBSButton variant="darkBlue" className="text-[10px] w-20 h-8" rounded="md">Led Off</RBSButton>
                            </div>
                        </div>
                        <div className="bg-[#BFCDDB] p-2 rounded-md">
                            <label className="text-[10px] font-bold text-[#014E7F]">QTD. Passos</label>
                            <RBSTextBox defaultValue="1" className="h-8 text-base font-bold" />
                        </div>
                    </div>

                    <div className="flex-1 flex flex-col gap-2 relative">
                        <div className="flex justify-between px-4 z-10 relative">
                            <div className="flex flex-col gap-2">
                                <RBSButton className="w-20 h-10 text-[10px]" rounded="md">Move Berço 1</RBSButton>
                                <RBSButton className="w-20 h-10 text-[10px]" rounded="md">Pilha 1</RBSButton>
                                <RBSButton className="w-20 h-10 text-[10px]" rounded="md">Trava Berço 1</RBSButton>
                            </div>
                            <div className="flex flex-col gap-2">
                                <RBSButton className="w-20 h-10 text-[10px]" rounded="md">Move Berço 2</RBSButton>
                                <RBSButton className="w-20 h-10 text-[10px]" rounded="md">Pilha 2</RBSButton>
                                <RBSButton className="w-20 h-10 text-[10px]" rounded="md">Trava Berço 2</RBSButton>
                            </div>
                        </div>

                        <div className="absolute top-[35%] left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-0">
                            <div className="grid grid-cols-3 grid-rows-3 gap-1 place-items-center">
                                <span className="col-start-2 row-start-1 text-[#014E7F] font-bold">Y +</span>
                                <span className="col-start-2 row-start-3 text-[#014E7F] font-bold">Y -</span>
                                <span className="col-start-1 row-start-2 text-[#014E7F] font-bold mr-8">X -</span>
                                <span className="col-start-3 row-start-2 text-[#014E7F] font-bold ml-8">X +</span>

                                <div className="col-start-2 row-start-1 mt-4"><RBSCircularBtn variant="green" size="w-12 h-12" icon={<ArrowUp size={24} />} /></div>
                                <div className="col-start-1 row-start-2 mr-4"><RBSCircularBtn variant="green" size="w-12 h-12" icon={<ArrowLeft size={24} />} /></div>
                                <div className="col-start-3 row-start-2 ml-4"><RBSCircularBtn variant="green" size="w-12 h-12" icon={<ArrowRight size={24} />} /></div>
                                <div className="col-start-2 row-start-3 mb-4"><RBSCircularBtn variant="green" size="w-12 h-12" icon={<ArrowDown size={24} />} /></div>
                            </div>
                        </div>

                        <div className="mt-auto flex flex-col gap-2">
                            <div className="bg-[#014E7F] h-10 rounded-full flex items-center justify-between px-6 relative">
                                <span className="text-white font-bold text-xl absolute left-1/3 transform -translate-x-1/2">X {'->'}</span>
                                <span className="text-[#FFA500] font-bold text-2xl absolute right-10">0</span>
                            </div>
                            <div className="bg-[#014E7F] h-10 rounded-full flex items-center justify-between px-6 relative">
                                <span className="text-white font-bold text-xl absolute left-1/3 transform -translate-x-1/2">Y {'->'}</span>
                                <span className="text-[#FFA500] font-bold text-2xl absolute right-10">0</span>
                            </div>
                        </div>
                        <span className="text-[10px] text-[#014E7F] mt-1">Imagens serão salvas em:</span>
                    </div>
                </div>
                )}
            </div>
        </div>

        {/* --- PARTE INFERIOR ESQUERDA (RODAPÉ / GRADES) --- */}
        {/* MOVIDO PARA DENTRO DA COLUNA DA ESQUERDA */}
        <div className="flex-1 flex flex-col mt-2 bg-white p-2 border border-slate-300 rounded-md overflow-hidden">
            {/* Área das tabelas e abas */}
            <div className="flex gap-2 h-full">
                {/* Tabela Esquerda */}
                <div className="flex-1 flex flex-col gap-1">
                    <div className="flex items-center justify-between bg-[#FFA500] px-2 py-1 rounded-sm">
                        <span className="font-bold text-white flex items-center gap-1"><Upload size={12}/> Carregar arquivo</span>
                        <div className="flex items-center gap-1 bg-white px-1 rounded-sm"><input type="checkbox" className="h-3 w-3" /><span className="text-[10px]">Libera</span></div>
                    </div>
                    <div className="flex gap-1"><RBSTextBox disabled className="bg-slate-100" /></div>
                    <div className="flex-1 min-h-0"><RBSGrid rows={5} /></div>
                    <div className="flex gap-1">
                        <RBSButton variant="orange" className="flex-1 h-10 leading-3 text-[9px]">MOVER<br/>(grade)</RBSButton>
                        <RBSButton variant="orange" className="flex-1 h-10 leading-3 text-[9px]">SALVAR NA LINHA<br/>EXISTENTE</RBSButton>
                        <RBSButton variant="orange" className="flex-1 h-10 text-[10px]">SALVAR</RBSButton>
                        <RBSButton variant="darkBlue" className="w-12 h-10 text-[10px]">Fim POS</RBSButton>
                    </div>
                </div>

                {/* Tabela Direita */}
                <div className="flex-1 flex flex-col gap-1">
                    <div className="flex items-center justify-between bg-[#FFA500] px-2 py-1 rounded-sm">
                        <span className="font-bold text-white flex items-center gap-1"><Upload size={12}/> Carregar arquivo</span>
                        <div className="flex items-center gap-1 bg-white px-1 rounded-sm"><input type="checkbox" className="h-3 w-3" /><span className="text-[10px]">Libera</span></div>
                    </div>
                    <div className="flex gap-1"><RBSTextBox disabled className="bg-slate-100" /></div>
                    <div className="flex-1 min-h-0"><RBSGrid rows={5} /></div>
                    <div className="flex gap-1">
                        <RBSButton variant="orange" className="flex-1 h-10 leading-3 text-[9px]">MOVER<br/>(grade)</RBSButton>
                        <RBSButton variant="orange" className="flex-1 h-10 leading-3 text-[9px]">SALVAR NA LINHA<br/>EXISTENTE</RBSButton>
                        <RBSButton variant="orange" className="flex-1 h-10 text-[10px]">SALVAR</RBSButton>
                        <RBSButton variant="darkBlue" className="w-12 h-10 text-[10px]">Fim POS</RBSButton>
                    </div>
                </div>
            </div>

            {/* Painel de Abas Inferior (Arquivos) */}
            <div className="mt-2 h-48 flex gap-2">
                <div className="w-64 flex flex-col h-full">
                    <div className="flex gap-1 text-[10px] border-b border-slate-300 mb-1">
                        {['Padrao', 'Comparar', 'Testar'].map(t => (
                            <button 
                            key={t}
                            onClick={() => setTabBottom(t as any)}
                            className={`px-1 ${tabBottom === t ? 'font-bold text-[#014E7F] border-b-2 border-blue-800' : 'text-gray-500'}`}
                            >
                            {t}
                            </button>
                        ))}
                    </div>
                    <div className="bg-[#F0F0F0] p-2 flex-1 border border-slate-300 flex flex-col gap-2">
                        {tabBottom === 'Padrao' && (
                            <>
                            <div className="flex items-center gap-1">
                                <input type="checkbox" className="h-3 w-3" />
                                <span className="text-[10px] text-teal-600 font-bold">Diretório PADRÃO</span>
                            </div>
                            <RBSButton variant="blue" className="w-full text-[10px] h-6">Diretório Padrão</RBSButton>
                            <RBSButton variant="blue" className="w-full text-[10px] h-6">Editar Arquivos</RBSButton>
                            <RBSButton variant="blue" className="w-full text-[10px] h-6">Atualizar lista</RBSButton>
                            <div className="mt-auto">
                                <label className="text-[9px] text-[#014E7F]">Nome da Imagem</label>
                                <RBSTextBox className="h-6" />
                            </div>
                            </>
                        )}
                    </div>
                </div>
                
                {/* Espaço em branco ou Botão Espelhar se quiser colocar aqui */}
                <div className="flex-1"></div>
            </div>
        </div>

      </div>

      {/* ===================================================================================== */}
      {/* COLUNA DIREITA (55% da tela) - Altura Total - SERIAL / CAMERAS */}
      {/* ===================================================================================== */}
      <div className="w-[55%] flex flex-col h-full">
           <div className="flex">
              {['Serial', 'Cameras'].map(t => (
                <button
                  key={t}
                  onClick={() => setTabRight(t as any)}
                  className={`px-4 py-1 border border-b-0 text-xs ${tabRight === t ? 'bg-white border-slate-400 font-bold text-black z-10 -mb-[1px]' : 'bg-slate-200 text-slate-500 border-slate-300'}`}
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

                  {/* Busca de Guias (Só aparece em Câmeras) */}
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
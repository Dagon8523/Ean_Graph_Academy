import { conversationMessage, deleteConversation } from '../api/endpoints.js';
import { toItem, toRelations, toSource } from './adapters.js';
let latest = null, catalog = new Map(), edges = [];
const categories = [['educacion_continuada','continuing_education','Educación Continuada'],['programas_directos','official_program','Programas oficiales'],['programas_por_unidades','official_program','Programas por unidades'],['unidades_estudio','study_unit','Unidades de estudio'],['eanx','eanx','EAN X']];
const kindOf = t => ({Formacion:'continuing_education',ProgramaOficial:'official_program',UnidadEstudio:'study_unit',FormacionEANX:'eanx',CursoEANX:'eanx'}[t] || 'eanx');
const idOf = (k,id) => `${k}:${id}`;
function normalize(r,kind){
 const natural=r.programa_id||r.formacion_id||r.unidad_id||r.id;
 const it=toItem({id:idOf(kind,natural),kind,name:r.nombre||r.descripcion_abreviada||r.distincion_genero||natural,attributes:{code:natural,modality:r.modalidad,level:r.nivel_formacion,snies_descripcion_abreviada:r.descripcion_abreviada,snies_distincion_genero:r.distincion_genero},reason:r.origen==='COINCIDENCIA_POR_UNIDAD'?'Encontrado mediante una unidad coincidente.':'Coincidencia recuperada en el catálogo.',source:{id:kind,name:categories.find(c=>c[1]===kind)?.[2],origin:'API · grafo institucional'},program:r.programas?.length?{id:idOf('official_program',r.programas[0].programa_id),name:r.programas[0].nombre,link_type:'code'}:null,units:(r.unidades_coincidentes||[]).map(u=>({id:idOf('study_unit',u.unidad_id),kind:'study_unit',name:u.nombre,attributes:{code:u.unidad_id},program:{id:idOf(kind,natural),name:r.descripcion_abreviada,link_type:'code'}}))});
 const attr=(key,label,value)=>({key,label,value,missing:value==null||value===''});
 if(kind==='continuing_education')it.attributes=[attr('disponibilidad','Disponibilidad',({SIN_OFERTA_DISPONIBLE:'Sin oferta disponible',PROXIMA:'Próxima',VIGENTE:'Vigente'}[r.disponibilidad]||r.disponibilidad)),attr('eventos_vigentes','Eventos vigentes',r.eventos_vigentes),attr('proxima_fecha','Próxima fecha',r.proxima_fecha),attr('ultima_fecha','Última fecha registrada',r.ultima_fecha),attr('code','Código',natural)];
 if(kind==='eanx')it.attributes=[attr('descripcion','Descripción',r.descripcion),attr('code','Código',natural)];
 if(r.estado)it.attributes.push(attr('estado','Estado',r.estado));
 if(r.snies_codigo)it.attributes.push(attr('snies','SNIES',r.snies_codigo));
 it.hasMissing=it.attributes.some(a=>a.missing);it.raw=r;return it;
}
function node(n){const kind=kindOf(n.tipo),id=idOf(kind,n.id);if(!catalog.has(id))catalog.set(id,normalize({...n,id:n.id},kind));return{id,name:n.nombre||catalog.get(id).name,kind};}
export function resetResults(id){latest=null;catalog=new Map();edges=[];if(id)deleteConversation(id).catch(()=>{});}
export const assistantService={async send({message, conversationId}){
 const goal=message?.trim();if(!goal||goal.length>2000)throw new Error('Escribe un mensaje de entre 1 y 2000 caracteres.');
 const turn=await conversationMessage({message:goal,conversation_id:conversationId||null});
 const profileLabels={learning_goal:'Interés académico',experience:'Experiencia',age:'Edad',education:'Estudios',objective:'Objetivo'};
 const profileCriteria=Object.entries(turn.profile).filter(([,v])=>v!==null).map(([key,value])=>({key,label:profileLabels[key],value:String(value)}));
 const extra={conversationId:turn.conversation_id,text:turn.text,profile:turn.profile,jobs:turn.jobs,jobsStatus:turn.jobs_status,notices:turn.notices.map(text=>({text}))};
 const r=turn.academic;
 if(!r){latest=null;edges=[];return{...extra,clarifications:[],criteria:profileCriteria,results:[],relatedUnits:[],sources:[],trace:null};}
 latest=r;edges=[];
 const results=[],relatedUnits=[];
 for(const[key,kind]of categories)for(const row of r[key]?.resultados||[]){const it=normalize(row,kind);if(![...results,...relatedUnits].some(existing=>existing.id===it.id))(kind==='study_unit'?relatedUnits:results).push(it);catalog.set(it.id,it);it.units.forEach(u=>catalog.set(u.id,u));}
 for(const row of r.ruta_academica?.ofertas_continuada_relacionadas||[]){const it=normalize(row,'continuing_education');catalog.set(it.id,it);}
 for(const rel of r.ruta_academica?.relaciones_estructurales||[])edges.push({from:node(rel.destino),to:node(rel.origen),type:'BELONGS_TO',evidence:rel.relacion});
 for(const path of r.ruta_academica?.recorridos||[]){const ns=path.nodos.map(node);(path.conexiones||[]).forEach((c,i)=>{if(ns[i]&&ns[i+1])edges.push({from:ns[i],to:ns[i+1],type:'AFFINITY',evidence:c,note:`${c.naturaleza} · similitud ${Number(c.similitud).toFixed(3)}`});});}
 return{...extra,clarifications:[],criteria:profileCriteria,results,relatedUnits,sources:categories.map(([key,kind,name])=>({id:key,kind,name,origin:`${r[key]?.total??0} resultados · ${r[key]?.modo_busqueda}`})),notices:[...extra.notices,...(r.ruta_academica?.observaciones||[]).map(text=>({text}))],trace:null};
}};
export const catalogService={async getItem(id){const it=catalog.get(id);if(!it)throw new Error('Haz una consulta para recuperar este registro.');return it;},async getRelations(id){return toRelations({relations:edges.filter(r=>r.from.id===id||r.to.id===id)});}};
export const routeService={async suggest(){if(!latest)throw new Error('Primero escribe tu objetivo en la conversación para recuperar la ruta.');return{goal:latest.entrada,academic:latest.ruta_academica,paths:(latest.ruta_academica.recorridos||[]).map(p=>({...p,nodes:p.nodos.map(n=>catalog.get(idOf(kindOf(n.tipo),n.id))),relations:toRelations({relations:p.conexiones.map((c,i)=>({from:node(p.nodos[i]),to:node(p.nodos[i+1]),type:'AFFINITY',note:c.naturaleza,evidence:c}))})})),structural:toRelations({relations:edges.filter(e=>e.type==='BELONGS_TO')})};}};
export const sourcesService={async list(){if(!latest)throw new Error('Primero realiza una consulta para ver los catálogos consultados.');return categories.map(([key,,name])=>toSource({id:key,name,type:'catalog',origin:`${latest[key]?.total??0} resultados recuperados · ${latest[key]?.modo_busqueda}`,status:'available'}));}};

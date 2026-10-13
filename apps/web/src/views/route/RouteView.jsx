import { useEffect, useState } from 'react';
import { Button, Callout, ErrorNotice, Tabs, TypePill } from '../../common/ui/index.jsx';
import { routeService } from '../../services/assistantService.js';
import { RelationsGraph } from '../graph.jsx';
export function RouteView() {
 const [s,set]=useState({status:'loading'}),[mode,setMode]=useState('list');
 const load=()=>{routeService.suggest().then(route=>set({status:'done',route})).catch(error=>set({status:'error',error}));};
 useEffect(load,[]);
 return <section className="view"><div className="page-head"><div className="tblock"><span className="kicker">Mi ruta formativa · exploratoria</span><h2>tu ruta formativa</h2><p>Conexiones recuperadas para tu objetivo. No establecen un orden de prerrequisitos.</p></div><Tabs label="Formato de la ruta" value={mode} onChange={setMode} options={[{value:'list',label:'Recorridos',icon:'list'},{value:'graph',label:'Grafo',icon:'graph'}]}/></div>
 {s.status==='error'?<><ErrorNotice error={s.error} onRetry={load}/><Button as="a" href="#/conversacion">Ir a la conversación</Button></>:null}
 {s.status==='done'?<div className="route"><div><div className="goal"><span className="tblock"><small>Objetivo declarado</small><b>{s.route.goal}</b></span></div>
 {!s.route.paths.length?<Callout>No se recuperaron recorridos para esta consulta.</Callout>:null}
 {s.route.paths.map((path,i)=><div className="card route-path" key={i}><span className="kicker">Recorrido {i+1} · {path.saltos} saltos</span>{mode==='graph'?<RelationsGraph relations={path.relations} title={`Recorrido ${i+1}`}/>:<div className="mini-list">{path.nodes.map((n,j)=><div key={`${n.id}-${j}`}><div className="row"><TypePill pill={n.pill}>{n.kindLabel}</TypePill><b>{n.name}</b><Button size="sm" as="a" href={`#/detalle/${n.id}`}>Ver detalle</Button></div>{path.conexiones[j]?<p className="why">Afinidad temática · similitud {Number(path.conexiones[j].similitud).toFixed(3)} · {path.conexiones[j].validada?'validada':'sin validar'}</p>:null}</div>)}</div>}{path.usa_representante_textual?<p className="g-note">El recorrido utiliza un representante textual del registro consultado.</p>:null}</div>)}
 {s.route.structural.length?<div className="card"><h3>vínculos entre programas y unidades</h3><RelationsGraph relations={s.route.structural} title="Relaciones estructurales recuperadas"/></div>:null}
 </div><aside><div className="card"><span className="kicker">Consulta real</span><h3>conexiones académicas</h3><p>{s.route.academic.total_recorridos} recorridos recuperados.</p><p>{s.route.academic.total_conexiones_recuperadas} conexiones recuperadas.</p>{(s.route.academic.observaciones||[]).map((o,i)=><p className="muted" key={i}>{o}</p>)}</div></aside></div>:null}</section>;
}

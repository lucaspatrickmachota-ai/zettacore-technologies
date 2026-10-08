const KEY="zettacore-client-hub-v1";
let items=[];
let filter="all",market="ALL",editing=null;

const $=s=>document.querySelector(s);
const $$=s=>[...document.querySelectorAll(s)];
const save=()=>localStorage.setItem(KEY,JSON.stringify(items));
const priorityRank={high:3,medium:2,low:1};
const budgetValue=v=>{const n=String(v||"").replace(/[^0-9.]/g,"");return parseFloat(n)||0};

function statusLabel(s){return{new:"Nuevo",ready:"Listo para revisar",sent:"Enviado",interview:"Entrevista",won:"Ganado",lost:"Perdido"}[s]||s}
function render(){
  const q=$("#search").value.toLowerCase().trim();
  const diff=$("#difficulty").value;
  const sort=$("#sort").value;
  let arr=items.filter(x=>
    (filter==="all"||x.status===filter)&&
    (market==="ALL"||x.market===market)&&
    (diff==="all"||x.difficulty===diff)&&
    (!q||[x.company,x.service,x.market,x.source,x.need].join(" ").toLowerCase().includes(q))
  );
  arr.sort((a,b)=>
    sort==="budget"?budgetValue(b.budget)-budgetValue(a.budget):
    sort==="newest"?String(b.id).localeCompare(String(a.id)):
    priorityRank[b.priority]-priorityRank[a.priority]
  );
  $("#cards").innerHTML=arr.length?arr.map(card).join(""):'<div class="empty">No hay oportunidades con estos filtros.</div>';
  updateMetrics();
}
function card(x){
  const diff=x.difficulty==="green"?"🟢":x.difficulty==="yellow"?"🟡":"🔴";
  const statusClass=["ready","sent","won","lost"].includes(x.status)?x.status:"";
  return `<article class="card">
    <div class="card-head">
      <span class="country">${escapeHtml(x.market)} · ${escapeHtml(x.source)}</span>
      <span class="badge ${escapeHtml(x.priority)}">${x.priority==="high"?"HIGH PRIORITY":x.priority.toUpperCase()}</span>
    </div>
    <h3>${escapeHtml(x.company)}</h3>
    <div class="meta">${escapeHtml(x.budget||"Presupuesto no indicado")} · <span class="status ${statusClass}">${statusLabel(x.status)}</span></div>
    <div class="service">${escapeHtml(x.service)}</div>
    <p>${escapeHtml(x.need)}</p>
    <div class="chips">
      <span class="chip">${diff} ${escapeHtml(x.difficulty)}</span>
      <span class="chip">${escapeHtml(x.market)}</span>
      <span class="chip">${escapeHtml(x.source)}</span>
    </div>
    <div class="card-actions">
      <button class="mini primary" data-action="proposal" data-id="${escapeHtml(x.id)}">Ver propuesta</button>
      <button class="mini" data-action="copy" data-id="${escapeHtml(x.id)}">Copiar</button>
      ${x.url?'<button class="mini" data-action="open" data-id="'+escapeHtml(x.id)+'">Abrir proyecto ↗</button>':''}
      <button class="mini" data-action="edit" data-id="${escapeHtml(x.id)}">Editar</button>
      <button class="mini" data-action="status" data-id="${escapeHtml(x.id)}">Marcar enviado</button>
    </div>
  </article>`
}
function escapeHtml(s){
  return String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[c]));
}
function updateMetrics(){
  $("#mTotal").textContent=items.length;
  $("#mHigh").textContent=items.filter(x=>x.priority==="high"&&x.status!=="lost").length;
  $("#mReady").textContent=items.filter(x=>x.status==="ready").length;
  $("#mWon").textContent=items.filter(x=>x.status==="won").length;
  $("#countAll").textContent=items.length;
  $("#countNew").textContent=items.filter(x=>x.status==="new").length;
  $("#countReady").textContent=items.filter(x=>x.status==="ready").length;
  $("#countSent").textContent=items.filter(x=>x.status==="sent").length;
}
function openModal(item=null){
  editing=item?.id||null;
  $("#modalTitle").textContent=item?"Editar oportunidad":"Nueva oportunidad";
  const f=$("#opForm");
  f.reset();
  if(item)Object.entries(item).forEach(([k,v])=>{if(f.elements[k])f.elements[k].value=v});
  $("#modal").classList.add("open");
}
function closeModal(){ $("#modal").classList.remove("open"); editing=null; }
function copyProposal(x){
  if(navigator.clipboard){
    navigator.clipboard.writeText(x.proposal).then(()=>flash("Propuesta copiada al portapapeles."));
  }else{
    const ta=document.createElement("textarea");ta.value=x.proposal;document.body.appendChild(ta);ta.select();document.execCommand("copy");ta.remove();flash("Propuesta copiada.");
  }
}
function flash(msg){
  const n=document.createElement("div");
  n.className="toast";
  n.textContent=msg;
  document.body.appendChild(n);
  setTimeout(()=>n.remove(),1800);
}

$$(".side-filter").forEach(b=>b.addEventListener("click",()=>{
  filter=b.dataset.filter;
  $$(".side-filter").forEach(x=>x.classList.remove("active"));
  b.classList.add("active");
  render();
}));
$$(".market").forEach(b=>b.addEventListener("click",()=>{
  market=b.dataset.market;
  $$(".market").forEach(x=>x.classList.remove("active"));
  b.classList.add("active");
  render();
}));
$("#search").addEventListener("input",render);
$("#difficulty").addEventListener("change",render);
$("#sort").addEventListener("change",render);
$("#addBtn").addEventListener("click",()=>openModal());
$("#closeModal").addEventListener("click",closeModal);
$("#cancelBtn").addEventListener("click",closeModal);
$("#modal").addEventListener("click",e=>{if(e.target.id==="modal")closeModal()});

$("#opForm").addEventListener("submit",e=>{
  e.preventDefault();
  const f=new FormData(e.target);
  const data=Object.fromEntries(f.entries());
  const item={
    ...data,
    id:editing||("op-"+Date.now()),
    company:data.company,market:data.market,source:data.source,service:data.service,
    budget:data.budget,priority:data.priority,difficulty:data.difficulty,status:data.status,
    url:data.url,need:data.need,proposal:data.proposal,notes:data.notes
  };
  if(editing){
    const i=items.findIndex(x=>x.id===editing);
    if(i>=0)items[i]=item;
  }else items.unshift(item);
  save(); closeModal(); render(); flash("Oportunidad guardada.");
});

$("#cards").addEventListener("click",e=>{
  const b=e.target.closest("button[data-action]");
  if(!b)return;
  const x=items.find(i=>i.id===b.dataset.id);
  if(!x)return;
  if(b.dataset.action==="copy")copyProposal(x);
  if(b.dataset.action==="proposal")openModal(x);
  if(b.dataset.action==="edit")openModal(x);
  if(b.dataset.action==="open")window.open(x.url,"_blank","noopener");
  if(b.dataset.action==="status"){x.status="sent";save();render();flash("Marcada como enviada.");}
});

$("#exportBtn").addEventListener("click",()=>{
  const blob=new Blob([JSON.stringify(items,null,2)],{type:"application/json"});
  const a=document.createElement("a");
  a.href=URL.createObjectURL(blob);
  a.download="zettacore-client-pipeline.json";
  a.click();
  setTimeout(()=>URL.revokeObjectURL(a.href),0);
});

const style=document.createElement("style");
style.textContent=".toast{position:fixed;right:20px;bottom:20px;padding:12px 15px;background:#0c1822;border:1px solid rgba(99,221,255,.3);border-radius:8px;color:#dff7ff;box-shadow:0 15px 40px rgba(0,0,0,.4);z-index:50;font-size:12px}";
document.head.appendChild(style);

async function loadRemote(){
  const local=JSON.parse(localStorage.getItem(KEY)||"[]");
  try{
    const res=await fetch("data.json?v="+Date.now(),{cache:"no-store"});
    if(!res.ok)throw new Error("data fetch failed");
    const remote=await res.json();
    const byId=new Map(remote.map(x=>[x.id,x]));
    for(const x of local)byId.set(x.id,x);
    items=[...byId.values()];
    save();
  }catch(e){
    items=local;
  }
  render();
}
loadRemote();

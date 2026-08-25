const state={person:null,file:null,type:'VL'};
const $=id=>document.getElementById(id);
function clean(v){return String(v||'').trim()}
function fullName(p){return [p.first_name,p.middle_name,p.last_name,p.suffix].map(clean).filter(Boolean).join(' ')}
function safe(v){return clean(v).toUpperCase().replace(/[^A-Z0-9]+/g,'-').replace(/^-|-$/g,'')}
function nowParts(){const d=new Date();return {year:d.getFullYear(),month:String(d.getMonth()+1).padStart(2,'0'),monthName:d.toLocaleString('en',{month:'long'}).toUpperCase()}}
function extension(name){const m=clean(name).match(/(\.[^.]+)$/);return m?m[1].toLowerCase():''}
function updateBucket(){
 const p=state.person, f=state.file, n=nowParts();
 if(p){$('selectedPerson').innerHTML=`<small>SELECTED PERSONNEL</small><strong>${clean(p.rank)} ${fullName(p)}</strong><span>${clean(p.office)||'Office not specified'}</span>`}
 else $('selectedPerson').innerHTML='<small>SELECTED PERSONNEL</small><strong>No personnel selected</strong><span>Click a row from the search results.</span>';
 $('fileName').textContent=f?f.name:'No file selected';
 if(p&&f){$('suggestedName').value=`${n.year}-${n.month}_${state.type}_${safe(p.rank)}_${safe(fullName(p))}${extension(f.name)}`}
 else if(!p||!f){$('suggestedName').value=''}
 $('destination').textContent=p?`PERSONNEL FILES / ${clean(p.rank)} ${fullName(p)} / LEAVE / ${n.year} / ${n.month} - ${n.monthName}`:'PERSONNEL FILES / — / LEAVE / —';
 $('fileButton').disabled=!(p&&f&&state.type);
}
async function search(){
 const q=$('search').value;
 try{
  const rows=await window.pywebview.api.search_personnel(q,200);
  const body=$('results');
  if(!rows.length){body.innerHTML='<tr><td colspan="5" class="empty">No personnel found.</td></tr>';return}
  body.innerHTML=rows.map((p,i)=>`<tr data-i="${i}"><td>${clean(p.rank)}</td><td>${clean(p.last_name)}</td><td>${clean(p.first_name)}</td><td>${clean(p.middle_name)}</td><td>${clean(p.office)}</td></tr>`).join('');
  [...body.querySelectorAll('tr')].forEach(tr=>tr.onclick=()=>{[...body.querySelectorAll('tr')].forEach(x=>x.classList.remove('selected'));tr.classList.add('selected');state.person=rows[Number(tr.dataset.i)];updateBucket()});
 }catch(e){$('results').innerHTML=`<tr><td colspan="5" class="empty">${e}</td></tr>`}
}
let timer;$('search').addEventListener('input',()=>{clearTimeout(timer);timer=setTimeout(search,180)});
$('leaveTypes').addEventListener('click',e=>{const b=e.target.closest('button');if(!b)return;[...$('leaveTypes').querySelectorAll('button')].forEach(x=>x.classList.remove('active'));b.classList.add('active');state.type=b.dataset.type;updateBucket()});
const dz=$('dropzone'),fi=$('fileInput');function takeFile(file){if(!file)return;const ok=/\.(pdf|jpe?g)$/i.test(file.name);if(!ok){$('status').textContent='PDF/JPG only';return}state.file=file;$('status').textContent='File ready';updateBucket()}
fi.addEventListener('change',()=>takeFile(fi.files[0]));['dragenter','dragover'].forEach(x=>dz.addEventListener(x,e=>{e.preventDefault();dz.classList.add('drag')}));['dragleave','drop'].forEach(x=>dz.addEventListener(x,e=>{e.preventDefault();dz.classList.remove('drag')}));dz.addEventListener('drop',e=>takeFile(e.dataTransfer.files[0]));
$('fileButton').onclick=()=>{$('status').textContent='Preview ready';alert(`V1 workflow is ready.\n\nPersonnel: ${clean(state.person.rank)} ${fullName(state.person)}\nLeave: ${state.type}\nFilename: ${$('suggestedName').value}\n\nGoogle Drive upload is intentionally not connected yet.`)};
window.addEventListener('pywebviewready',search);

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
 $('destination').textContent=p?`LOCAL + DRIVE: ${clean(p.rank)} ${fullName(p)} / LEAVE / ${n.year} / ${n.month} - ${n.monthName}`:'LOCAL + DRIVE: — / LEAVE / —';
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
function fileToBase64(file){return new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>{const result=String(reader.result||'');resolve(result.includes(',')?result.split(',',2)[1]:result)};reader.onerror=()=>reject(reader.error||new Error('Could not read file'));reader.readAsDataURL(file)})}
let timer;$('search').addEventListener('input',()=>{clearTimeout(timer);timer=setTimeout(search,180)});
$('leaveTypes').addEventListener('click',e=>{const b=e.target.closest('button');if(!b)return;[...$('leaveTypes').querySelectorAll('button')].forEach(x=>x.classList.remove('active'));b.classList.add('active');state.type=b.dataset.type;updateBucket()});
const dz=$('dropzone'),fi=$('fileInput');function takeFile(file){if(!file)return;const ok=/\.(pdf|jpe?g)$/i.test(file.name);if(!ok){$('status').textContent='PDF/JPG only';return}state.file=file;$('status').textContent='File ready';updateBucket()}
fi.addEventListener('change',()=>takeFile(fi.files[0]));['dragenter','dragover'].forEach(x=>dz.addEventListener(x,e=>{e.preventDefault();dz.classList.add('drag')}));['dragleave','drop'].forEach(x=>dz.addEventListener(x,e=>{e.preventDefault();dz.classList.remove('drag')}));dz.addEventListener('drop',e=>takeFile(e.dataTransfer.files[0]));
$('fileButton').onclick=async()=>{
 if(!state.person||!state.file)return;
 const button=$('fileButton');
 button.disabled=true;button.textContent='FILING…';$('status').textContent='Saving + uploading';
 try{
  const data=await fileToBase64(state.file);
  const finalName=clean($('suggestedName').value)||state.file.name;
  const result=await window.pywebview.api.file_document(data,finalName,clean(state.person.rank),fullName(state.person),'LEAVE');
  if(!result||!result.ok){
   if(result?.local_saved){
    $('status').textContent='Local saved, Drive failed';
    $('destination').textContent=`LOCAL SAVED: ${result.local?.path||''}`;
    throw new Error(result.message||'Drive upload failed');
   }
   throw new Error(result?.message||'Could not file document');
  }
  $('status').textContent='Filed ✓';
  const localPath=result.local?.path||'';
  const driveLink=result.drive?.web_view_link||'';
  $('destination').textContent=`LOCAL: ${localPath} | DRIVE: ${result.drive?.filename||finalName}`;
  alert(`Document filed successfully.\n\nLocal copy:\n${localPath}\n\nGoogle Drive:\n${driveLink||'Uploaded successfully'}`);
 }catch(e){$('status').textContent=$('status').textContent.includes('Local saved')?'Local saved, Drive failed':'Filing failed';alert(`Could not complete filing:\n${e.message||e}`)}
 finally{button.disabled=false;button.textContent='FILE DOCUMENT'}
};
window.addEventListener('pywebviewready',search);

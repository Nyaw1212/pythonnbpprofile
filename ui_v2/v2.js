let v2Zoom = 1;
const V2_ZOOM_MIN = 0.5;
const V2_ZOOM_MAX = 1.5;
const V2_ZOOM_STEP = 0.1;

function applyV2Zoom(){
  const sheet=document.querySelector('.v2-profile-sheet');
  const value=document.getElementById('zoomResetButton');
  if(sheet)sheet.style.zoom=String(v2Zoom);
  if(value)value.textContent=`${Math.round(v2Zoom*100)}%`;
  const out=document.getElementById('zoomOutButton');
  const inc=document.getElementById('zoomInButton');
  if(out)out.disabled=v2Zoom<=V2_ZOOM_MIN;
  if(inc)inc.disabled=v2Zoom>=V2_ZOOM_MAX;
}

function setV2Zoom(next){
  v2Zoom=Math.min(V2_ZOOM_MAX,Math.max(V2_ZOOM_MIN,Math.round(next*10)/10));
  applyV2Zoom();
}

function normalizeV2PersonnelStatus(value){
  const text=String(value||'').trim();
  if(/^active\s*\/\s*on duty$/i.test(text))return 'Active';
  return text||'—';
}

async function hydrateV2ProfileExtras(){
  try{
    if(typeof state==='undefined'||!state.currentBadge)return;
    const person=await pywebview.api.get_profile(String(state.currentBadge));
    if(!person)return;
    const batch=document.getElementById('profileBatchName');
    if(batch)batch.textContent=person.batch_name||'—';
    const status=document.getElementById('profilePersonnelStatus');
    if(status)status.textContent=normalizeV2PersonnelStatus(person.personnel_status);
  }catch(error){/* Keep profile usable even if optional V2 fields fail. */}
}

document.addEventListener('click',event=>{
  if(event.target.closest('#zoomOutButton')){event.preventDefault();setV2Zoom(v2Zoom-V2_ZOOM_STEP);return;}
  if(event.target.closest('#zoomInButton')){event.preventDefault();setV2Zoom(v2Zoom+V2_ZOOM_STEP);return;}
  if(event.target.closest('#zoomResetButton')){event.preventDefault();setV2Zoom(1);return;}

  if(event.target.closest('.person-row'))setTimeout(hydrateV2ProfileExtras,120);

  const saveButton=event.target.closest('#savePdfButton');
  if(!saveButton)return;
  event.preventDefault();
  event.stopImmediatePropagation();
  const status=document.getElementById('pdfStatus');
  if(status){status.textContent='Choose “Save as PDF” in the print dialog.';status.className='pdf-status success';}
  window.print();
},true);

document.addEventListener('keydown',event=>{
  const modal=document.getElementById('profileModal');
  if(!modal||modal.classList.contains('hidden'))return;
  if(!event.ctrlKey)return;
  if(event.key==='+'||event.key==='='){event.preventDefault();setV2Zoom(v2Zoom+V2_ZOOM_STEP);}
  else if(event.key==='-'){event.preventDefault();setV2Zoom(v2Zoom-V2_ZOOM_STEP);}
  else if(event.key==='0'){event.preventDefault();setV2Zoom(1);}
});

window.addEventListener('pywebviewready',()=>{
  setV2Zoom(1);
  const modal=document.getElementById('profileModal');
  if(modal){
    new MutationObserver(()=>{
      if(!modal.classList.contains('hidden'))setTimeout(hydrateV2ProfileExtras,0);
    }).observe(modal,{attributes:true,attributeFilter:['class']});
  }
});

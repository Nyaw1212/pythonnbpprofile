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

document.addEventListener('click',event=>{
  if(event.target.closest('#zoomOutButton')){event.preventDefault();setV2Zoom(v2Zoom-V2_ZOOM_STEP);return;}
  if(event.target.closest('#zoomInButton')){event.preventDefault();setV2Zoom(v2Zoom+V2_ZOOM_STEP);return;}
  if(event.target.closest('#zoomResetButton')){event.preventDefault();setV2Zoom(1);return;}

  const saveButton=event.target.closest('#savePdfButton');
  if(!saveButton)return;
  event.preventDefault();
  event.stopImmediatePropagation();
  const status=document.getElementById('pdfStatus');
  if(status){status.textContent='Choose “Save as PDF” in the print dialog.';status.className='pdf-status success';}
  window.print();
},true);

document.addEventListener('keydown',event=>{
  if(!document.getElementById('profileModal') || document.getElementById('profileModal').classList.contains('hidden'))return;
  if(!event.ctrlKey)return;
  if(event.key==='+'||event.key==='='){event.preventDefault();setV2Zoom(v2Zoom+V2_ZOOM_STEP);}
  else if(event.key==='-'){event.preventDefault();setV2Zoom(v2Zoom-V2_ZOOM_STEP);}
  else if(event.key==='0'){event.preventDefault();setV2Zoom(1);}
});

window.addEventListener('pywebviewready',()=>{setV2Zoom(1);});

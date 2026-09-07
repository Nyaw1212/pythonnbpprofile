let v2Zoom = 1;
const V2_ZOOM_MIN = 0.5;
const V2_ZOOM_MAX = 1.5;
const V2_ZOOM_STEP = 0.1;

const V2_RANKS={
  CO1:{name:'Corrections Officer I',classification:'Non-Commissioned',type:'CORRECTIONS OFFICER'},
  CO2:{name:'Corrections Officer II',classification:'Non-Commissioned',type:'CORRECTIONS OFFICER'},
  CO3:{name:'Corrections Officer III',classification:'Non-Commissioned',type:'CORRECTIONS OFFICER'},
  CSO1:{name:'Corrections Senior Officer I',classification:'Non-Commissioned',type:'CORRECTIONS OFFICER'},
  CSO2:{name:'Corrections Senior Officer II',classification:'Non-Commissioned',type:'CORRECTIONS OFFICER'},
  CSO3:{name:'Corrections Senior Officer III',classification:'Non-Commissioned',type:'CORRECTIONS OFFICER'},
  CSO4:{name:'Corrections Senior Officer IV',classification:'Non-Commissioned',type:'CORRECTIONS OFFICER'},
  CINSP:{name:'Corrections Inspector',classification:'Commissioned',type:'CORRECTIONS OFFICER'},
  CSINSP:{name:'Corrections Senior Inspector',classification:'Commissioned',type:'CORRECTIONS OFFICER'},
  CCINSP:{name:'Corrections Chief Inspector',classification:'Commissioned',type:'CORRECTIONS OFFICER'},
  CSUPT:{name:'Corrections Superintendent',classification:'Commissioned',type:'CORRECTIONS OFFICER'},
  CSSUPT:{name:'Corrections Senior Superintendent',classification:'Commissioned',type:'CORRECTIONS OFFICER'},
  CCSUPT:{name:'Corrections Chief Superintendent',classification:'Commissioned',type:'CORRECTIONS OFFICER'},
  CTO1:{name:'Corrections Technical Officer I',classification:'Non-Commissioned',type:'CORRECTIONS TECHNICAL OFFICER'},
  CTO2:{name:'Corrections Technical Officer II',classification:'Non-Commissioned',type:'CORRECTIONS TECHNICAL OFFICER'},
  CTO3:{name:'Corrections Technical Officer III',classification:'Non-Commissioned',type:'CORRECTIONS TECHNICAL OFFICER'},
  CTSO1:{name:'Corrections Technical Senior Officer I',classification:'Non-Commissioned',type:'CORRECTIONS TECHNICAL OFFICER'},
  CTSO2:{name:'Corrections Technical Senior Officer II',classification:'Non-Commissioned',type:'CORRECTIONS TECHNICAL OFFICER'},
  CTSO3:{name:'Corrections Technical Senior Officer III',classification:'Non-Commissioned',type:'CORRECTIONS TECHNICAL OFFICER'},
  CTSO4:{name:'Corrections Technical Senior Officer IV',classification:'Non-Commissioned',type:'CORRECTIONS TECHNICAL OFFICER'},
  CTINSP:{name:'Corrections Technical Inspector',classification:'Commissioned',type:'CORRECTIONS TECHNICAL OFFICER'},
  CTSINSP:{name:'Corrections Technical Senior Inspector',classification:'Commissioned',type:'CORRECTIONS TECHNICAL OFFICER'},
  CTCINSP:{name:'Corrections Technical Chief Inspector',classification:'Commissioned',type:'CORRECTIONS TECHNICAL OFFICER'},
  CTSUPT:{name:'Corrections Technical Superintendent',classification:'Commissioned',type:'CORRECTIONS TECHNICAL OFFICER'},
  CTSSUPT:{name:'Corrections Technical Senior Superintendent',classification:'Commissioned',type:'CORRECTIONS TECHNICAL OFFICER'},
  CTCSUPT:{name:'Corrections Technical Chief Superintendent',classification:'Commissioned',type:'CORRECTIONS TECHNICAL OFFICER'}
};

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

function applyV2RankPresentation(person){
  const code=String(person.rank||'').trim().toUpperCase();
  const mapped=V2_RANKS[code];
  const rank=document.getElementById('profileRank');
  const classification=document.getElementById('profileClassificationOffice');
  const type=document.getElementById('profileType');
  if(mapped){
    if(rank)rank.textContent=mapped.name;
    if(classification)classification.textContent=mapped.classification;
    if(type)type.textContent=mapped.type;
  }else{
    if(rank)rank.textContent=person.rank||'—';
    if(classification)classification.textContent=person.classification||'—';
    if(type)type.textContent=person.personnel_type||'—';
  }
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
    applyV2RankPresentation(person);
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
  const subtitle=document.querySelector('.v2-brand-header p');
  if(subtitle)subtitle.textContent='MOVEMENT TRACKING';
  const modal=document.getElementById('profileModal');
  if(modal){
    new MutationObserver(()=>{
      if(!modal.classList.contains('hidden'))setTimeout(hydrateV2ProfileExtras,0);
    }).observe(modal,{attributes:true,attributeFilter:['class']});
  }
});

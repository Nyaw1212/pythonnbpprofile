let v2Zoom = 1;
const V2_ZOOM_MIN = 0.5;
const V2_ZOOM_MAX = 1.5;
const V2_ZOOM_STEP = 0.1;
const V2_PAN_STEP = 90;
let v2PanState = { active:false, startX:0, startY:0, scrollLeft:0, scrollTop:0, pointerId:null };
let v2Initialized = false;

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

const V2_CAMP_COLORS={
  NBP:{background:'#1f6b45',color:'#fff'},
  MAXIMUM:{background:'#d97706',color:'#fff'},
  MEDIUM:{background:'#2563a6',color:'#fff'},
  MINIMUM:{background:'#7a4b2a',color:'#fff'},
  RDC:{background:'#d6a900',color:'#2d2500'}
};

function v2Frame(){ return document.querySelector('.v2-modal-frame'); }
function blankV2(value){ return value===null||value===undefined||String(value).trim()===''; }
function setV2Text(id,value){ const node=document.getElementById(id); if(node)node.textContent=blankV2(value)?'—':String(value); }
function setV2Node(node,value){ if(node)node.textContent=blankV2(value)?'—':String(value); }

function forceV2GreenTheme(){
  const sheet=document.querySelector('.v2-profile-sheet');
  if(!sheet)return;
  sheet.style.setProperty('--v2-orange','#1f6b45');
  sheet.style.setProperty('--v2-orange-dark','#155437');
  sheet.style.setProperty('--v2-soft','#e7f2eb');
  sheet.style.setProperty('--v2-line','#8ab69d');
  sheet.style.setProperty('--v2-text','#173a2a');
  sheet.style.setProperty('--v2-accent-text','#fff');
}

function applyV2CampBadge(person){
  const badge=document.getElementById('profileCampBadge');
  if(!badge)return;
  const camp=String(person.camp||'').trim().toUpperCase();
  const palette=V2_CAMP_COLORS[camp]||{background:'#6b7280',color:'#fff'};
  badge.textContent=camp||'—';
  badge.style.background=palette.background;
  badge.style.color=palette.color;
}

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
  const frame=v2Frame();
  const oldZoom=v2Zoom;
  const centerX=frame ? frame.scrollLeft + frame.clientWidth/2 : 0;
  const centerY=frame ? frame.scrollTop + frame.clientHeight/2 : 0;
  v2Zoom=Math.min(V2_ZOOM_MAX,Math.max(V2_ZOOM_MIN,Math.round(next*10)/10));
  applyV2Zoom();
  if(frame && oldZoom>0){
    const ratio=v2Zoom/oldZoom;
    requestAnimationFrame(()=>{
      frame.scrollLeft=Math.max(0,centerX*ratio-frame.clientWidth/2);
      frame.scrollTop=Math.max(0,centerY*ratio-frame.clientHeight/2);
    });
  }
}

function panV2By(dx,dy){ const frame=v2Frame(); if(frame){frame.scrollLeft+=dx;frame.scrollTop+=dy;} }
function normalizeV2PersonnelStatus(value){ const text=String(value||'').trim(); return /^active\s*\/\s*on duty$/i.test(text)?'Active':(text||'—'); }
function formatV2Date(value){
  if(!value)return '—';
  const parsed=new Date(String(value));
  if(Number.isNaN(parsed.getTime()))return String(value);
  return parsed.toLocaleDateString('en-US',{year:'numeric',month:'long',day:'numeric'});
}

function applyV2RankPresentation(person){
  const code=String(person.rank||'').trim().toUpperCase();
  const mapped=V2_RANKS[code];
  setV2Text('profileRank',mapped?mapped.name:person.rank);
  setV2Text('profileClassificationOffice',mapped?mapped.classification:person.classification);
  setV2Text('profileType',mapped?mapped.type:person.personnel_type);
}

function hydrateV2Family(person){
  const cards=document.querySelectorAll('.v2-family-card');
  const data=[
    [person.father_name,person.father_occupation,person.father_address],
    [person.mother_name,person.mother_occupation,person.mother_address],
    [person.spouse_name,person.spouse_occupation,person.spouse_address]
  ];
  cards.forEach((card,index)=>{
    const values=card.querySelectorAll('strong');
    if(!data[index])return;
    values.forEach((node,valueIndex)=>setV2Node(node,data[index][valueIndex]));
  });
}

function hydrateV2Education(person){
  const rows=document.querySelectorAll('.v2-education-table tbody tr');
  const data=[
    ['Elementary',person.elementary_school,person.elementary_course,person.elementary_address,person.elementary_year_graduated],
    ['High School',person.high_school,person.high_school_course,person.high_school_address,person.high_school_year_graduated],
    ['College',person.college,person.college_course,person.college_address,person.college_year_graduated],
    ['Graduate Studies',person.graduate_studies,person.graduate_studies_course,person.graduate_studies_address,person.graduate_studies_year_graduated]
  ];
  rows.forEach((row,index)=>{
    const cells=row.querySelectorAll('td');
    if(!data[index])return;
    cells.forEach((cell,cellIndex)=>setV2Node(cell,data[index][cellIndex]));
  });
}

async function hydrateV2ProfileExtras(){
  try{
    if(typeof state==='undefined'||!state.currentBadge||!window.pywebview?.api?.get_profile)return;
    const person=await pywebview.api.get_profile(String(state.currentBadge));
    if(!person)return;
    forceV2GreenTheme();
    setV2Text('profileBatchName',person.batch_name);
    setV2Text('profileDateEntranceDuty',formatV2Date(person.date_entrance_duty));
    setV2Text('profilePersonnelStatus',normalizeV2PersonnelStatus(person.personnel_status));
    setV2Text('profileCurrentOffice',person.office);
    setV2Text('profilePreviousOffice',person.previous_office);
    applyV2CampBadge(person);
    if(person.home_address)setV2Text('profileAddress',person.home_address);
    setV2Text('profileEmergencyContact',person.emergency_contact);
    setV2Text('profileEmergencyRelationship',person.emergency_relationship);
    setV2Text('profileEmergencyNumber',person.emergency_number);
    setV2Text('profileEmergencyAddress',person.emergency_address);
    hydrateV2Family(person);
    hydrateV2Education(person);
    applyV2RankPresentation(person);
  }catch(error){ console.error('V2 profile hydration failed:',error); }
}

function initV2(){
  if(v2Initialized)return;
  v2Initialized=true;
  forceV2GreenTheme();
  setV2Zoom(1);

  document.addEventListener('click',event=>{
    if(event.target.closest('#zoomOutButton')){event.preventDefault();setV2Zoom(v2Zoom-V2_ZOOM_STEP);return;}
    if(event.target.closest('#zoomInButton')){event.preventDefault();setV2Zoom(v2Zoom+V2_ZOOM_STEP);return;}
    if(event.target.closest('#zoomResetButton')){event.preventDefault();setV2Zoom(1);return;}
    const saveButton=event.target.closest('#savePdfButton');
    if(saveButton){
      event.preventDefault();
      const status=document.getElementById('pdfStatus');
      if(status){status.textContent='Choose “Save as PDF” in the print dialog.';status.className='pdf-status success';}
      window.print();
    }
  });

  document.addEventListener('keydown',event=>{
    const modal=document.getElementById('profileModal');
    if(!modal||modal.classList.contains('hidden'))return;
    if(event.ctrlKey&&event.shiftKey){
      if(event.key==='ArrowLeft'){event.preventDefault();panV2By(-V2_PAN_STEP,0);return;}
      if(event.key==='ArrowRight'){event.preventDefault();panV2By(V2_PAN_STEP,0);return;}
      if(event.key==='ArrowUp'){event.preventDefault();panV2By(0,-V2_PAN_STEP);return;}
      if(event.key==='ArrowDown'){event.preventDefault();panV2By(0,V2_PAN_STEP);return;}
    }
    if(!event.ctrlKey)return;
    if(event.key==='+'||event.key==='='){event.preventDefault();setV2Zoom(v2Zoom+V2_ZOOM_STEP);}
    else if(event.key==='-'){event.preventDefault();setV2Zoom(v2Zoom-V2_ZOOM_STEP);}
    else if(event.key==='0'){event.preventDefault();setV2Zoom(1);}
  });

  const frame=v2Frame();
  if(frame){
    frame.addEventListener('wheel',event=>{
      if(event.ctrlKey){event.preventDefault();setV2Zoom(v2Zoom+(event.deltaY<0?V2_ZOOM_STEP:-V2_ZOOM_STEP));return;}
      if(event.shiftKey){event.preventDefault();frame.scrollLeft+=event.deltaY||event.deltaX;}
    },{passive:false});

    frame.addEventListener('pointerdown',event=>{
      if(event.button!==0||event.target.closest('.profile-toolbar,button,input,textarea,select,a'))return;
      v2PanState={active:true,startX:event.clientX,startY:event.clientY,scrollLeft:frame.scrollLeft,scrollTop:frame.scrollTop,pointerId:event.pointerId};
      frame.classList.add('v2-panning');
      try{frame.setPointerCapture(event.pointerId);}catch(_error){}
      event.preventDefault();
    });
    frame.addEventListener('pointermove',event=>{
      if(!v2PanState.active)return;
      frame.scrollLeft=v2PanState.scrollLeft-(event.clientX-v2PanState.startX);
      frame.scrollTop=v2PanState.scrollTop-(event.clientY-v2PanState.startY);
    });
    const endPan=()=>{v2PanState.active=false;frame.classList.remove('v2-panning');v2PanState.pointerId=null;};
    frame.addEventListener('pointerup',endPan);
    frame.addEventListener('pointercancel',endPan);
    frame.addEventListener('lostpointercapture',endPan);
  }

  const modal=document.getElementById('profileModal');
  if(modal){
    new MutationObserver(()=>{
      if(!modal.classList.contains('hidden')){
        requestAnimationFrame(()=>{
          hydrateV2ProfileExtras();
          const current=v2Frame();
          if(current){current.scrollLeft=0;current.scrollTop=0;}
        });
      }
    }).observe(modal,{attributes:true,attributeFilter:['class']});
  }
}

window.addEventListener('pywebviewready',initV2);
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',initV2);
else initV2();

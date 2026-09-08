let v2Zoom = 1;
const V2_ZOOM_MIN = 0.5;
const V2_ZOOM_MAX = 1.5;
const V2_ZOOM_STEP = 0.1;
const V2_PAN_STEP = 90;
let v2PanState = { active:false, startX:0, startY:0, scrollLeft:0, scrollTop:0, pointerId:null };

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

function v2Frame(){return document.querySelector('.v2-modal-frame');}

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

function setV2Text(id,value){
  const node=document.getElementById(id);
  if(node)node.textContent=(value===null||value===undefined||String(value).trim()==='')?'—':String(value);
}

function setV2Node(node,value){
  if(node)node.textContent=(value===null||value===undefined||String(value).trim()==='')?'—':String(value);
}

function applyV2CampBadge(person){
  const valueNode=document.getElementById('profileCurrentCamp');
  if(!valueNode)return;
  const row=valueNode.parentElement;
  if(!row)return;
  const label=row.querySelector('span');
  if(label)label.textContent='Previous Office:';
  valueNode.textContent=person.previous_office||'—';
  row.style.gridTemplateColumns='39mm minmax(0,1fr) auto';
  row.style.alignItems='center';

  let badge=row.querySelector('.v2-camp-badge');
  if(!badge){
    badge=document.createElement('span');
    badge.className='v2-camp-badge';
    row.appendChild(badge);
  }
  const camp=String(person.camp||'').trim().toUpperCase();
  const palette=V2_CAMP_COLORS[camp]||{background:'#6b7280',color:'#fff'};
  badge.textContent=camp||'—';
  Object.assign(badge.style,{
    display:'inline-flex',alignItems:'center',justifyContent:'center',minWidth:'22mm',padding:'1.2mm 2.5mm',
    borderRadius:'999px',background:palette.background,color:palette.color,fontSize:'8.5px',fontWeight:'900',
    lineHeight:'1',letterSpacing:'.04em',textTransform:'uppercase',whiteSpace:'nowrap'
  });
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

function panV2By(dx,dy){
  const frame=v2Frame();
  if(!frame)return;
  frame.scrollLeft+=dx;
  frame.scrollTop+=dy;
}

function normalizeV2PersonnelStatus(value){
  const text=String(value||'').trim();
  if(/^active\s*\/\s*on duty$/i.test(text))return 'Active';
  return text||'—';
}

function formatV2Date(value){
  if(!value)return '—';
  const parsed=new Date(String(value));
  if(Number.isNaN(parsed.getTime()))return String(value);
  return parsed.toLocaleDateString('en-US',{year:'numeric',month:'long',day:'numeric'});
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

function hydrateV2Family(person){
  setV2Text('profileFatherName',person.father_name);
  setV2Text('profileFatherAddress',person.father_address);
  setV2Text('profileMotherName',person.mother_name);
  setV2Text('profileMotherAddress',person.mother_address);

  const cards=document.querySelectorAll('.v2-family-card');
  if(cards[0]){
    const values=cards[0].querySelectorAll('strong');
    setV2Node(values[0],person.father_name);
    setV2Node(values[1],person.father_occupation);
    setV2Node(values[2],person.father_address);
  }
  if(cards[1]){
    const values=cards[1].querySelectorAll('strong');
    setV2Node(values[0],person.mother_name);
    setV2Node(values[1],person.mother_occupation);
    setV2Node(values[2],person.mother_address);
  }
  if(cards[2]){
    const values=cards[2].querySelectorAll('strong');
    setV2Node(values[0],person.spouse_name);
    setV2Node(values[1],person.spouse_occupation);
    setV2Node(values[2],person.spouse_address);
  }
}

function hydrateV2Education(person){
  const table=document.querySelector('.v2-education-table');
  if(!table)return;

  const headerRow=table.querySelector('thead tr');
  if(headerRow){
    headerRow.innerHTML='<th>School Level</th><th>School Attended</th><th>Address</th><th>Year Graduated</th>';
  }

  const levels=['Elementary','High School','College','Graduate Studies'];
  const data=[
    [person.elementary_school,person.elementary_address,person.elementary_year_graduated],
    [person.high_school,person.high_school_address,person.high_school_year_graduated],
    [person.college,person.college_address,person.college_year_graduated],
    [person.graduate_studies,person.graduate_studies_address,person.graduate_studies_year_graduated]
  ];

  const rows=table.querySelectorAll('tbody tr');
  rows.forEach((row,index)=>{
    if(!data[index])return;
    row.innerHTML='<td></td><td></td><td></td><td></td>';
    const cells=row.querySelectorAll('td');
    setV2Node(cells[0],levels[index]);
    setV2Node(cells[1],data[index][0]);
    setV2Node(cells[2],data[index][1]);
    setV2Node(cells[3],data[index][2]);
  });
}

async function hydrateV2ProfileExtras(){
  try{
    if(typeof state==='undefined'||!state.currentBadge)return;
    const person=await pywebview.api.get_profile(String(state.currentBadge));
    if(!person)return;

    forceV2GreenTheme();
    setV2Text('profileBatchName',person.batch_name);
    setV2Text('profileDateEntranceDuty',formatV2Date(person.date_entrance_duty));
    setV2Text('profilePersonnelStatus',normalizeV2PersonnelStatus(person.personnel_status));
    setV2Text('profileCurrentOffice',person.office);
    applyV2CampBadge(person);

    if(person.home_address)setV2Text('profileAddress',person.home_address);
    setV2Text('profileEmergencyContact',person.emergency_contact);
    setV2Text('profileEmergencyRelationship',person.emergency_relationship);
    setV2Text('profileEmergencyNumber',person.emergency_number);
    setV2Text('profileEmergencyAddress',person.emergency_address);

    hydrateV2Family(person);
    hydrateV2Education(person);
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

window.addEventListener('pywebviewready',()=>{
  setV2Zoom(1);
  forceV2GreenTheme();
  const modal=document.getElementById('profileModal');
  const frame=v2Frame();
  if(frame){
    frame.addEventListener('wheel',event=>{
      if(event.ctrlKey){
        event.preventDefault();
        setV2Zoom(v2Zoom + (event.deltaY < 0 ? V2_ZOOM_STEP : -V2_ZOOM_STEP));
        return;
      }
      if(event.shiftKey){
        event.preventDefault();
        frame.scrollLeft+=event.deltaY||event.deltaX;
      }
    },{passive:false});

    frame.addEventListener('pointerdown',event=>{
      if(event.button!==0)return;
      if(event.target.closest('.profile-toolbar,button,input,textarea,select,a'))return;
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

    const endPan=event=>{
      if(!v2PanState.active)return;
      v2PanState.active=false;
      frame.classList.remove('v2-panning');
      try{if(v2PanState.pointerId!==null)frame.releasePointerCapture(v2PanState.pointerId);}catch(_error){}
      v2PanState.pointerId=null;
    };
    frame.addEventListener('pointerup',endPan);
    frame.addEventListener('pointercancel',endPan);
    frame.addEventListener('lostpointercapture',endPan);
  }
  if(modal){
    new MutationObserver(()=>{
      if(!modal.classList.contains('hidden')){
        setTimeout(()=>{
          forceV2GreenTheme();
          hydrateV2ProfileExtras();
          const current=v2Frame();
          if(current){current.scrollLeft=0;current.scrollTop=0;}
        },0);
      }
    }).observe(modal,{attributes:true,attributeFilter:['class']});
  }
});

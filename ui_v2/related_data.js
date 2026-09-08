function v2FindSection(title){
  return [...document.querySelectorAll('.v2-section')].find(section=>{
    const heading=section.querySelector('.v2-section-title');
    return heading&&heading.textContent.trim().toUpperCase()===title.toUpperCase();
  });
}

function v2RelatedDisplay(value){
  return value===null||value===undefined||String(value).trim()===''?'—':String(value);
}

function v2RelatedDate(value){
  if(!value)return '—';
  const parsed=new Date(String(value));
  if(Number.isNaN(parsed.getTime()))return String(value);
  return parsed.toLocaleDateString('en-US',{year:'numeric',month:'short',day:'numeric'});
}

function v2MovementToDate(value){
  return value===null||value===undefined||String(value).trim()===''?'PRESENT':v2RelatedDate(value);
}

function v2MovementTimestamp(value){
  if(!value)return Number.NEGATIVE_INFINITY;
  const parsed=new Date(String(value));
  return Number.isNaN(parsed.getTime())?Number.NEGATIVE_INFINITY:parsed.getTime();
}

function v2NormalizeCamp(value){
  const camp=String(value||'').trim().toUpperCase();
  const aliases={NPB:'NBP',MAX:'MAXIMUM',MED:'MEDIUM',MIN:'MINIMUM'};
  return aliases[camp]||camp;
}

function v2CampPalette(camp){
  const key=v2NormalizeCamp(camp);
  const colors={
    NBP:{background:'#1f6b45',color:'#fff'},
    MAXIMUM:{background:'#d97706',color:'#fff'},
    MEDIUM:{background:'#2563a6',color:'#fff'},
    MINIMUM:{background:'#7a4b2a',color:'#fff'},
    RDC:{background:'#d6a900',color:'#2d2500'}
  };
  return colors[key]||{background:'#6b7280',color:'#fff'};
}

function v2SetCampBadge(node,camp){
  if(!node)return;
  const normalized=v2NormalizeCamp(camp);
  const palette=v2CampPalette(normalized);
  node.textContent=normalized||'—';
  node.style.background=palette.background;
  node.style.color=palette.color;
}

function v2SetConflictBadge(node){
  if(!node)return;
  node.textContent='CONFLICT';
  node.style.background='#b42318';
  node.style.color='#fff';
}

function v2EnsureCurrentCampBadge(){
  const valueNode=document.getElementById('profileCurrentOffice');
  if(!valueNode||!valueNode.parentElement)return null;
  const row=valueNode.parentElement;
  row.classList.add('v2-previous-office-row');
  let badge=row.querySelector('.v2-current-camp-badge');
  if(!badge){
    badge=document.createElement('em');
    badge.className='v2-camp-badge v2-current-camp-badge';
    row.appendChild(badge);
  }
  return badge;
}

function v2FullPersonnelName(person){
  return [person.first_name,person.middle_name,person.last_name,person.suffix]
    .map(value=>String(value||'').trim())
    .filter(Boolean)
    .join(' ')
    .replace(/\s+/g,' ')
    .trim();
}

function v2BuildTable(headers,rows,emptyMessage){
  const table=document.createElement('table');
  table.className='v2-table';
  const thead=document.createElement('thead');
  const headRow=document.createElement('tr');
  headers.forEach(header=>{
    const th=document.createElement('th');
    th.textContent=header;
    headRow.appendChild(th);
  });
  thead.appendChild(headRow);
  table.appendChild(thead);
  const tbody=document.createElement('tbody');
  if(!rows.length){
    const tr=document.createElement('tr');
    const td=document.createElement('td');
    td.colSpan=headers.length;
    td.textContent=emptyMessage;
    tr.appendChild(td);
    tbody.appendChild(tr);
  }else{
    rows.forEach(values=>{
      const tr=document.createElement('tr');
      values.forEach(value=>{
        const td=document.createElement('td');
        td.textContent=v2RelatedDisplay(value);
        tr.appendChild(td);
      });
      tbody.appendChild(tr);
    });
  }
  table.appendChild(tbody);
  return table;
}

function v2ReplaceSectionBody(section,node){
  if(!section)return;
  [...section.children].forEach(child=>{
    if(!child.classList.contains('v2-section-title'))child.remove();
  });
  section.appendChild(node);
}

function v2NormalizeMovements(rawMovements){
  return [...(rawMovements||[])]
    .map(item=>({
      ...item,
      from_camp:v2NormalizeCamp(item.from_camp),
      to_camp:v2NormalizeCamp(item.to_camp)
    }))
    .sort((a,b)=>v2MovementTimestamp(b.from_date)-v2MovementTimestamp(a.from_date));
}

function v2ResolveAssignments(movements){
  const present=movements.filter(item=>item.to_date===null||item.to_date===undefined||String(item.to_date).trim()==='');
  if(present.length>1){
    return {conflict:true,current:null,previous:null,present_count:present.length};
  }

  if(present.length===1){
    const current=present[0];
    const currentTime=v2MovementTimestamp(current.from_date);
    const previous=movements
      .filter(item=>item!==current && v2MovementTimestamp(item.from_date)<=currentTime)
      .sort((a,b)=>v2MovementTimestamp(b.from_date)-v2MovementTimestamp(a.from_date))[0]||null;
    return {conflict:false,current,previous,present_count:1};
  }

  const latest=movements[0]||null;
  const previous=movements[1]||null;
  return {conflict:false,current:latest,previous,present_count:0};
}

async function hydrateV2RelatedRecords(){
  try{
    if(typeof state==='undefined'||!state.currentBadge||!window.pywebview?.api?.get_profile_related)return;

    let person=null;
    if(window.pywebview?.api?.get_profile){
      person=await pywebview.api.get_profile(String(state.currentBadge));
      if(person){
        const fullName=v2FullPersonnelName(person);
        if(fullName)setV2Text('profileName',fullName.toUpperCase());
      }
    }

    const data=await pywebview.api.get_profile_related(String(state.currentBadge));
    if(!data)return;

    const commendations=(data.commendations||[]).map(item=>[
      v2RelatedDate(item.date_received),
      item.award_title,
      item.presented_by,
      item.remarks
    ]);
    v2ReplaceSectionBody(
      v2FindSection('COMMENDATIONS / RECOGNITIONS'),
      v2BuildTable(['Date Received','Award / Title','Presented By','Remarks'],commendations,'No commendation records yet.')
    );

    const officeMovements=v2NormalizeMovements(data.office_movements||[]);
    const movements=officeMovements.map(item=>[
      item.from_camp,
      item.from_office,
      item.to_camp,
      item.to_office,
      item.position,
      v2RelatedDate(item.from_date),
      v2MovementToDate(item.to_date),
      item.remarks
    ]);
    v2ReplaceSectionBody(
      v2FindSection('OFFICE MOVEMENT HISTORY'),
      v2BuildTable(
        ['From Camp','From Office','To Camp','To Office','Position','From Date','To Date','Remarks'],
        movements,
        'No office movement records yet.'
      )
    );

    const assignments=v2ResolveAssignments(officeMovements);
    const currentBadge=v2EnsureCurrentCampBadge();
    const previousBadge=document.getElementById('profileCampBadge');

    if(assignments.conflict){
      setV2Text('profileCurrentOffice',`${assignments.present_count} PRESENT ASSIGNMENTS`);
      setV2Text('profilePreviousOffice','Check OFFICE_MOVEMENT');
      v2SetConflictBadge(currentBadge);
      v2SetConflictBadge(previousBadge);
    }else if(assignments.current){
      setV2Text('profileCurrentOffice',assignments.current.to_office||assignments.current.from_office);
      v2SetCampBadge(currentBadge,assignments.current.to_camp||assignments.current.from_camp);

      if(assignments.previous){
        setV2Text('profilePreviousOffice',assignments.previous.to_office||assignments.previous.from_office);
        v2SetCampBadge(previousBadge,assignments.previous.to_camp||assignments.previous.from_camp);
      }else{
        setV2Text('profilePreviousOffice','—');
        v2SetCampBadge(previousBadge,'');
      }
    }else{
      setV2Text('profileCurrentOffice','—');
      setV2Text('profilePreviousOffice','—');
      v2SetCampBadge(currentBadge,'');
      v2SetCampBadge(previousBadge,'');
    }

    const admin=(data.administrative_documents||[]).map(item=>[
      item.memo_no,
      item.subject_description,
      item.document_from,
      v2RelatedDate(item.date_received)
    ]);
    v2ReplaceSectionBody(
      v2FindSection('ADMINISTRATIVE DOCUMENTS'),
      v2BuildTable(['Doc No.','Title','From','Date'],admin,'No administrative documents recorded yet.')
    );
  }catch(error){
    console.error('Could not load related profile records',error);
  }
}

window.addEventListener('pywebviewready',()=>{
  const modal=document.getElementById('profileModal');
  if(!modal)return;
  new MutationObserver(()=>{
    if(!modal.classList.contains('hidden'))setTimeout(hydrateV2RelatedRecords,0);
  }).observe(modal,{attributes:true,attributeFilter:['class','aria-hidden']});
});

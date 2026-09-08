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

async function hydrateV2RelatedRecords(){
  try{
    if(typeof state==='undefined'||!state.currentBadge||!window.pywebview?.api?.get_profile_related)return;
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

    const movements=(data.office_movements||[]).map((item,index)=>[
      String(index+1),
      item.from_office,
      item.to_office,
      item.position,
      v2RelatedDate(item.from_date),
      v2RelatedDate(item.to_date),
      item.remarks
    ]);
    v2ReplaceSectionBody(
      v2FindSection('OFFICE MOVEMENT HISTORY'),
      v2BuildTable(['#','From Office','To Office','Position','From Date','To Date','Remarks'],movements,'No office movement records yet.')
    );

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

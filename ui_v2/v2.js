document.addEventListener('click',event=>{
  const saveButton=event.target.closest('#savePdfButton');
  if(!saveButton)return;
  event.preventDefault();
  event.stopImmediatePropagation();
  const status=document.getElementById('pdfStatus');
  if(status){status.textContent='Choose “Save as PDF” in the print dialog.';status.className='pdf-status success';}
  window.print();
},true);

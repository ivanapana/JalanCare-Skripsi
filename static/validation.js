/* Website-owned validation: no browser validation bubbles. */
(function(root){
 const words=(en,id,english)=>english?en:id;
 function fieldMessage(field,context={}){
  const en=!!context.english,name=field.name||'',value=String(field.value??''),plain=field.type==='password'?value:value.trim();
  const label=context.label||name||words('This field','Kolom ini',en);
  if(field.disabled||field.type==='hidden'||['submit','button','reset'].includes(field.type))return '';
  if(name==='catatan'&&context.status==='Ditolak'&&!plain)return words('A rejection reason is required.','Alasan penolakan wajib diisi.',en);
  if(name==='catatan'&&context.status==='Selesai'&&!plain)return words('Completion notes are required.','Catatan penyelesaian wajib diisi.',en);
  if(name==='photos'&&context.photoCount!==undefined)return context.photoCount===3?'':words('Select exactly 3 photos.','Pilih tepat 3 foto.',en);
  if(field.required&&((field.type==='checkbox'&&!field.checked)||!plain))return words(label+' is required.',label+' wajib diisi.',en);
  if(!plain)return '';
  if(name==='password'&&(Array.from(value).length<8||Array.from(value).length>128))return words('Password must contain 8–128 characters.','Password harus berisi minimal 8 dan maksimal 128 karakter.',en);
  if(name==='confirm_password'&&value!==context.password)return words('Password confirmation does not match.','Konfirmasi password tidak sama.',en);
  if(field.type==='email'&&!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(plain))return words('Enter a valid email address.','Masukkan alamat email yang valid.',en);
  if(field.minLength>0&&Array.from(value).length<field.minLength)return words(label+' must contain at least '+field.minLength+' characters.',label+' minimal '+field.minLength+' karakter.',en);
  if(field.maxLength>0&&Array.from(value).length>field.maxLength)return words(label+' must not exceed '+field.maxLength+' characters.',label+' maksimal '+field.maxLength+' karakter.',en);
  if(field.type==='number'){
   const number=Number(plain);
   if(!Number.isFinite(number)||field.badInput)return words(label+' must be a number.',label+' harus berupa angka.',en);
   if(field.min!==undefined&&field.min!==''&&number<Number(field.min))return words(label+' must be at least '+field.min+'.',label+' minimal '+field.min+'.',en);
   if(field.step==='1'&&!Number.isInteger(number))return words(label+' must be an integer.',label+' harus berupa bilangan bulat.',en);
  }
  if(name==='kategoriKerusakan'&&plain&&context.sdi!==''&&context.sdi!==undefined){
   const n=Number(context.sdi),expected=n<=50?'Baik':n<=100?'Sedang':n<=150?'Rusak':'Rusak Berat';
   if(Number.isFinite(n)&&n>=0&&plain!==expected)return words('The selected category does not match the survey SDI value.','Kategori yang dipilih tidak sesuai nilai SDI hasil survei.',en);
  }
  return '';
 }
 if(typeof module!=='undefined'&&module.exports)module.exports={fieldMessage};
 if(!root.document)return;
 const english=document.documentElement.lang==='en';let serial=0;
 document.querySelectorAll('form').forEach(form=>{
  form.noValidate=true;
  const fields=()=>Array.from(form.elements).filter(f=>['INPUT','SELECT','TEXTAREA'].includes(f.tagName));
  const context=field=>({english,status:form.elements.namedItem('status')?.value,password:form.elements.namedItem('password')?.value,sdi:form.elements.namedItem('nilaiSDI')?.value,photoCount:field.name==='photos'?field.files.length:undefined,label:field.closest('label')?.querySelector('span')?.textContent.trim()||field.closest('label')?.firstChild?.textContent.trim()||field.name,badInput:field.validity?.badInput});
  const errorFor=field=>fieldMessage(Object.assign({badInput:field.validity?.badInput},{name:field.name,type:field.type,value:field.value,required:field.required,checked:field.checked,disabled:field.disabled,minLength:field.minLength,maxLength:field.maxLength,min:field.min,step:field.step}),context(field));
  function showField(field,message){
   if(!field.dataset.errorId)field.dataset.errorId='field-error-'+(++serial);
   let node=document.getElementById(field.dataset.errorId);
   if(message){
    if(!node){node=document.createElement('small');node.id=field.dataset.errorId;node.className='field-error';field.insertAdjacentElement('afterend',node);}
    node.textContent=message;field.setAttribute('aria-invalid','true');
    const described=(field.getAttribute('aria-describedby')||'').split(' ').filter(Boolean);if(!described.includes(node.id))described.push(node.id);field.setAttribute('aria-describedby',described.join(' '));
   }else{node?.remove();field.removeAttribute('aria-invalid');field.setAttribute('aria-describedby',(field.getAttribute('aria-describedby')||'').split(' ').filter(x=>x&&x!==field.dataset.errorId).join(' '));}
  }
  form.addEventListener('submit',event=>{
   const errors=[];fields().forEach(field=>{const message=errorFor(field);showField(field,message);if(message)errors.push({field,message});});
   let summary=form.querySelector('.form-error-summary');
   if(!errors.length){summary?.remove();return;}
   event.preventDefault();event.stopImmediatePropagation();
   if(!summary){summary=document.createElement('div');summary.className='notice error form-error-summary';summary.setAttribute('role','alert');form.prepend(summary);}
   summary.replaceChildren();const title=document.createElement('b');title.textContent=words('Please check the form.','Periksa kembali isian formulir.',english);summary.append(title);
   const list=document.createElement('ul');errors.forEach(({message})=>{const item=document.createElement('li');item.textContent=message;list.append(item);});summary.append(list);
   for(let node=errors[0].field.parentElement;node;node=node.parentElement)if(node.tagName==='DETAILS')node.open=true;
   errors[0].field.focus();summary.scrollIntoView({block:'nearest',behavior:'smooth'});
  },true);
  function update(){fields().filter(f=>f.getAttribute('aria-invalid')==='true').forEach(field=>showField(field,errorFor(field)));const summary=form.querySelector('.form-error-summary');if(summary){const errors=fields().map(errorFor).filter(Boolean);if(!errors.length)summary.remove();else{const list=summary.querySelector('ul');list.replaceChildren();errors.forEach(message=>{const item=document.createElement('li');item.textContent=message;list.append(item);});}}}
  form.addEventListener('input',update);form.addEventListener('change',update);
 });
})(typeof window==='undefined'?globalThis:window);

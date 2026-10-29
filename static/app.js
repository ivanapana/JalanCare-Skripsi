const english=document.documentElement.lang==='en';
const tr=(id,en)=>english?en:id;
const statusLabels={'Menunggu Verifikasi':'Pending verification','Sedang Ditangani':'In progress','Selesai':'Completed','Ditolak':'Rejected'};
let selectedPhotos=[];
const photoInput=document.querySelector('#photos');
function updateFiles(){if(!photoInput)return;const dt=new DataTransfer();selectedPhotos.forEach(s=>dt.items.add(s.file));photoInput.files=dt.files;photoInput.setCustomValidity(selectedPhotos.length===3?'':tr('Pilih tepat 3 foto.','Select exactly 3 photos.'));document.querySelector('#photo-count').textContent=tr(`${selectedPhotos.length} dari 3 foto dipilih`,`${selectedPhotos.length} of 3 photos selected`);const regions={};selectedPhotos.forEach((s,i)=>regions['foto'+(i+1)]=s.regions);document.querySelector('#blur-regions').value=JSON.stringify(regions);}
function drawPhoto(s){if(!s.img||!s.canvas)return;const ctx=s.canvas.getContext('2d');ctx.drawImage(s.img,0,0,s.canvas.width,s.canvas.height);ctx.strokeStyle='#e44545';ctx.lineWidth=3;s.regions.forEach(([x,y,w,h])=>ctx.strokeRect(x*s.canvas.width,y*s.canvas.height,w*s.canvas.width,h*s.canvas.height));}
function renderPhotos(){const grid=document.querySelector('#photo-preview-grid');if(!grid)return;grid.replaceChildren();for(let i=0;i<3;i++){const card=document.createElement('div');card.className='photo-slot';const s=selectedPhotos[i];if(!s){const empty=document.createElement('div');empty.className='photo-placeholder';empty.textContent=tr('Foto ','Photo ')+(i+1);card.append(empty);grid.append(card);continue;}card.innerHTML='<div class="photo-title"><b></b><button type="button" class="remove-photo"></button></div><canvas></canvas><small class="filename"></small>';
card.querySelector('b').textContent=tr('Foto ','Photo ')+(i+1);card.querySelector('.filename').textContent=s.file.name;
const remove=card.querySelector('.remove-photo');remove.textContent=tr('Hapus foto ×','Remove photo ×');remove.addEventListener('click',()=>{URL.revokeObjectURL(s.url);selectedPhotos.splice(i,1);renderPhotos();updateFiles();previewLocation();});

s.canvas=card.querySelector('canvas');s.canvas.classList.toggle('marking',!!s.marking);let start=null;
const point=e=>{const b=s.canvas.getBoundingClientRect();return [Math.max(0,Math.min(1,(e.clientX-b.left)/b.width)),Math.max(0,Math.min(1,(e.clientY-b.top)/b.height))];};
s.canvas.addEventListener('pointerdown',e=>{if(!s.marking)return;start=point(e);s.canvas.setPointerCapture(e.pointerId);});s.canvas.addEventListener('pointermove',e=>{if(!start)return;drawPhoto(s);const p=point(e);s.canvas.getContext('2d').strokeRect(start[0]*s.canvas.width,start[1]*s.canvas.height,(p[0]-start[0])*s.canvas.width,(p[1]-start[1])*s.canvas.height);});s.canvas.addEventListener('pointerup',e=>{if(!start)return;const p=point(e),box=[Math.min(p[0],start[0]),Math.min(p[1],start[1]),Math.abs(p[0]-start[0]),Math.abs(p[1]-start[1])];if(box[2]>.005&&box[3]>.005)s.regions.push(box);start=null;drawPhoto(s);updateFiles();});s.canvas.addEventListener('pointercancel',()=>{start=null;drawPhoto(s);});
const setDimensions=()=>{s.canvas.width=800;s.canvas.height=Math.round(800*s.img.naturalHeight/s.img.naturalWidth);drawPhoto(s);};if(s.img)setDimensions();else{const img=new Image();img.onload=()=>{s.img=img;setDimensions();};img.src=s.url;}grid.append(card);}updateFiles();}
photoInput?.addEventListener('change',()=>{const incoming=Array.from(photoInput.files);let warning='';for(const file of incoming){if(selectedPhotos.some(s=>s.file.name===file.name&&s.file.size===file.size&&s.file.lastModified===file.lastModified))continue;if(selectedPhotos.length>=3){warning=tr('Maksimal 3 foto. Hapus foto yang salah terlebih dahulu.','Maximum 3 photos. Remove the incorrect photo first.');break;}if(file.size>10*1024*1024){warning=tr('Maksimal 10 MB per foto.','Maximum 10 MB per photo.');continue;}if(!['image/jpeg','image/png'].includes(file.type)){warning=tr('Gunakan foto JPG atau PNG.','Use JPG or PNG photos.');continue;}selectedPhotos.push({file,url:URL.createObjectURL(file),regions:[],marking:false});}renderPhotos();previewLocation();if(warning)document.querySelector('#photo-count').textContent=warning;});
document.querySelector('#report-form')?.addEventListener('submit',e=>{if(selectedPhotos.length!==3){e.preventDefault();document.querySelector('#photo-count').textContent=tr('Pilih tepat 3 foto.','Select exactly 3 photos.');return;}updateFiles();document.querySelector('#analyze-button').disabled=true;document.querySelector('#processing').hidden=false;});
document.querySelectorAll('[data-confirm]').forEach(form=>form.addEventListener('submit',e=>{if(!confirm(form.dataset.confirm))e.preventDefault();}));
document.querySelectorAll('[data-photo-tab]').forEach(button=>button.addEventListener('click',()=>{document.querySelectorAll('[data-photo-panel]').forEach(p=>p.hidden=p.dataset.photoPanel!==button.dataset.photoTab);document.querySelectorAll('[data-photo-tab]').forEach(b=>b.classList.toggle('selected',b===button));}));
const statusSelect=document.querySelector('#staff-status');function staffStatus(){if(!statusSelect)return;const rejected=statusSelect.value==='Ditolak';document.querySelector('#staff-note-label span').textContent=document.querySelector('#staff-note-label').dataset[rejected?'rejected':'normal'];document.querySelector('#staff-note').required=rejected||statusSelect.value==='Selesai';}statusSelect?.addEventListener('change',staffStatus);staffStatus();
const statusNode=document.querySelector('[data-status-url]');if(statusNode&&!window.EventSource)setInterval(async()=>{if(document.hidden)return;try{const res=await fetch(statusNode.dataset.statusUrl,{headers:{Accept:'application/json'}});if(res.ok){const data=await res.json();statusNode.textContent=data.label||(english?statusLabels[data.status]:data.status);statusNode.className='badge '+({'Selesai':'done','Sedang Ditangani':'working','Ditolak':'rejected'}[data.status]||'');const note=document.querySelector('#staff-note-live');if(note)note.textContent=data.note||tr('Belum ada catatan.','No notes yet.');}}catch{}},15000);
const mapNode=document.querySelector('#report-map');
if(mapNode){
 const fallback=document.querySelector('#map-fallback');
 if(typeof L==='undefined')fallback.textContent=tr('Peta belum dapat dimuat. Periksa koneksi internet.','The map could not load. Check your internet connection.');
 else{
  const map=L.map(mapNode,{scrollWheelZoom:false}).setView([1.25,124.8],8),markers=L.layerGroup().addTo(map);let tileFailed=false;
  const tiles=L.tileLayer(mapNode.dataset.tiles,{maxZoom:19,attribution:mapNode.dataset.attribution}).addTo(map);
  tiles.on('tileerror',()=>{tileFailed=true;fallback.textContent=tr('Sebagian peta belum termuat. Titik laporan tetap ditampilkan.','Some map tiles are unavailable. Report markers remain visible.');});
  window.refreshReportMap=(points,fit=false)=>{
   markers.clearLayers();points.forEach(p=>{const label=document.createElement('div');label.textContent=p.label+' · '+(english?(statusLabels[p.status]||p.status):p.status);L.circleMarker([p.lat,p.lon],{radius:7,color:'#2b82cd',fillOpacity:.8}).addTo(markers).bindPopup(label);});
   if(points.length&&fit)map.fitBounds(points.map(p=>[p.lat,p.lon]),{padding:[30,30],maxZoom:15});
   if(!tileFailed)fallback.textContent=points.length?tr('Titik berasal dari GPS EXIF foto.','Locations come from photo GPS EXIF.'):tr('Belum ada titik laporan.','No report locations yet.');
  };
  window.refreshReportMap(JSON.parse(document.querySelector('#map-data').textContent),true);
 }
}

let locationRequest=null;
async function previewLocation(){
 const label=document.querySelector('#location-preview-text'),credit=document.querySelector('#location-preview-credit');
 if(!label)return;
 locationRequest?.abort();credit.hidden=true;
 if(selectedPhotos.length!==3){label.textContent=tr('Pilih tiga foto untuk membaca GPS EXIF dan nama daerah.','Select three photos to read GPS EXIF and the area name.');return;}
 const controller=new AbortController();locationRequest=controller;
 label.textContent=tr('Membaca lokasi pengambilan foto…','Reading photo capture location…');
 const data=new FormData();data.append('csrf',document.querySelector('[name=csrf]').value);selectedPhotos.forEach(p=>data.append('photos',p.file));
 try{const response=await fetch('/api/photos/location',{method:'POST',body:data,signal:controller.signal});const result=await response.json();if(controller!==locationRequest)return;
 if(!response.ok){label.textContent=result.error||tr('Lokasi foto belum dapat dibaca.','Unable to read photo location.');return;}
 label.textContent=(result.alamatLokasi||tr('Nama daerah belum tersedia.','Area name unavailable.'))+' · GPS EXIF: '+result.latitude.toFixed(6)+', '+result.longitude.toFixed(6);
 credit.hidden=result.locationLookup!=='OpenStreetMap / Nominatim';
 }catch(error){if(error.name!=='AbortError')label.textContent=tr('Lokasi belum terbaca. Sistem akan memeriksa ulang saat analisis.','Location not yet available. The system will check again during analysis.');}
}

const viewer=document.querySelector('#photo-viewer');let photoZoom=1;const viewerImage=document.querySelector('#viewer-image');
function setPhotoZoom(value){photoZoom=Math.max(1,Math.min(4,value));viewerImage.style.width=(photoZoom*100)+'%';document.querySelector('#zoom-level').textContent=Math.round(photoZoom*100)+'%';}
document.querySelectorAll('[data-enlarge]').forEach(button=>button.addEventListener('click',()=>{const image=button.querySelector('img');viewerImage.src=image.src;viewerImage.alt=image.alt;setPhotoZoom(1);viewer.showModal();document.querySelector('.viewer-scroll').scrollTo(0,0);}));
document.querySelector('#close-viewer')?.addEventListener('click',()=>viewer.close());
document.querySelectorAll('[data-zoom]').forEach(button=>button.addEventListener('click',()=>setPhotoZoom(photoZoom+(button.dataset.zoom==='+'?.5:-.5))));
viewer?.addEventListener('click',event=>{if(event.target===viewer)viewer.close();});

const liveStatistics=document.querySelector('[data-live-statistics]');
if(window.EventSource&&(document.querySelector('#report-table')||statusNode||liveStatistics)){
 const stream=new EventSource('/api/reports/events');let refreshing=false,pending=false;
 async function refreshPanels(){
  if(!document.querySelector('#report-table')&&!liveStatistics)return;
  if(refreshing){pending=true;return;}refreshing=true;
  try{
   const response=await fetch(location.href,{headers:{'X-Live-Refresh':'1'}});
   if(!response.ok||response.redirected){stream.close();return;}
   const doc=new DOMParser().parseFromString(await response.text(),'text/html');
   for(const selector of ['#report-table tbody','.summary-metrics','#monthly-summary','#regional-summary']){
    const current=document.querySelector(selector),next=doc.querySelector(selector);if(current&&next)current.replaceWith(next);
   }
   const points=doc.querySelector('#map-data');if(points&&window.refreshReportMap)window.refreshReportMap(JSON.parse(points.textContent));
   const message=document.querySelector('#reports-live-message');if(message){message.hidden=false;message.textContent=tr('Laporan dan rekap diperbarui otomatis.','Reports and summaries update automatically.');}
  }catch{const message=document.querySelector('#reports-live-message');if(message){message.hidden=false;message.textContent=tr('Pembaruan belum termuat. Periksa koneksi atau muat ulang halaman.','Updates could not load. Check your connection or reload the page.');}}
  finally{refreshing=false;if(pending){pending=false;refreshPanels();}}
 }
 stream.addEventListener('reports',event=>{
  const rows=JSON.parse(event.data),byId=new Map(rows.map(r=>[r.id,r]));
  document.querySelectorAll('[data-live-report]').forEach(node=>{const report=byId.get(node.dataset.liveReport);if(!report)return;node.textContent=english?statusLabels[report.status]:report.status;node.className='badge '+({'Selesai':'done','Sedang Ditangani':'working','Ditolak':'rejected'}[report.status]||'');});
  if(statusNode){const report=byId.get(statusNode.dataset.liveReport),note=document.querySelector('#staff-note-live');if(report&&note)note.textContent=report.note||tr('Belum ada catatan.','No notes yet.');}
  refreshPanels();
 });
 window.addEventListener('pagehide',()=>stream.close(),{once:true});
}

const reduced=()=>window.matchMedia('(prefers-reduced-motion: reduce)').matches;
const active=new Set();
export function animate(element,frames,options={}){
 if(!element||reduced()||typeof element.animate!=='function')return null;
 const animation=element.animate(frames,{duration:220,easing:'cubic-bezier(.2,.7,.2,1)',...options});active.add(animation);animation.finished.catch(()=>{}).finally(()=>active.delete(animation));return animation;
}
export async function dismissDialog(element,done){
 const a=animate(element,[{opacity:1,transform:'scale(1)'},{opacity:0,transform:'scale(.98)'}],{duration:130});
 if(a)await a.finished.catch(()=>{});done();
}
export function installMotion(root){
 const seen=new WeakSet(),images=new WeakSet(),observed=new WeakSet(),meters=new WeakSet();
 const entrances='.movie-grid > article,.review-entry,.comment,.diary-entry,.list-index-card,.wall-search-film,.comment-thread,.profile-tab-content > section';
 const show=node=>{
  if(seen.has(node))return;seen.add(node);
  const siblings=node.parentElement?Array.from(node.parentElement.children):[];
  const index=Math.min(Math.max(0,siblings.indexOf(node)),7);
  animate(node,[{opacity:0,transform:'translateY(9px)'},{opacity:1,transform:'translateY(0)'}],{delay:index*25,duration:240});
 };
 const intersection=new IntersectionObserver(entries=>entries.forEach(e=>{if(e.isIntersecting){show(e.target);intersection.unobserve(e.target)}}),{threshold:.05});
 function slideTabs(nav){const selected=nav.querySelector('[aria-current="page"]');if(!selected)return;nav.style.setProperty('--tab-left',`${selected.offsetLeft}px`);nav.style.setProperty('--tab-width',`${selected.offsetWidth}px`)}
 const resize=new ResizeObserver(entries=>entries.forEach(e=>slideTabs(e.target)));
 function revealImage(img){if(images.has(img)||!img.complete||!img.naturalWidth)return;images.add(img);animate(img,[{opacity:0},{opacity:1}],{duration:260});if(img.closest('.wall-frame'))animate(img.closest('.wall-frame'),[{filter:'brightness(1.18)',transform:'translateY(-5px) scale(.98)'},{filter:'brightness(1)',transform:'translateY(0) scale(1)'}],{duration:300})}
 function growMeter(meter){if(meters.has(meter)||meter.closest('[hidden]'))return;meters.add(meter);animate(meter,[{transform:'scaleX(0)',transformOrigin:'left'},{transform:'scaleX(1)',transformOrigin:'left'}],{duration:350})}
 function scan(element){if(!(element instanceof Element))return;const select=selector=>[...(element.matches(selector)?[element]:[]),...element.querySelectorAll(selector)];select(entrances).forEach(n=>{if(!observed.has(n)){observed.add(n);intersection.observe(n)}});select('img').forEach(revealImage);select('.profile-tabs').forEach(nav=>{slideTabs(nav);resize.observe(nav)});select('.stats-bar meter').forEach(growMeter)}
 let pageFrame;
 function page(){cancelAnimationFrame(pageFrame);pageFrame=requestAnimationFrame(()=>{root.querySelectorAll('#main > :is(div,section,article)').forEach(el=>{if(el.hidden||el.closest('[hidden]')||el.matches('.search-row,.service-status,.notice,.error-box'))return;animate(el,[{opacity:.35,transform:'translateY(7px)'},{opacity:1,transform:'translateY(0)'}],{duration:200})})})}
 const observer=new MutationObserver(records=>{for(const record of records){if(record.type==='childList'){record.addedNodes.forEach(scan)}else{const el=record.target;if(record.attributeName==='data-motion-view')page();if(record.attributeName==='aria-current'&&el.closest('.profile-tabs'))slideTabs(el.closest('.profile-tabs'));if(record.attributeName==='aria-pressed'&&el.getAttribute('aria-pressed')==='true')animate(el,[{transform:'scale(1)'},{transform:'scale(1.15)'},{transform:'scale(1)'}],{duration:240});if(record.attributeName==='open'&&el.open)animate(el,[{opacity:.25,transform:el.tagName==='DIALOG'?'scale(.97)':'translateY(-4px)'},{opacity:1,transform:'none'}],{duration:200});if(record.attributeName==='src'&&el.tagName==='IMG'){images.delete(el);revealImage(el)}if(record.attributeName==='hidden'&&!el.hidden)scan(el)}}});
 function loaded(e){if(e.target instanceof HTMLImageElement)revealImage(e.target)}
 // Animate both opening and closing without leaving invisible focusable content.
 const closing=new WeakSet();
 function summaryClick(e){const summary=e.target.closest?.('summary');if(!summary)return;const details=summary.parentElement;if(details?.tagName!=='DETAILS'||reduced())return;e.preventDefault();if(closing.has(details))return;if(!details.open){details.open=true;const h=summary.getBoundingClientRect().height;animate(details,[{height:`${h}px`,overflow:'hidden'},{height:`${details.getBoundingClientRect().height}px`,overflow:'hidden'}],{duration:200})}else{closing.add(details);const a=animate(details,[{height:`${details.getBoundingClientRect().height}px`,overflow:'hidden'},{height:`${summary.getBoundingClientRect().height}px`,overflow:'hidden'}],{duration:180});if(a)a.finished.catch(()=>{}).finally(()=>{details.open=false;closing.delete(details)});else{details.open=false;closing.delete(details)}}}
 const preference=matchMedia('(prefers-reduced-motion: reduce)');function changed(){if(preference.matches)active.forEach(a=>a.cancel())}
 scan(root);observer.observe(root,{subtree:true,childList:true,attributes:true,attributeFilter:['aria-current','aria-pressed','open','hidden','src','data-motion-view']});root.addEventListener('load',loaded,true);root.addEventListener('click',summaryClick);preference.addEventListener('change',changed);
 return()=>{observer.disconnect();intersection.disconnect();resize.disconnect();root.removeEventListener('load',loaded,true);root.removeEventListener('click',summaryClick);preference.removeEventListener('change',changed);cancelAnimationFrame(pageFrame);active.forEach(a=>a.cancel())};
}

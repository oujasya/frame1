export const API=(import.meta.env.VITE_API_BASE_URL||'').replace(/\/$/,'');
const cache=new Map(),pending=new Map();
let csrfToken='',csrfPromise=null;
async function ensureCsrf(refresh=false){
 if(refresh)csrfToken='';
 if(csrfToken)return csrfToken;
 if(!csrfPromise)csrfPromise=(async()=>{const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),10000);try{const r=await fetch(`${API}/api/csrf`,{credentials:'include',signal:controller.signal});if(!r.ok)throw new Error('Cannot initialize a secure connection. Please retry.');const data=await r.json();if(!data.csrf_token)throw new Error('Security token unavailable. Please refresh.');csrfToken=data.csrf_token;return csrfToken}finally{clearTimeout(timer);csrfPromise=null}})();
 return csrfPromise;
}

const cacheable=path=>/^\/movies\/(?:\d+|search|trending|popular|top-rated)(?:\?|$)/.test(path);
export async function api(path,options={}){
 if(location.protocol==='file:')throw new Error('Run the FRAME app over HTTP to use live data.');
 const method=options.method||'GET',key=path,allowed=method==='GET'&&cacheable(path),old=allowed?cache.get(key):null;
 if(old&&Date.now()-old.time<120000)return old.data;
 if(allowed&&pending.has(key))return pending.get(key);
 const task=(async()=>{const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),25000);try{
  const write=!['GET','HEAD','OPTIONS'].includes(method.toUpperCase());
  if(write)await ensureCsrf();
  const perform=()=>fetch(`${API}/api${path}`,{credentials:'include',...options,signal:options.signal||controller.signal,headers:{'Content-Type':'application/json',...(write?{'X-CSRFToken':csrfToken}:{}),...options.headers}});
  let r=await perform();
  if(write&&r.status===403){const failure=await r.clone().json().catch(()=>null);if(failure?.code==='CSRF_FAILED'){await ensureCsrf(true);r=await perform()}}

  if(r.status===204)return null;
  if(!r.headers.get('content-type')?.includes('application/json'))throw new Error('Cannot reach the FRAME backend. Please retry.');
  const d=await r.json();
  if(!r.ok){const detail=d?.detail;const message=typeof detail==='string'?detail:detail?.message||(Array.isArray(detail)?detail.map(e=>e.msg).join(' '):'Please check your details and try again.');const error=new Error(message);error.status=r.status;throw error}
  if(allowed){cache.set(key,{time:Date.now(),data:d});while(cache.size>64)cache.delete(cache.keys().next().value)}
  return d;
 }catch(e){if(old&&Date.now()-old.time<1800000&&(!e.status||[429,502,503].includes(e.status)))return {...old.data,_stale:true};if(e.name==='AbortError')throw new Error('This request took too long. Please try again.');if(e instanceof TypeError)throw new Error('Connection failed. Check your internet connection and retry.');throw e}finally{clearTimeout(timer)}})();
 if(allowed)pending.set(key,task);
 try{return await task}finally{if(allowed)pending.delete(key)}
}

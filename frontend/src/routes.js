export function parseRoute(hash=''){
 const raw=hash.replace(/^#/,'')||'/discover';const [path,query='']=raw.split('?');const params=new URLSearchParams(query);
 if(path==='/search')return {view:'search',query:params.get('q')||'',key:query};
 if(path==='/verify-email')return {view:'verify',token:params.get('token')||''};
 if(path==='/recover'||path==='/reset-password')return {view:'reset',token:params.get('token')||''};
 const list=path.match(/^\/lists(?:\/([1-9]\d*))?$/);if(list)return {view:'lists',id:list[1]?Number(list[1]):null};
 const movie=path.match(/^\/movie\/([1-9]\d*)$/);if(movie&&Number.isSafeInteger(Number(movie[1])))return {view:'movie',id:Number(movie[1])};
 const category=path.match(/^\/category\/(trending|popular|country|top-rated)$/);if(category)return {view:'category',category:category[1]};
 const profile=path.match(/^\/u\/([a-zA-Z0-9_]{3,24})$/);if(profile)return {view:'member',username:profile[1].toLowerCase()};
 if(['/discover','/popular','/watchlist','/diary','/settings','/activity','/stats','/login','/signup'].includes(path))return {view:path.slice(1)};
 if(path==='spotlight')return {view:'discover'};
 return {view:'notfound'};
}
export function routeHash(view,options={}){
 if(view==='lists')return '#/lists'+(options.id?'/'+options.id:'');
 if(view==='movie')return `#/movie/${options.id}`;
 if(view==='category')return `#/category/${options.category||'trending'}`;
 if(view==='member')return `#/u/${encodeURIComponent(options.username||'')}`;
 if(view==='reset')return '#/recover';
 if(view==='search'){const p=new URLSearchParams();if(options.query)p.set('q',options.query);return '#/search'+(p.size?'?'+p:'')}
 return '#/'+view;
}

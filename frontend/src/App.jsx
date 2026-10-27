import React,{useEffect,useRef,useState} from 'react';
import {Icon} from '@iconify/react';
import {demoMovies,demoBackdrop} from './demo';
import {DiaryView} from './Journal';
import MoviePage from './MoviePage';
import CountrySelect,{countryName} from './CountrySelect';
import RegionalMovies from './RegionalMovies';
import MovieRow from './MovieRow';
import Navbar from './Navbar';
import HomeHero from './HomeHero';
import Pip from './Pip';
import AuthPage from './AuthPage';
import {VerifyEmailPage} from './EmailSettings';

import MovieAutocomplete from './MovieAutocomplete';
import CategoryPage from './CategoryPage';
import WatchlistView from './WatchlistView';
import SearchPage from './SearchPage';
import AccountSettings,{RecoveryPage} from './AccountSettings';
import {SpoilerProvider,ActivityPage,StatsPage} from './Social';
import ListsPage from './ListsPage';
import './community.css';
import PublicProfilePage from './ProfilePage';
import {parseRoute,routeHash} from './routes';
import {api,API} from './api';
import {animate,dismissDialog} from './motion';
import './watchlist-basics.css';
import './home-hover.css';
import './movie-rails.css';
import './movie-page.css';
import './journal.css';
const DEMO=import.meta.env.VITE_DEMO_MODE!=='false';
const icon=name=><Icon icon={`solar:${name}`} width="20" aria-hidden="true"/>;
function Artwork({movie,hero=false}){
 const [failed,setFailed]=useState(false);
 const path=hero?movie.backdrop_path:movie.poster_path;
 useEffect(()=>setFailed(false),[path]);
 const valid=path&&/^\/[a-zA-Z0-9_.-]+$/.test(path);
 const src=valid?`${API}/api/artwork/tmdb/${hero?'w1280':'w500'}${path}`:null;
 return src&&!failed?<img src={src} alt={hero?'':`${movie.title} poster`} loading={hero?'eager':'lazy'} onError={()=>setFailed(true)}/>:<span className="art-fallback">{hero?'Film image unavailable':`${movie.title} — poster unavailable`}</span>;
}
function Modal({title,onClose,children}){
 const ref=useRef(null);useEffect(()=>{const d=ref.current;d.showModal();return()=>d.close()},[]);
 const closing=useRef(false);function dismiss(){if(closing.current)return;closing.current=true;dismissDialog(ref.current,onClose)}
 return <dialog ref={ref} aria-labelledby="modal-title" onCancel={e=>{e.preventDefault();dismiss()}} onClick={e=>{if(e.target===e.currentTarget)dismiss()}}><div className="modal-head"><h2 id="modal-title">{title}</h2><button className="icon-button" aria-label="Close dialog" onClick={dismiss}>{icon('close-circle-linear')}</button></div>{children}</dialog>;
}
export default function App(){
 const authReturn=useRef('#/discover');
 const [headerPicture,setHeaderPicture]=useState(null);
 const [avatarRevision,setAvatarRevision]=useState(0);
 useEffect(()=>{const refresh=()=>setAvatarRevision(v=>v+1);window.addEventListener('frame:avatar-updated',refresh);return()=>window.removeEventListener('frame:avatar-updated',refresh)},[]);

 const [topRated,setTopRated]=useState([]);
 const [journalRevision,setJournalRevision]=useState(0);
 const [resetToken,setResetToken]=useState('');
 const [searchRouteKey,setSearchRouteKey]=useState('');
 const [listId,setListId]=useState(null);
 function openList(id){setListId(id);navigate('lists',{id})}
 const [profileUsername,setProfileUsername]=useState('');
 function openPublicProfile(username){setProfileUsername(username);navigate('member',{username})}
 const [logIntent,setLogIntent]=useState(false);
 const [category,setCategory]=useState('trending');
 function openCategory(type){setCategory(type);navigate('category',{category:type})}
 const [view,setView]=useState('discover'),[query,setQuery]=useState(''),[term,setTerm]=useState(''),[trending,setTrending]=useState(DEMO?demoMovies.slice(0,6):[]),[popular,setPopular]=useState(DEMO?[...demoMovies].reverse().slice(0,6):[]),[loading,setLoading]=useState(!DEMO),[error,setError]=useState(''),[retry,setRetry]=useState(0),[selected,setSelected]=useState(null),[user,setUser]=useState(null),[profile,setProfile]=useState(false),[saved,setSaved]=useState([]),[notice,setNotice]=useState(''),[busy,setBusy]=useState(false),[formError,setFormError]=useState('');
 useEffect(()=>{let active=true;setHeaderPicture(null);if(user)api(`/profiles/${user.username}/details`).then(d=>{if(active)setHeaderPicture(d.images.avatar||null)}).catch(()=>{});return()=>{active=false}},[user?.id,avatarRevision]);
 useEffect(()=>{api('/auth/me').then(async u=>{setUser(u);setSaved(await api('/watchlist'))}).catch(()=>{})},[]);
 useEffect(()=>{if(DEMO)return;let active=true;setLoading(true);setError('');Promise.allSettled([api('/movies/trending'),api('/movies/popular'),api('/movies/top-rated')]).then(([t,p,r])=>{if(!active)return;if(t.status==='fulfilled')setTrending(t.value.results);if(p.status==='fulfilled')setPopular(p.value.results);if(r.status==='fulfilled')setTopRated(r.value.results);const failed=[t,p,r].find(r=>r.status==='rejected');if(failed)setError(failed.reason.message)}).finally(()=>{if(active)setLoading(false)});return()=>{active=false}},[retry]);
 const returnView=useRef('discover'),returnScroll=useRef(0);
 useEffect(()=>{
  function syncRoute(){
   const route=parseRoute(location.hash);
   if(route.view==='movie'){setSelected(old=>old?.id===route.id?old:{id:route.id,title:'Loading film…'});returnView.current=history.state?.returnView||'discover'}
   else{setSelected(null);returnView.current=route.view;setLogIntent(false)}
   if(route.view==='search'){setTerm(route.query);setQuery(route.query);setSearchRouteKey(route.key||'')}
   if(route.view==='category')setCategory(route.category);
   if(route.view==='lists')setListId(route.id);
   if(route.view==='member')setProfileUsername(route.username);
   if(route.view==='reset'||route.view==='verify')setResetToken(route.token);
   setView(route.view);setError('');
   requestAnimationFrame(()=>window.scrollTo(0,history.state?.scrollY||0));
  }
  syncRoute();window.addEventListener('hashchange',syncRoute);window.addEventListener('popstate',syncRoute);
  return()=>{window.removeEventListener('hashchange',syncRoute);window.removeEventListener('popstate',syncRoute)};
 },[]);
 function rememberScroll(){history.replaceState({...history.state,scrollY:window.scrollY},'',location.href)}
 function openMovie(movie,{log=false}={}){
  setLogIntent(log);rememberScroll();
  if(view!=='movie'){returnView.current=view;returnScroll.current=window.scrollY}
  history.pushState({frameMovie:true,returnView:returnView.current,scrollY:0},'',routeHash('movie',{id:movie.id}));setSelected(movie);setView('movie');setError('');setNotice('');window.scrollTo(0,0);
 }
 function backToBrowse(){
  if(history.state?.frameMovie){history.back()}
  else{history.replaceState({frameView:'discover',scrollY:0},'',routeHash('discover'));setSelected(null);setView('discover');window.scrollTo(0,0)}
 }
 function navigate(v,options={}){if(v==='lists')setListId(options.id||null);rememberScroll();const hash=routeHash(v,options);if(location.hash!==hash)history.pushState({frameView:v,scrollY:0},'',hash);returnView.current=v;setSelected(null);setView(v);setError('');setNotice('');if(v==='reset')setResetToken('');window.scrollTo(0,0)}
 function openAuth(mode){if(!['login','signup','reset','verify'].includes(view))authReturn.current=location.hash||'#/discover';setFormError('');navigate(mode)}
 async function completeAuth(u){setUser(u);let message=`Welcome, ${u.display_name}.`;if('email_verification_sent' in u)message+=u.email_verification_sent?' Check your inbox to verify your email.':' Email verification is pending. Visit Settings for email setup status.';try{setSaved(await api('/watchlist'))}catch{setSaved([]);message+=' Your watchlist could not load. Open Watchlist to retry.'}const target=authReturn.current||'#/discover';history.replaceState({frameView:parseRoute(target).view,returnView:'discover',scrollY:0},'',target);window.dispatchEvent(new PopStateEvent('popstate'));setNotice(message)}
 async function logout(){try{await api('/auth/logout',{method:'POST'});setUser(null);setSaved([]);navigate('discover');setNotice('You have signed out.')}catch(e){setNotice(e.message)}}
 async function toggle(m){if(!user){openAuth('login');return}setBusy(true);try{if(saved.some(s=>s.id===m.id)){await api(`/watchlist/${m.id}`,{method:'DELETE'});setSaved(s=>s.filter(x=>x.id!==m.id));setNotice(`${m.title} removed.`)}else{await api('/watchlist',{method:'POST',body:JSON.stringify({id:m.id,title:m.title,poster_path:m.poster_path,release_date:m.release_date||'',overview:m.overview||'',vote_average:m.vote_average||0})});setSaved(s=>[m,...s]);setNotice(`${m.title} saved to your watchlist.`)}}catch(e){setNotice(e.message)}finally{setBusy(false)}}
 async function saveProfile(e){e.preventDefault();setBusy(true);setFormError('');try{setUser(await api('/profiles/me',{method:'PATCH',body:JSON.stringify(Object.fromEntries(new FormData(e.currentTarget)))}));setProfile(false);setNotice('Profile updated.')}catch(e){setFormError(e.message)}finally{setBusy(false)}}
 function cards(movies,{watchlist=false}={}){return <div className="movie-grid">{movies.map((m,i)=><article key={m.id}><button className="poster" aria-label={`View ${m.title}`} onClick={()=>openMovie(m)}><Artwork movie={m}/><span className="card-index">{String(i+1).padStart(2,'0')}</span><span className="poster-hover-hint" aria-hidden="true">View film <span>↗</span></span></button><div className="card-info"><div><h3><button onClick={()=>openMovie(m)}>{m.title}</button></h3><p>{m.release_date?.slice(0,4)||'Date unknown'}{m.vote_average>0&&` · ${m.vote_average.toFixed(1)} / 10`}</p></div><button className="save-button" aria-label={`${saved.some(s=>s.id===m.id)?'Remove':'Save'} ${m.title}`} aria-pressed={saved.some(s=>s.id===m.id)} disabled={busy} onClick={()=>toggle(m)}>{saved.some(s=>s.id===m.id)?<span className="saved-check" aria-hidden="true">✓</span>:<span className="saved-check" aria-hidden="true">+</span>}</button></div>{watchlist&&<div className="watchlist-actions"><button className="secondary" onClick={()=>openMovie(m,{log:true})}>Mark watched</button></div>}</article>)}</div>}
 function section(title,subtitle,movies){return <section className="shell section"><div className="section-head"><div><p className="eyebrow">{subtitle}</p><h2>{title}<span className="accent">.</span></h2></div><span className="section-label">{DEMO?'THE SAMPLE COLLECTION':'FROM TMDB'}</span></div>{loading&&movies.length===0?<div className="movie-grid" aria-label="Loading films" aria-busy="true">{Array.from({length:6},(_,i)=><div key={i} className="poster skeleton"/>)}</div>:movies.length?((view==='discover'||(view==='movie'&&returnView.current==='discover'))?<MovieRow movies={movies} renderCards={cards} title={title} onDiscover={()=>openCategory(title==='In the spotlight'?'trending':title==='Highest rated'?'top-rated':'popular')}/>:cards(movies)):<div className="empty"><h3>No films here yet.</h3><p>{view==='search'?'Try a different title.':'Discover a film and save it for later.'}</p><button className="secondary" onClick={()=>navigate('discover')}>Browse films</button></div>}</section>}
 const hero=trending[0]?{...trending[0],backdrop_path:DEMO?demoBackdrop:trending[0].backdrop_path}:null;
 return <SpoilerProvider user={user} api={api}><a className="skip" href="#main">Skip to content</a><Navbar view={view} user={user} picture={headerPicture} onPictureError={()=>setHeaderPicture(null)} savedCount={saved.length} onNavigate={navigate} onProfile={openPublicProfile} onAuth={openAuth} onLogout={logout}/><main id="main" data-motion-view={view}>{!['login','signup'].includes(view)&&<><div className="shell search-row"><span className="edition">YOUR NEXT GREAT FILM IS OUT THERE.</span><form role="search" onSubmit={e=>{e.preventDefault();if(query.trim()){setTerm(query.trim());navigate('search',{query:query.trim()})}}}>{icon('magnifer-linear')}<MovieAutocomplete compact label="Search movies" value={query} onChange={setQuery} onSelect={m=>{setQuery(m.title);openMovie(m)}} api={api} Artwork={Artwork} demoMovies={DEMO?demoMovies:null}/><button type="submit" aria-label="Search films">↵</button></form></div><div className="shell service-status">{DEMO?'Sample collection · Accounts and watchlists use the real backend.':'Live movie discovery · Powered by TMDB'}</div></>}{notice&&<p className="shell notice" role="status">{notice}<button className="text-button" onClick={e=>{const toast=e.currentTarget.closest('.notice');const exit=animate(toast,[{opacity:1,transform:'translateY(0)'},{opacity:0,transform:'translateY(-5px)'}],{duration:150});if(exit)exit.finished.catch(()=>{}).finally(()=>setNotice(''));else setNotice('')}}>Dismiss</button></p>}{error&&<div className="shell error-box" role="alert"><p>{error}</p><button className="secondary" onClick={()=>setRetry(r=>r+1)}>Try again</button></div>}{(view==='discover'||(view==='movie'&&returnView.current==='discover'))&&<div className="home-collections" hidden={view!=='discover'}><HomeHero movie={hero} Artwork={Artwork} saved={saved} busy={busy} onOpenMovie={openMovie} onToggle={toggle} onBrowse={()=>{const el=document.getElementById('spotlight');if(el)window.scrollTo({top:el.getBoundingClientRect().top+window.scrollY-105,behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'})}}/><div id="spotlight">{section('In the spotlight','THE CONVERSATION STARTS HERE',trending)}</div><aside className="shell manifesto"><p>For the films you love.<br/><span>And the ones you haven’t met yet.</span></p><span className="edition">COLLECT MOMENTS. KEEP DISCOVERING.</span></aside><RegionalMovies user={user} api={api} renderCards={movies=><MovieRow movies={movies} renderCards={cards} title={`Movies from ${countryName(user?.country)}`} onDiscover={()=>openCategory("country")}/>} onSignup={()=>openAuth('signup')} onProfile={()=>{setFormError('');setProfile(true)}}/>{section('Worth a closer look','POPULAR WITH MOVIE LOVERS',popular)}{!DEMO&&section('Highest rated','TOP RATED BY THE TMDB COMMUNITY',topRated)}</div>}{(view==='category'||(view==='movie'&&returnView.current==='category'))&&<div hidden={view!=='category'}><CategoryPage key={`${category}:${user?.country||''}`} category={category} user={user} api={api} renderCards={cards} onBack={()=>navigate('discover')} demo={DEMO}/></div>}{view==='popular'&&section('The popular collection','FIND YOUR NEXT FAVORITE',popular)}{(view==='search'||(view==='movie'&&returnView.current==='search'))&&<div hidden={view!=='search'}><SearchPage Artwork={Artwork} onOpenMovie={openMovie} key={`${term}:${searchRouteKey}`} term={term} api={api} renderCards={cards} demoMovies={DEMO?demoMovies:null} onRouteChange={filters=>{const params=new URLSearchParams();for(const [key,value] of Object.entries(filters))if(value)params.set(key==='query'?'q':key,value);history.replaceState({...history.state,view:'search'},'',`#/search?${params}`)}}/></div>}{(view==='diary'||(view==='movie'&&returnView.current==='diary'))&&<div hidden={view!=='diary'}><DiaryView refreshToken={journalRevision} user={user} api={api} Artwork={Artwork} onOpenMovie={openMovie} onSignIn={()=>openAuth('login')}/></div>}{(view==='watchlist'||(view==='movie'&&returnView.current==='watchlist'))&&<div hidden={view!=='watchlist'}><WatchlistView user={user} movies={saved} renderCards={movies=>cards(movies,{watchlist:true})} onSignIn={()=>openAuth('login')}/></div>}{(view==='member'||(view==='movie'&&returnView.current==='member'))&&<div hidden={view!=='member'}><PublicProfilePage onEditBasic={()=>{setFormError('');setProfile(true)}} onOpenList={openList} journalRevision={journalRevision} user={user} onLogin={()=>openAuth('login')} key={`${profileUsername}:${user?.id||'guest'}`} username={profileUsername} api={api} Artwork={Artwork} onOpenMovie={openMovie} onBack={()=>navigate('discover')}/></div>}{(view==='lists'||(view==='movie'&&returnView.current==='lists'))&&<div hidden={view!=='lists'}><ListsPage key={listId||'index'} user={user} api={api} listId={listId} onOpenList={openList} onOpenMovie={openMovie} Artwork={Artwork} onLogin={()=>openAuth('login')} onBack={()=>navigate('lists')}/></div>}{(view==='activity'||(view==='movie'&&returnView.current==='activity'))&&<div hidden={view!=='activity'}><ActivityPage user={user} api={api} Artwork={Artwork} onOpenMovie={openMovie} onLogin={()=>openAuth('login')}/></div>}{view==='stats'&&<StatsPage user={user} api={api} onLogin={()=>openAuth('login')}/>}
{['login','signup'].includes(view)&&<AuthPage key={view} mode={view} user={user} api={api} onAuthenticated={completeAuth} onSwitch={openAuth} onRecover={()=>navigate('reset')} onBrowse={()=>navigate('discover')} movies={popular.length?popular:trending} Artwork={Artwork}/>}{view==='verify'&&<VerifyEmailPage key={resetToken} token={resetToken} api={api} user={user} onSettings={()=>navigate('settings')} onLogin={()=>openAuth('login')}/>}{view==='notfound'&&<section className="shell section"><h1>That page is out of frame.</h1><button className="primary" onClick={()=>navigate('discover')}>Back to discover</button></section>}{view==='settings'&&<AccountSettings user={user} api={api} onLogin={()=>openAuth('login')} onDeleted={()=>{setUser(null);setSaved([]);navigate('discover');setNotice('Your account and its data have been deleted.')}}/>}{view==='reset'&&<RecoveryPage api={api} token={resetToken} onLogin={()=>openAuth('login')}/>}{view==='movie'&&selected&&<MoviePage renderCards={cards} focusJournal={logIntent} key={selected.id} movie={selected} user={user} api={api} Artwork={Artwork} onBack={backToBrowse} onToggle={toggle} saved={saved} busy={busy} onSignIn={()=>openAuth('login')} onJournalChanged={()=>{setJournalRevision(r=>r+1);api('/watchlist').then(setSaved).catch(e=>setNotice(e.message))}} demo={DEMO}/>}</main><footer className="shell footer"><button className="logo logo-button" onClick={()=>navigate('discover')}>FRAME</button><p>Made for people who feel something at the movies.</p><div><a href="https://www.themoviedb.org/" target="_blank" rel="noreferrer">Movie data & images: TMDB ↗</a><p>This product uses the TMDB API but is not endorsed or certified by TMDB.</p></div></footer>{profile&&user&&<Modal title="Your profile" onClose={()=>setProfile(false)}><p className="muted">@{user.username} · Public display name and bio</p><button className="secondary" onClick={()=>{setProfile(false);openPublicProfile(user.username)}}>View public profile</button><form className="stack" onSubmit={saveProfile}><label>Display name<input name="display_name" required maxLength={60} defaultValue={user.display_name}/></label><label>Bio<textarea name="bio" rows={4} maxLength={280} defaultValue={user.bio}/></label><CountrySelect value={user.country}/><p className="muted">{saved.length} films in your watchlist</p>{formError&&<p role="alert" className="form-error">{formError}</p>}<button className="primary" disabled={busy}>{busy?'Saving…':'Save profile'}</button></form></Modal>}<Pip user={user} api={api} Artwork={Artwork} saved={saved} movie={selected} view={view} onOpenMovie={openMovie} onNavigate={navigate} onLogin={()=>openAuth('login')} notice={notice} journalRevision={journalRevision} covered={Boolean(profile)||['login','signup','reset','verify'].includes(view)}/></SpoilerProvider>;
}

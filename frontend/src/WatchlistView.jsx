import React,{useState} from 'react';

export default function WatchlistView({user,movies,renderCards,onSignIn}){
 const [layout,setLayout]=useState('posters');
 const [query,setQuery]=useState(''),[year,setYear]=useState('all'),[sort,setSort]=useState('added-newest');
 const years=[...new Set(movies.map(m=>m.release_date?.slice(0,4)).filter(Boolean))].sort().reverse();
 const filtered=movies.map((movie,index)=>({...movie,_added:index})).filter(m=>m.title.toLowerCase().includes(query.trim().toLowerCase())&&(year==='all'||m.release_date?.startsWith(year))).sort((a,b)=>{
  if(sort==='title')return a.title.localeCompare(b.title);
  if(sort==='release-newest')return (b.release_date||'').localeCompare(a.release_date||'');
  if(sort==='rating')return (b.vote_average||0)-(a.vote_average||0);
  if(sort==='added-oldest')return b._added-a._added;
  return a._added-b._added;
 });
 return <section className="shell section watchlist-page"><p className="eyebrow">YOUR PERSONAL SCREENING ROOM</p><h1>{user?`${user.display_name}’s watchlist`:'Make room for great films.'}</h1><p className="muted">{user?'Find your next watch, then log it straight to your diary.':'Sign in to keep a watchlist that follows you.'}</p>{!user?<button className="primary" onClick={onSignIn}>Log in to your watchlist</button>:<><div className="watchlist-controls"><label>Find a film<input type="search" value={query} onChange={e=>setQuery(e.target.value)} placeholder="Search your watchlist"/></label><label>Release year<select value={year} onChange={e=>setYear(e.target.value)}><option value="all">All years</option>{years.map(y=><option key={y}>{y}</option>)}</select></label><label>Sort by<select value={sort} onChange={e=>setSort(e.target.value)}><option value="added-newest">Recently added</option><option value="added-oldest">Added first</option><option value="title">Title A–Z</option><option value="release-newest">Newest release</option><option value="rating">TMDB rating</option></select></label></div><div className="watchlist-toolbar"><p role="status" className="muted text-sm">{filtered.length} of {movies.length} saved films</p><div className="watchlist-view-switch" role="group" aria-label="Watchlist layout"><button aria-pressed={layout==='posters'} onClick={()=>setLayout('posters')}>▦ Posters</button><button aria-pressed={layout==='list'} onClick={()=>setLayout('list')}>☷ List</button></div></div>{filtered.length?<div className={layout==='list'?'watchlist-list-layout':'watchlist-poster-layout'}>{renderCards(filtered)}</div>:<div className="empty"><h2>{movies.length?'No matching films.':'Your next film is waiting.'}</h2><p>{movies.length?'Try a different title or release year.':'Save a film from Discover or Search to start your watchlist.'}</p>{movies.length>0&&<button className="secondary" onClick={()=>{setQuery('');setYear('all')}}>Clear filters</button>}</div>}</>}</section>;
}

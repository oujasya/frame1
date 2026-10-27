import React,{useEffect,useId,useRef,useState} from 'react';

export default function MovieRow({movies,renderCards,onDiscover,title}){
 const viewport=useRef(null),id=useId(),[bounds,setBounds]=useState({left:false,right:false});
 useEffect(()=>{const element=viewport.current;function update(){setBounds({left:element.scrollLeft>4,right:element.scrollLeft+element.clientWidth<element.scrollWidth-4})}update();element.addEventListener('scroll',update,{passive:true});const observer=new ResizeObserver(update);observer.observe(element);return()=>{element.removeEventListener('scroll',update);observer.disconnect()}},[movies.length]);
 function move(direction){const el=viewport.current;el.scrollBy({left:direction*Math.max(180,el.clientWidth*.85),behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'})}
 const grid=renderCards(movies.slice(0,20));
 const end=<article className="discover-more-item" key="discover-more"><button className="poster discover-more-card" onClick={onDiscover}><span className="discover-arrow" aria-hidden="true">↗</span><strong>Discover more</strong><span>{title}</span></button></article>;
 return <div className="movie-rail" role="region" aria-label={`${title} movies`}><button className="rail-arrow rail-left" aria-label={`Scroll ${title} left`} aria-controls={id} disabled={!bounds.left} onClick={()=>move(-1)}>‹</button><div className="rail-viewport" id={id} ref={viewport} tabIndex={0} aria-label="Scroll to browse movies">{React.cloneElement(grid,{},...React.Children.toArray(grid.props.children),end)}</div><button className="rail-arrow rail-right" aria-label={`Scroll ${title} right`} aria-controls={id} disabled={!bounds.right} onClick={()=>move(1)}>›</button></div>;
}

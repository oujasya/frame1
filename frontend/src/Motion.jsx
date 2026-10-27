import React,{useEffect,useLayoutEffect,useRef,useState} from 'react';
import {animate,installMotion} from './motion';
export function Motion(){useEffect(()=>installMotion(document.getElementById('root')),[]);return null}
export function AnimatedCollapse({open,children}){
 const [present,setPresent]=useState(open),container=useRef(null);
 useLayoutEffect(()=>{if(open&&!present){setPresent(true);return}const el=container.current;if(!el)return;el.inert=!open;const height=el.getBoundingClientRect().height;const a=animate(el,open?[{height:'0px',opacity:0,overflow:'hidden'},{height:`${height}px`,opacity:1,overflow:'hidden'}]:[{height:`${height}px`,opacity:1,overflow:'hidden'},{height:'0px',opacity:0,overflow:'hidden'}],{duration:200});if(!open){if(a)a.finished.then(()=>setPresent(false)).catch(()=>{});else setPresent(false)}return()=>a?.cancel()},[open,present]);
 return present?<div ref={container}>{children}</div>:null;
}
export function useListMotion(items){
 const container=useRef(null),positions=useRef(new Map());
 useLayoutEffect(()=>{const next=new Map();container.current?.querySelectorAll('[data-movie-id]').forEach(row=>{const box=row.getBoundingClientRect(),before=positions.current.get(row.dataset.movieId);next.set(row.dataset.movieId,box);if(before&&Math.abs(before.top-box.top)>1)animate(row,[{transform:`translateY(${before.top-box.top}px)`},{transform:'translateY(0)'}],{duration:260})});positions.current=next},[items]);
 return container;
}

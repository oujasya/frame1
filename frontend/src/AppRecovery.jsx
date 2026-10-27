import React,{useEffect,useState} from 'react';
export class ErrorBoundary extends React.Component{
 constructor(props){super(props);this.state={failed:false}}
 static getDerivedStateFromError(){return {failed:true}}
 render(){return this.state.failed?<main className="shell section"><h1>Something went out of frame.</h1><p>Your saved account data is still on the server. Reload the page to recover.</p><button className="primary" onClick={()=>location.reload()}>Reload FRAME</button></main>:this.props.children}
}
export function ConnectivityNotice(){const [online,setOnline]=useState(navigator.onLine);useEffect(()=>{const update=()=>setOnline(navigator.onLine);window.addEventListener('online',update);window.addEventListener('offline',update);return()=>{window.removeEventListener('online',update);window.removeEventListener('offline',update)}},[]);return online?null:<p className="offline-notice" role="status">You’re offline. Previously loaded movie information may still be shown. Reconnect before saving changes.</p>}

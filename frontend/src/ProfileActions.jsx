import React,{useRef,useState} from 'react';
import {API} from './api';

export function CopyProfileLink({username}){
 const [message,setMessage]=useState(''),[fallback,setFallback]=useState(false),[busy,setBusy]=useState(false);
 const link=`${location.origin}${location.pathname}#/u/${encodeURIComponent(username)}`;
 async function copy(){setBusy(true);setMessage('');try{if(!navigator.clipboard?.writeText)throw new Error();await navigator.clipboard.writeText(link);setFallback(false);setMessage('Profile link copied.')}catch{setFallback(true);setMessage('Select the link below and copy it.')}finally{setBusy(false)}}
 return <div className="copy-profile-action"><button type="button" className="secondary" disabled={busy} onClick={copy}>{busy?'Copying…':'Copy profile link'}</button>{message&&<p role="status" className="text-sm">{message}</p>}{fallback&&<label className="copy-profile-fallback">Profile link<input autoFocus readOnly value={link} onFocus={e=>e.target.select()} onClick={e=>e.currentTarget.select()}/></label>}</div>;
}

export function ProfilePicture({profile,image,own,api,onSaved}){
 const input=useRef(null),[busy,setBusy]=useState(false),[message,setMessage]=useState(''),[error,setError]=useState('');
 async function upload(e){const file=e.target.files?.[0];e.target.value='';if(!file)return;setError('');setMessage('');if(!['image/jpeg','image/png','image/webp'].includes(file.type)){setError('Choose a JPG, PNG or WebP image.');return}if(file.size>2097152){setError('Choose an image under 2 MB.');return}setBusy(true);try{const data=await new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(reader.result.split(',')[1]);reader.onerror=()=>reject(new Error('The image could not be read.'));reader.readAsDataURL(file)});await api('/profile/images/avatar',{method:'PUT',body:JSON.stringify({data})});window.dispatchEvent(new Event('frame:avatar-updated'));setMessage('Profile picture updated.');onSaved()}catch(e){setError(e.message)}finally{setBusy(false)}}
 const picture=image?<img src={API+image} alt={`${profile.display_name}'s profile picture`}/>:<span>{profile.display_name.slice(0,1).toUpperCase()}</span>;
 return <div className="profile-picture-control">{own?<><button type="button" className="profile-avatar profile-avatar-edit" disabled={busy} onClick={()=>input.current?.click()} aria-label="Change profile picture">{picture}<span className="profile-avatar-overlay" aria-hidden="true">Change photo</span></button><input hidden ref={input} type="file" accept="image/jpeg,image/png,image/webp" onChange={upload}/><button type="button" className="text-button" disabled={busy} onClick={()=>input.current?.click()}>{busy?'Uploading…':'Change picture'}</button></>:<div className="profile-avatar">{picture}</div>}{message&&<p role="status" className="text-sm">{message}</p>}{error&&<p role="alert" className="form-error text-sm">{error}</p>}</div>;
}

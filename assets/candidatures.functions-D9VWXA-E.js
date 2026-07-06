import{c as n}from"./index-BpXf34zV.js";
const a=[["path",{d:"M13 21h8",key:"1jsn5i"}],["path",{d:"M21.174 6.812a1 1 0 0 0-3.986-3.987L3.842 16.174a2 2 0 0 0-.5.83l-1.321 4.352a.5.5 0 0 0 .623.622l4.353-1.32a2 2 0 0 0 .83-.497z",key:"1a8usu"}]],P=n("pen-line",a),KEY="newair-whitelist-candidatures";
function read(){try{return JSON.parse(localStorage.getItem(KEY)||"[]")}catch{return[]}}
function write(t){localStorage.setItem(KEY,JSON.stringify(t))}
async function api(path,body){try{const r=await fetch(path,{method:body?"POST":"GET",headers:{"content-type":"application/json"},body:body?JSON.stringify(body):void 0});if(r.ok)return await r.json()}catch{}return null}
async function s({data:t}={}){const e=read(),r={id:`wl_${Date.now()}_${Math.random().toString(36).slice(2,8)}`,created_at:new Date().toISOString(),status:"pending",...t};e.unshift(r),write(e);const o=await api("/api/candidatures",{data:r,created_at:r.created_at});return o?.ok?{ok:!0,id:o.id||r.id}:{ok:!0,id:r.id}}
async function g(){const a=await api("/api/candidatures"),t=Array.isArray(a?.rows)?a.rows:read(),e=t.length||1,r=t.filter(o=>o.status==="accepted").length;return{rate:Math.round(r/e*100)}}
async function d({data:t}={}){const e=read(),r=e.find(o=>o.id===t?.id);if(!r)return{ok:!1,error:"Candidature introuvable"};r.status=t.status||r.status,r.reviewed_at=new Date().toISOString(),write(e);await api("/api/candidatures/status",{id:r.id,status:r.status});return{ok:!0,candidature:r}}
export{P,d,g,s};

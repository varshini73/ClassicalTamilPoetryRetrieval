import type { SearchResponse, Stats, PilotQuery } from '../types/api'
const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'
async function call<T>(path:string, init?:RequestInit):Promise<T>{const response=await fetch(`${API}${path}`,init); if(!response.ok) throw new Error((await response.json().catch(()=>null))?.detail || `Request failed (${response.status})`); return response.json()}
export const api = {stats:()=>call<Stats>('/api/dataset/stats'), queries:()=>call<{queries:PilotQuery[];message:string}>('/api/evaluation/queries'), retrieve:(body:object)=>call<SearchResponse>('/api/retrieve',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)})}

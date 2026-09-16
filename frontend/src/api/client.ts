import type { ComparisonResponse, HealthResponse, HistoryResponse, InventoryResponse, ReportsResponse, SampleRepositoriesResponse, ScanResultView, TrendResponse, VulnerabilityIntelligenceResponse } from '../types/api';
export interface SessionPayload { authenticated: boolean; username?: string; csrf_token?: string; expires_at?: number; }
export interface LoginPayload { authenticated: true; username: string; csrf_token: string; expires_in_seconds: number; }
export class ApiError extends Error { readonly status: number; constructor(message: string, status: number) { super(message); this.name='ApiError'; this.status=status; } }
async function parseErrorMessage(response: Response): Promise<string> { try { const payload=(await response.json()) as {detail?:unknown}; if(typeof payload.detail==='string'&&payload.detail.trim()) return payload.detail; } catch { /* Non-JSON error bodies fall back to the generic status message below. */ } return `Request failed with status ${response.status}.`; }
async function requestJson<T>(path:string, init:RequestInit={}):Promise<T>{ const response=await fetch(path,{credentials:'same-origin',...init,headers:{Accept:'application/json',...(init.body?{'Content-Type':'application/json'}:{}),...init.headers}}); if(!response.ok) throw new ApiError(await parseErrorMessage(response),response.status); return (await response.json()) as T; }
function csrfHeaders(token:string):HeadersInit{return {'X-CSRF-Token':token};}
export const getSession=()=>requestJson<SessionPayload>('/api/auth/session');
export const login=(username:string,password:string)=>requestJson<LoginPayload>('/api/auth/login',{method:'POST',body:JSON.stringify({username,password})});
export const logout=(csrfToken:string)=>requestJson<{authenticated:false}>('/api/auth/logout',{method:'POST',headers:csrfHeaders(csrfToken)});
export const getHealth=()=>requestJson<HealthResponse>('/health');
export const getSampleRepositories=()=>requestJson<SampleRepositoriesResponse>('/api/sample-repositories');
export const runScan=(csrfToken:string,targetPath:string,policyPath:string|null,reportFormats:string[])=>requestJson<ScanResultView>('/api/scan',{method:'POST',headers:csrfHeaders(csrfToken),body:JSON.stringify({target_path:targetPath,policy_path:policyPath,report_formats:reportFormats})});
export const runInventory=(csrfToken:string,targetPath:string)=>requestJson<InventoryResponse>('/api/inventory',{method:'POST',headers:csrfHeaders(csrfToken),body:JSON.stringify({target_path:targetPath})});
export const runVulnerabilityIntelligence=(csrfToken:string,targetPath:string,onlineLookup:boolean)=>requestJson<VulnerabilityIntelligenceResponse>('/api/vulnerability-intelligence',{method:'POST',headers:csrfHeaders(csrfToken),body:JSON.stringify({target_path:targetPath,online_lookup:onlineLookup,timeout_seconds:10})});
export const runComparison=(csrfToken:string,baselinePath:string,targetPath:string)=>requestJson<ComparisonResponse>('/api/compare',{method:'POST',headers:csrfHeaders(csrfToken),body:JSON.stringify({baseline_path:baselinePath,target_path:targetPath,baseline_label:'Vulnerable Repo',target_label:'Secure Repo',report_formats:['json','md','html']})});
export const getHistory=(limit=20)=>requestJson<HistoryResponse>(`/api/history?limit=${limit}`);
export const getTrend=(limit=20)=>requestJson<TrendResponse>(`/api/history/trend?limit=${limit}`);
export const getReports=()=>requestJson<ReportsResponse>('/api/reports');

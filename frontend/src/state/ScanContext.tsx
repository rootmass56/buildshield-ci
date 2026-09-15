import { createContext, type ReactNode, useContext, useMemo, useState } from 'react';
import type { ScanResultView } from '../types/api';
interface ScanContextValue { latestScan: ScanResultView | null; setLatestScan: (scan: ScanResultView | null) => void; }
const ScanContext=createContext<ScanContextValue|null>(null);
export function ScanProvider({children}:{children:ReactNode}){ const [latestScan,setLatestScan]=useState<ScanResultView|null>(null); const value=useMemo(()=>({latestScan,setLatestScan}),[latestScan]); return <ScanContext.Provider value={value}>{children}</ScanContext.Provider>; }
export function useScanState(){ const value=useContext(ScanContext); if(!value) throw new Error('useScanState must be used within ScanProvider.'); return value; }

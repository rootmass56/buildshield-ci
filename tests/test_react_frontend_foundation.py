from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; FRONTEND=ROOT/'frontend'; SRC=FRONTEND/'src'
def test_react_feature_files_exist():
 required=['api/client.ts','auth/AuthContext.tsx','state/ScanContext.tsx','components/Ui.tsx','layouts/AppShell.tsx','pages/LoginPage.tsx','pages/OverviewPage.tsx','pages/ScannerPage.tsx','pages/FindingsPage.tsx','pages/PolicyPage.tsx','pages/InventoryPage.tsx','pages/VulnerabilityIntelPage.tsx','pages/ComparePage.tsx','pages/HistoryPage.tsx','pages/ReportsPage.tsx','pages/CicdPage.tsx','pages/AboutPage.tsx','types/api.ts','utils/security.ts','App.tsx','main.tsx'];missing=[x for x in required if not (SRC/x).is_file()];assert not missing
def test_no_raw_html_or_browser_credential_storage():
 for p in SRC.rglob('*'):
  if p.suffix not in {'.ts','.tsx','.js','.jsx'}: continue
  text=p.read_text(encoding='utf-8')
  for token in ['dangerouslySetInnerHTML','.innerHTML','.outerHTML','document.write(','localStorage','sessionStorage']: assert token not in text, f'{p}: {token}'
def test_all_security_workflows_are_routed():
 text=(SRC/'App.tsx').read_text(encoding='utf-8')
 for route in ['scanner','findings','policy','inventory','vulnerability-intelligence','compare','history','reports','cicd','about']: assert f'path="{route}"' in text
def test_api_client_covers_current_backend():
 text=(SRC/'api/client.ts').read_text(encoding='utf-8')
 for path in ['/api/scan','/api/inventory','/api/vulnerability-intelligence','/api/compare','/api/history','/api/history/trend','/api/reports']: assert path in text
 assert 'credentials:' in text and 'X-CSRF-Token' in text
def test_osv_links_are_restricted():
 text=(SRC/'utils/security.ts').read_text(encoding='utf-8'); assert "url.protocol!=='https:'" in text; assert "url.hostname.toLowerCase()!=='osv.dev'" in text
def test_legacy_ui_is_removed_after_h3c_integration():
 legacy=ROOT/'src/supplysentinel/web/static'
 for name in ['index.html','app.js','styles.css','vulnerability-intelligence.js']:
  assert not (legacy/name).exists()

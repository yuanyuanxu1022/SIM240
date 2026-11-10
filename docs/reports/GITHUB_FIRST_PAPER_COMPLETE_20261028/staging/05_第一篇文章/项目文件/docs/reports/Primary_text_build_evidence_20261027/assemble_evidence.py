"""Assemble a bounded retrieval ledger from saved responses; no network or solver."""
from pathlib import Path
from datetime import datetime, timezone
import csv
import hashlib
import json
import re

OUT = Path(__file__).resolve().parent
E = OUT / 'evidence'
papers = []
for number, doi in [(8,'10.1063/1.1399290'), (9,'10.1103/PhysRevE.65.046308'), (10,'10.1115/1.2960953')]:
    oa = json.loads((E/f'ref{number}_openalex.json').read_text())
    s2 = json.loads((E/f'ref{number}_s2.json').read_text())
    assert oa['doi'].lower() == ('https://doi.org/'+doi).lower()
    assert s2['externalIds']['DOI'].lower() == doi.lower()
    papers.append({'reference': number, 'doi': doi, 'title': oa['title'],
        'openalex_oa': oa['open_access'], 's2_pdf': s2['openAccessPdf'],
        'openalex_year': oa['publication_year'], 's2_year': s2['year'],
        's2_authors': [a['name'] for a in s2['authors']],
        'new_full_text_saved_and_visually_verified': False,
        'status': 'OPEN_FULLTEXT' if number != 10 else 'PUBLISHED_METADATA_STRENGTHENED_FULLTEXT_OPEN'})

html = (E/'ref10_institution.html').read_text()
meta = re.findall(r'<meta name="(citation_[^"]+)" content="([^"]*)"', html)
authors = [value for key,value in meta if key=='citation_author']
assert len(authors)==6 and dict(meta)['citation_doi']=='10.1115/1.2960953'
(OUT/'ref10_version_identity.json').write_text(json.dumps({
    'institution_url': 'https://pure.kfupm.edu.sa/en/publications/procedure-for-estimation-and-reporting-of-uncertainty-due-to-disc/',
    'citation_meta':meta, 'published_authors':authors,
    'publication_date':dict(meta)['citation_publication_date'],
    'online_date_field_not_used_as_publication_date':dict(meta)['citation_online_date'],
    'article_number_retained_from_prior_publisher_crossref':'078001',
    'institution_raw_pages':['780011','780014'],
    'version_mapping_established_at_identity_level_only':True,
    'official_manuscript_visual_review':{
        'source':'../Methods_sources_data_audit_20261027/evidence/asme_gci_official_manuscript.pdf',
        'pdf_pages':[3,7], 'printed_manuscript_pages':[1,5], 'authors_count':4,
        'equations_seen':[4,5,6,7],
        'notation_caveat':'Equation (4) defines phi_ext^(21), but (6) prints phi_ext^(12); do not silently transfer or correct this source notation. Published-version comparison remains open.',
        'preview_files':['evidence/asme_manuscript_title.png','evidence/asme_manuscript_gci.png']},
    'published_pdf_downloaded':False,'full_version_equivalence_verified':False},ensure_ascii=False,indent=2)+'\n')

requests = [
  {'target':'ref8','url':'https://api.openalex.org/works/doi:10.1063/1.1399290','http':200,'file':'evidence/ref8_openalex.json'},
  {'target':'ref9','url':'https://api.openalex.org/works/doi:10.1103/PhysRevE.65.046308','http':200,'file':'evidence/ref9_openalex.json'},
  {'target':'ref10','url':'https://api.openalex.org/works/doi:10.1115/1.2960953','http':200,'file':'evidence/ref10_openalex.json'},
]
for n,d in [(8,'10.1063/1.1399290'),(9,'10.1103/PhysRevE.65.046308'),(10,'10.1115/1.2960953')]:
    requests.append({'target':f'ref{n}','url':'https://api.semanticscholar.org/graph/v1/paper/DOI:'+d,
       'params':{'fields':'title,year,externalIds,openAccessPdf,authors'},'http':200,'file':f'evidence/ref{n}_s2.json'})
requests += [
 {'target':'ref8','url':'https://api.archives-ouvertes.fr/search/',
  'params':{'q':'doiId_s:"10.1063/1.1399290"','fl':'title_s,halId_s,uri_s,fileMain_s,docType_s,authFullName_s','wt':'json'},
  'http':200,'records':0,'file':'evidence/ref8_hal.json'},
 {'target':'ref10','url':'https://asmedigitalcollection.asme.org/fluidsengineering/article-pdf/130/7/078001/5491455/078001_1.pdf','http':403,'content_type':'text/html; charset=UTF-8','file':'evidence/ref10_publisher.response'},
 {'target':'ref10','url':'https://citeseerx.ist.psu.edu/document?doi=b9db382f2350e5d948efc2ab11a5abfa3b1389b1&repid=rep1&type=pdf','http':404,'web_tool_http':403,'file':'evidence/ref10_citeseer_404.html','note':'Search index excerpt is a lead; no PDF obtained. Non-PDF response renamed from initial .pdf filename.'},
 {'target':'ref9','url':'https://journals.aps.org/pre/pdf/10.1103/PhysRevE.65.046308','http':None,'curl_exit':35,'error':'SSL_ERROR_SYSCALL; web tool also inaccessible','file':None},
 {'target':'ref9','url':'https://www.researchgate.net/publication/11365084_Discrete_lattice_effects_on_the_forcing_term_in_the_lattice_Boltzmann_method','http':403,'file':'evidence/ref9_researchgate.html','note':'Web search has text snippets; uploader authority/full PDF unverified; excluded from accepted fulltext evidence.'},
 {'target':'ref9','url':'https://iirmas.hust.edu.cn/info/1024/1085.htm','http':None,'curl_exit':35,'error':'SSL_ERROR_SYSCALL; no response file','file':None},
 {'target':'ref9','url':'https://hust-cn.academia.edu/ZGuo','http':403,'file':'evidence/ref9_author_academia.html'},
 {'target':'ref10','url':'https://pure.kfupm.edu.sa/en/publications/procedure-for-estimation-and-reporting-of-uncertainty-due-to-disc/','http':200,'file':'evidence/ref10_institution.html'},
 {'target':'skill_method','url':'https://arxiv.org/abs/2609.00065','http':200,'file':'evidence/skill_method_arxiv.html'},
]
for r in requests:
    if r.get('file'):
        p = OUT / r['file']
        r['bytes'] = p.stat().st_size
        r['sha256'] = hashlib.sha256(p.read_bytes()).hexdigest()
ledger = {'recorded_at_utc':datetime.now(timezone.utc).isoformat(),
    'http_status_source':'Observed tool outputs, with response headers where available; this ledger does not reissue requests',
    'papers':papers,'requests':requests,
    'search_scope':'Targeted exact-title/DOI web queries; OpenAlex and S2 per-DOI; Bouzidi HAL DOI; publisher links and known author/institution records; not an exhaustive search of all repositories',
    'not_accepted':['Third-party OCR/search fragments as a substitute for visually verified originals', 'HTTP 200 metadata as fulltext', 'OA flag as proof a PDF was downloaded'],
    'fetch_parser_initial_failure':'HUST fetch failed, then initial combined parser raised FileNotFoundError before summarising KFUPM; response already saved. Final parser reads existing KFUPM independently.',
    'all_specified_fulltexts_obtained':False}
(OUT/'retrieval_ledger.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
build = json.loads((OUT/'build_evidence.json').read_text())
with (OUT/'binary_group_contract.csv').open('w',newline='') as f:
    w=csv.writer(f); w.writerow(['binary_sha256','run_count','retained_matching_elf','compiler_marker_observed','exact_historical_source_binding','recorded_build_command_and_flags','historical_openlb_dependency_contents','status'])
    for g in build['hash_groups']:
        w.writerow([g['sha256'],g['count'],';'.join(g['matching_elf_paths']),bool(g['matching_elf_paths']),False,False,False,'OPEN'])
print(json.dumps({'request_records':len(requests),'paper_records':len(papers),'published_authors':len(authors),'new_primary_fulltexts':0,'all_closed':False}))

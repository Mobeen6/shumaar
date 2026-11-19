"""Provenance for every district layer: tier (official / computed / inherited / model) and how it was checked.
Writes inds[c].tier and inds[c].check in shumaar/districts.json. Tiers:
  official  - published by the agency; we only divide by population or area
  computed  - computed by us from official microdata or official counts, checked against published totals
  model     - satellite, model or composite estimate; checked against independent figures where possible
"""
import json,re
P='shumaar/districts.json'
d=json.load(open(P)); I=d['inds']

def tier(c,i):
    s=i.get('src') or ''
    if c in ('mpi','mpi_h'): return 'computed'
    if s in ('PSLM 2019-20','HIES 2024-25','PDS 2020','LFS 2020-21 (all areas)','MICS 2016-21'): return 'computed'
    if s.startswith(('Census','District courts','Police','Bureau of Emigration','MNFSR','Health facility','Mouza')): return 'official' if not c.startswith('cg') else 'computed'
    if s.startswith(('PSLM 20','LFS','MICS 2017')): return 'computed'
    return 'model'

CHK={
 # computed from microdata
 'PSLM 2006-07':'Recomputed from PBS microdata with survey weights. Province immunisation matches PBS; Pakistan literacy 54.9 (PBS 55).',
 'PSLM 2008-09':'Recomputed from PBS microdata with survey weights. Province literacy and immunisation match PBS within 1 point (Pakistan literacy 57.2 vs 57; immunisation 77.9 vs 78).',
 'PSLM 2012-13':'Recomputed from PBS microdata with survey weights. Province literacy and immunisation match PBS within 1 point (Pakistan literacy 59.6 vs 60; immunisation 82.5 vs 82).',
 'PSLM 2014-15':'Recomputed from PBS microdata with survey weights. Province literacy, enrolment and immunisation match PBS within 1 point, except Sindh immunisation (72.9 vs 77).',
 'LFS 2024-25':'Recomputed from PBS microdata with survey weights. National check: participation 47.1 (PBS 47.7), women 23.7 (24.4), unemployment 6.8 (6.9), agriculture share 32.4 (33.1).',
 'LFS 2020-21 to 2024-25':'Both years recomputed from PBS microdata with the same definition; 2024-25 national figures within 0.7 points of PBS.',
 'LFS 2020-21':'Recomputed from PBS microdata with survey weights; national unemployment 6.4 (PBS 6.3). Correlates 0.98 with the earlier district file.',
 'MICS 2017-20':'Recomputed from MICS microdata with survey weights following the MICS 6 tabulation plan. Sindh foundational reading 17.7% and numeracy 3.7% match the Sindh MICS snapshot exactly; province fertility matches the reports (Punjab 3.71 vs 3.7).',
 # inherited
 'PSLM 2019-20':'District estimates from PBS PSLM 2019-20 microdata with survey weights; 2019-20 was a district-representative round.',
 'HIES 2024-25':'District estimates from PBS HIES 2024-25 microdata with survey weights, rural areas only. HIES is designed for province estimates, so district samples are smaller; see the margin of error.',
 'PDS 2020':'District estimates from PBS Pakistan Demographic Survey 2020 microdata with survey weights.',
 'LFS 2020-21 (all areas)':'District estimates from PBS LFS 2020-21 microdata with survey weights; Shumaar\'s separate recomputation correlates 0.98.',
 'MICS 2016-21':'District estimates from MICS microdata with survey weights (provincial bureaus and UNICEF); AJK from published tables.',
 # official
 'Census 2023':'Census 2023 district tables as published by PBS; only shares and per-person rates are calculated here.',
 'Mouza Census 2020':'PBS Mouza Census 2020 tehsil tables, summed to districts.',
 'Bureau of Emigration':'Bureau statements to Oct 2026; skill-group totals 2000-2023 match the earlier series exactly. Divided by Census 2023 population.',
 'MNFSR 2024-25':'MNFSR district tables; Punjab rows match the Punjab Crop Reporting Service final estimates 2024-25.',
 'Health facility list 2017':'Counts from the 2017 national facility list, divided by Census 2023 population.',
 'Police 2024 (KP and AJK)':'Police-published district counts, divided by Census 2023 population.',
 # model
 'Satellite (Earth Engine)':'Satellite product summed by district in Google Earth Engine. Checks: CHIRPS rainfall matches PMD normals (Lahore 644 mm, Quetta 234 mm); GHSL built-up and FIRMS fire patterns as expected.',
 'NASA Black Marble 2026':'Satellite measurement, not a survey. Lit area and city footprints checked visually against land cover; background noise removed with a 1 nW cut-off.',
 'NASA Black Marble 2012-26':'Satellite measurement, not a survey. Growth uses three-year averages to damp year-to-year noise.',
 'NASA Black Marble 2026; Census 2023':'Satellite measurement divided by Census 2023 population.',
 'Meta RWI (Chi et al. 2022)':'Model estimate trained on DHS wealth. Rank correlation with PSLM multidimensional poverty -0.76.',
 'Malaria Atlas Project 2019; WorldPop 2020':'Modelled travel time (Weiss et al. 2020) weighted by modelled population (WorldPop). WorldPop correlates 0.98 with Census 2023 district population but is about 19% lower.',
 'UNOSAT 2022':'UNOSAT satellite flood maps (Aug-Nov 2022) combined with modelled population; detects standing water only, so it misses flash floods.',
 'Open GIS data':'Open map data (Natural Earth, OurAirports, WRI power plants); mapped main lines and plants only, not a complete inventory.',
 'Satellite kiln map (2023)':'Peer-reviewed open dataset (Hamdani et al. 2024): kilns detected by model and confirmed on high-resolution images. Zigzag share is far below Punjab government figures, so read it as a lower bound.',
 'Satellite PM2.5 2022, modelled split':'Model estimate: MERRA-2 composition rescaled to AQLI\'s dust-free figures for 25 districts; typical error about 8 percentage points.',
 'AQLI 2024 (25 largest districts)':'Published by EPIC (University of Chicago), Air Quality Life Index fact sheet.',
 'Shumaar index':'A composite index, not a measurement: equal weights, each input scaled 0-10 between the 2nd and 98th percentile, combined by geometric mean (INFORM method).',
}
PM='ACAG/WashU satellite model (ground monitors + satellite). Population-weighted national mean for 2022 is 58.1, against the World Bank\'s 57.9.'
OVR={
 'mpi':'Computed by Shumaar from PSLM 2019-20 microdata (Alkire-Foster method, national MPI indicators). No official district MPI for 2019-20 to compare against.',
 'mpi_h':'Computed by Shumaar from PSLM 2019-20 microdata (Alkire-Foster method, national MPI indicators). No official district MPI for 2019-20 to compare against.',
 'fe_res':'Shumaar calculation: residual from a fit of district fertility on women\'s schooling (MICS microdata). Describes a pattern; not a causal estimate.',
 'fe_tfr':'Recomputed from MICS birth histories. Province TFR matches the MICS reports (Punjab 3.71 vs 3.7; Sindh 3.70 vs 3.7). Districts failing a quality screen (implausible TFR or >30% imputed dates) are withheld.',
 'sat_floodbuild':'Dynamic World flood water x Esri land-cover change. Both are model classifications made independently each year; includes rebuilding on the same site.',
 'sat_croploss':'Esri land cover 2017 vs 2025, classified independently each year, so this is an upper bound.',
 'nl_newlit':'Satellite measurement; lit and dark thresholds (>1 and <0.5 nW) chosen to avoid noise.',
 'cr_mur':'Police-published counts; only KP and AJK publish district figures.',
}
for c,i in I.items():
    i['tier']=tier(c,i)
    s=i.get('src') or ''
    if c in OVR: i['check']=OVR[c]
    elif s.startswith('Satellite PM2.5') and 'split' not in s: i['check']=PM
    elif s.startswith('Census') and c.startswith('cg'): i['check']='Computed from published census counts on fixed district footprints, so that boundary changes do not show up as growth.'
    elif s.startswith('District courts'): i['check']='Law and Justice Commission compilations of provincial court statistics; divided by Census 2023 population.'
    elif s in CHK: i['check']=CHK[s]
    else: print('NO CHECK',c,s)
json.dump(d,open(P,'w'),separators=(',',':'),ensure_ascii=False)
import collections; print(collections.Counter(i['tier'] for i in I.values()))

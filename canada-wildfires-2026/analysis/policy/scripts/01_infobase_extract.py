"""Extract wildfire-relevant federal program spending and results indicators from GC InfoBase open data.
Inputs: raw/infobase/*.csv (open.canada.ca dataset a35cf382-690c-4221-a971-cf0fd189a46f, downloaded 2026-10-22).
Outputs: work/fed_program_spending.csv, work/fed_program_indicators.csv, work/fed_transfer_payments.csv"""
import pandas as pd, re, os
B=os.path.dirname(os.path.abspath(__file__))+'/../'
R=B+'raw/infobase/'
# 1 program spending (DP/DRR)
r=pd.read_csv(R+'rbpo_rppo_en.csv',encoding='utf-8-sig')
keep={'BTL12':'NRCan Wildfire Risk Management','BYP15':'ISC Emergency Management Assistance','BXP09':'ISC Emergency Management Assistance',
      'BVH06':'Health Canada Air Quality','BGS01':'ECCC Air Quality','BTL09':'NRCan Climate Change Adaptation','BTK12':'INFC Disaster Mitigation and Adaptation Fund'}
s=r[r.program_id.isin(keep)].copy()
s['label']=s.program_id.map(keep)
s.to_csv(B+'work/fed_program_spending.csv',index=False)
# 2 indicators with targets and results, joined by indicator id and year
ind=pd.read_csv(R+'programs_indicators.csv',usecols=['year','id','program_code','dept_code','name_en','datatype'])
res=pd.read_csv(R+'programs_results.csv')
codes=['BTL12','BGW08','BYP15','BXP09']
i=ind[ind.program_code.isin(codes)|ind.name_en.str.contains(r'wildfire|wildland|forest fire',case=False,na=False)]
i=i[~i.name_en.str.contains('firearm|fired',case=False,na=False)]
m=i.merge(res[['year','indicator_id','actual_result_value','actual_result_text_en','actual_result_status','planned_result_min_value','planned_result_max_value','planned_result_text_en','planned_result_year']],
          left_on=['year','id'],right_on=['year','indicator_id'],how='left')
m.drop(columns=['indicator_id']).sort_values(['dept_code','program_code','name_en','year']).to_csv(B+'work/fed_program_indicators.csv',index=False)
# 3 transfer payments (Public Accounts)
tp=pd.read_csv(R+'tp_pt_en.csv',encoding='utf-8-sig')
pat=r'wildfire|wildland|FireSmart|Forest Fire Centre|natural disasters|Disaster Mitigation|emergency management assistance|Red Cross.*wildfire'
t=tp[tp.description.str.contains(pat,case=False,na=False)]
t.to_csv(B+'work/fed_transfer_payments.csv',index=False)
print(len(s),len(m),len(t))

"""Insured wildfire losses published by the issuing industry organizations only (CatIQ itself, or IBC releases that
state CatIQ estimates). INDUSTRY DATA, not government statistics. Copies of IBC pages in raw/insured/; CatIQ values
re-used from analysis/losses/insured_losses_wildfire.csv (CatIQ's own posts). 'over'/'close to' kept as stated."""
import os
import pandas as pd
P = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); W = os.path.dirname(os.path.dirname(P))
I = "https://www.ibc.ca/news-insights/news/"
rows = [
 (2023, "NS", "Upper Tantallon wildfire", 165e6, "over", "initial", "2023-07-05", "IBC (CatIQ estimate)", I + "tantallon-wildfire-causes-over-165-million-in-insured-damage"),
 (2023, "BC", "McDougall Creek wildfire (Okanagan)", 480e6, "over", "initial", "2023-10-03", "IBC (CatIQ estimate)", I + "okanagan-and-shuswap-area-wildfires-cause-over-720-million-in-insured-damage"),
 (2023, "BC", "Bush Creek East wildfire (Shuswap)", 240e6, "over", "initial", "2023-10-03", "IBC (CatIQ estimate)", I + "okanagan-and-shuswap-area-wildfires-cause-over-720-million-in-insured-damage"),
 (2023, "NT", "Hay River wildfire", 30e6, "over", "initial", "2023-11-20", "IBC (CatIQ estimate)", I + "behchoko-yellowknife-and-hay-river-wildfires-cause-over-60-million-in-insured-damage"),
 (2023, "NT", "Behchoko-Yellowknife wildfire", 30e6, "over", "initial", "2023-11-20", "IBC (CatIQ estimate)", I + "behchoko-yellowknife-and-hay-river-wildfires-cause-over-60-million-in-insured-damage"),
 (2024, "AB", "Jasper wildfire complex", 1.304e9, "exact", "final (2 years)", "2026-07-23", "CatIQ", "https://public.catiq.com/2026/07/23/catiq-discloses-final-industry-loss-estimate-for-jasper-wildfire-complex-of-july-2024-second-estimate-for-prairies-severe-weather-outbreak-of-june-2026/"),
 (2025, "MB/SK", "Flin Flon wildfire complex (incl. Denare Beach)", 249e6, "exact", "update", "2025-09-04", "IBC (CatIQ estimate)", I + "insured-damage-from-manitoba-and-saskatchewan-wildfires-nears-300-million"),
 (2025, "SK", "Pisew wildfire (La Ronge, Air Ronge, Hall Lake)", 50e6, "over", "initial", "2025-09-04", "IBC (CatIQ estimate)", I + "insured-damage-from-manitoba-and-saskatchewan-wildfires-nears-300-million"),
 (2025, "NL", "Kingston wildfire", 70e6, "over", "initial", "2025-09-17", "IBC (CatIQ estimate)", I + "august-wildfire-in-newfoundland-and-labrador-causes-over-70-million-in-insured-damage"),
 (2026, "BC", "Bald Range wildfire (Summerland)", 293e6, "exact", "second (45-day), was 313 M initial", "2026-10-06", "CatIQ", "https://public.catiq.com/2026/10/06/catiq-discloses-third-loss-estimate-for-june-july-severe-storm-event-in-ontario-and-quebec-updated-loss-for-bald-range-fire/"),
]
d = pd.DataFrame(rows, columns=["year", "prov", "event", "insured_loss_cad", "qualifier", "estimate_stage", "published", "publisher", "source_url"])
d["data_type"] = "industry data (CatIQ / IBC), not government"
d.to_csv(os.path.join(P, "insured_losses_industry.csv"), index=False)
y = d.groupby("year").agg(events=("event", "size"), insured_cad_sum=("insured_loss_cad", "sum")).reset_index()
y["note"] = "sum of published event estimates (lower bound where stated as 'over'); not a complete annual wildfire total"
y.to_csv(os.path.join(P, "insured_losses_industry_by_year.csv"), index=False)
print(d[["year", "event", "insured_loss_cad", "qualifier", "published"]].to_string()); print(y)

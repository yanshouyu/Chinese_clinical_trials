#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 12 13:18:46 2018

@author: yansy
"""

import pandas as pd

# ------------ Trial Metainfo ------------ #

META_CT = {
    "CTRid": None,
    "state": None,
    "drug": None,
    "indication": None,
    "title": None
}

def new_trial_meta(tr=None):
    "return a meta trial as pd.Series from a row or empty Series"
    if tr:
        trialmeta = META_CT.copy()
        recs = tr.find_all("a")
        trialmeta["CTRid"] = recs[0].string.strip()
        trialmeta["state"] = recs[1].string.strip()
        trialmeta["drug"] = recs[2].string.strip()
        trialmeta["indication"] = u" ".join(recs[3].string.strip().split())
        trialmeta["title"] = u" ".join(recs[4].string.strip().split())
        s = pd.Series(trialmeta)
        s.name = recs[0].attrs[u'id']
        return s
    else:
        s = pd.Series(META_CT.copy())
        return s

def new_metaDf():
    "return an empty pd.DataFrame of metainfo fields"
    metaDf = pd.DataFrame(columns=["id", "CTRid", "state", "drug", 
                                   "indication", "title"])
    metaDf.set_index("id", inplace=True)
    return metaDf

# ------------ Trial Detail ------------ #

DETAIL_CT = {
    "id":None,
    "CTRid": None,    # 登记号
    "date_1st_pub": None,    #首次公示信息日期
    "condition": None,    # 适应症
    "brief_title": None,   #试验通俗题目
    "official_title": None,   #试验专业题目
    "org_study_id": None,    #试验方案编号
    "accept_id": None,    #临床申请受理号
    "drugs_name": None,
    "drugs_type": None,
    "sponsors": [],    #申办者名称
    # omit the contacts here
    "purpose": None,    #试验目的
    "phase": None,    # 试验分期
    "study_design_info": {    # 试验设计
        "study_classification": None,    # 试验分类
        "intervention_model": None,    # 设计类型
        "allocation": None,    # 随机化
        "masking": None,    # 盲法
        "scope": None   # 试验范围:  国内试验 
    },
    "eligibility": {
        "minimum_age": None,
        "maximum_age": None,
        "gender": None,
        "healthy_volunteers": None,    # 健康受试者
        "inclusion": [],
        "exclusion": []
    },
    "enrollment_anticipated": None,   #目标入组人数
    "enrollment_real": None,    # 实际入组人数
    # TODO: arms, interventions, outcomes
    "has_dmc": None,    # 数据安全监察委员会（DMC）
    "start_date": None,     # 四、第一例受试者入组日期 
    "completion_date_anticipated": None,     # 五、试验终止日期 
    "researchers": {      #六、研究者信息 
        "lead_researcher": {    # 1、主要研究者信息
            "name": None,
            "agency": None    #单位名称
        },
        "locations": [
#                {"agency":None, 
#                 "researcher":None, 
#                 "address": {"country":None,
#                             "state":None,
#                             "city":None
#                             }
#                 }
                 ]
    },
    # omit the 伦理委员会信息
    "overall_status": None    # 八、试验状态
    # TODO: parse the info update record
}

def new_trial_detail():
    "return an empty trial detail in json structure"
    return DETAIL_CT.copy()
#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
This module is for scraping chinadrugtrials.gov for Chinese clinical trials.

Methods:
    scrape_meta: return a pandas.DataFrame of trials matching the search
    archive_meta: save the metainfo matching the search terms to a file
    get_trial_detail: a list of detailed trial in json format from ckm_ids
    scrape_trial_detail: a list of detailed trials in json matching the search
    archive_trial_detail: save json of detailed trials match the search to a file
    

Created on Thu Apr 12 13:14:52 2018

@author: yansy
"""

from httplib2 import Http
from urllib import urlencode
from bs4 import BeautifulSoup
import bs4
import json
import codecs
import time
import re
import sys

from trial import new_trial_meta, new_metaDf, new_trial_detail


# ------------ Trial Metainfo ------------ #

def format_ct_search_url(**kwargs):
    "return a URL of formatted search terms"
    PATH_HEAD = ("http://www.chinadrugtrials.org.cn/eap/"
                 "clinicaltrials.searchlist?")

    DRUG_TYPE = {u"中药/天然药物": "1", u"化学药物": "2", u"生物制品": "3"}
    if kwargs.has_key("drugs_type"):
        kwargs["drugs_type"] = DRUG_TYPE[kwargs["drugs_type"]]

    for kw in kwargs:
        kwargs[kw] = kwargs[kw].encode("utf-8")
    return PATH_HEAD + urlencode(kwargs)

def adv_search_ct(**kwargs):
    "return a BeautifulSoup of search result page using the params"
    headers = {"Host": "www.chinadrugtrials.org.cn", 
               "Referer": ("http://www.chinadrugtrials.org.cn/eap/"
                           "clinicaltrials.prosearch?pro=y")}
    url = format_ct_search_url(**kwargs)
    h = Http()
    response, content = h.request(uri=url, method='GET', headers=headers)
    if response['status'] == '200':
        return BeautifulSoup(content, "html.parser")
    else:
        return None

def one_page_meta(soup):
    "return a pandas.DataFrame of trials' metainfo in the page"
    tb = soup.find("table", class_="Tab")
    metaDf = new_metaDf()
    for tr in tb.find_all("tr"):
        if tr.has_attr("class") and "Tab_title" in tr.attrs["class"]:
            continue
        # treat the empty table condition
        elif re.search(u"暂无数据", tr.get_text()):
            return None
        else:
            metaDf = metaDf.append(new_trial_meta(tr))
    return metaDf

def cur_page(soup):
    "return the current page number, 1-based"
    slt = soup.find("select", id="current_page", class_="page_select")
    return(int(slt.find("option", selected="selected").string))

def total_page_count(soup):
    "count the total page number"
    slt = soup.find("select", id="current_page", class_="page_select")
    return len(slt.find_all("option"))

def total_ct_count(soup):
    "return the number of total records from the BeautifulSoup object"
    div = soup.find("div", class_="page_left")
    if (re.search(u'共', div.contents[0]) and 
        re.search(u'条记录', div.contents[2])):
        return int(div.find("a").string)
    else:
        return -1

def scrape_meta(sleepsec=0, **kwargs):
    "return a pandas.DataFrame of trials' metainfo matching the search"
    PSIZE = 100
    # first get the total count
    soup = adv_search_ct(**kwargs)
    if soup:
        ctCount = total_ct_count(soup)
    else:
        print >> sys.stderr, "Unable to perform search"
        exit(1)
    
    # get meta data
    kwargs["pagesize"] = unicode(PSIZE)
    metaDf = new_metaDf()
    for pnum in range(ctCount/PSIZE + 1):
        kwargs["currentpage"] = unicode(pnum+1)
        currpagesoup = adv_search_ct(**kwargs)
        metaDf = metaDf.append(one_page_meta(currpagesoup))
        if sleepsec:
            time.sleep(sleepsec)
    return metaDf

def archive_meta(fname, sleepsec=0, **kwargs):
    "save the metainfo matching the search terms to a file"
    metaDf = scrape_meta(sleepsec, **kwargs)
    metaDf.to_csv(fname, sep="\t", encoding="utf-8")

# ------------ Trial Detail ------------ #

def get_trial_detail(ckm_id_list):
    """return a JSON object of the detailed trials in ckm_id list, 
    if no such id or other error, ignore and continue"""
    details = []
    for ckm_id in ckm_id_list:
        content = get_ct_detail_content(ckm_id)
        if content:
            detsoup = BeautifulSoup(content, "html.parser")
            det = parse_trial_info(detsoup)
            det["id"] = ckm_id
            details.append(det)
    return details

def get_ct_detail_content(ckm_id):
    """return the content string of the detailed page for ckm_id, 
    if no such id or other error, return None"""
    headers = {"Host": "www.chinadrugtrials.org.cn", 
               "Referer": "http://www.chinadrugtrials.org.cn/eap/clinicaltrials.searchlist", 
               "Content-Type": "application/x-www-form-urlencoded"}
    url = "http://www.chinadrugtrials.org.cn/eap/clinicaltrials.searchlistdetail"

    MOCKUPBODY = "ckm_index=&pagesize=&currentpage="
    body = "ckm_id=%s&%s" % (ckm_id, MOCKUPBODY)

    h = Http()
    response, content = h.request(uri=url, method='POST', headers=headers, body = body)
    if response['status'] == '200':
        return content
    else:
        return None

def scrape_trial_detail(sleepsec=8, **kwargs):
    "return a list of detailed trials in json matching the search"
    metaDf = scrape_meta(**kwargs)
    ckm_ids = metaDf.index
    details = get_trial_detail(ckm_ids)
    return details

def archive_trial_detail(fname, sleepsec=8, **kwargs):
    "save json of detailed trials match the search to a file"
    details = scrape_trial_detail(sleepsec, **kwargs)
    with codecs.open(fname, "w", encoding="utf-8") as f:
        json.dump(details, f, ensure_ascii=False, indent=4)

# ------------ Parse Trial Detail ------------ #

def parse_trial_info(soup):
    """From the BeautifulSoup object of detailed page, return a python 
    JSON object of the detailed trial"""
    det = new_trial_detail()
    txtlst = get_textlist(soup)
    parse_CTRid(det, txtlst)
    parse_date_of_publicity(det, txtlst)
    parse_condition(det, txtlst)
    parse_titles(det, txtlst)
    parse_org_id(det, txtlst)
    parse_drugs(det, txtlst)
    parse_sponsors(det, txtlst)
    parse_clinical(det, txtlst)
    parse_recr_start_date(det, txtlst)
    parse_anticipated_complete_date(det, txtlst)
    parse_researchers(det, txtlst, soup)
    parse_recr_status(det, txtlst)
    return det

def get_textlist(soup):
    "return a list of string for the BeautifulSoup object"
    strs = soup.get_text().split("\n")
    txtlst = []
    for s in strs:
        s = s.strip()
        if s:
            txtlst.append(s)
    startid = txtlst.index(u"登记号：")
    return txtlst[startid:]

def parse_CTRid(det, txtlst):
    "assign CTRid from text list to trial detail JSON"
    det["CTRid"] = txtlst[txtlst.index(u"登记号：")+1]

def parse_date_of_publicity(det, txtlst):
    "assign time object of the date of publicity to trial detail JSON"
    dop = txtlst[txtlst.index(u"首次公示信息日期：")+1]
    det["date_1st_pub"] = dop

def parse_condition(det, txtlst):
    det["condition"] = txtlst[txtlst.index(u"适应症：")+1]

def parse_titles(det, txtlst):
    "assign brief_title and official_title to trial detail JSON"
    det["brief_title"] = txtlst[txtlst.index(u"试验通俗题目：")+1]
    det["official_title"] = txtlst[txtlst.index(u"试验专业题目：")+1]

def parse_org_id(det, txtlst):
    det["org_study_id"] = txtlst[txtlst.index(u"试验方案编号：")+1]

def parse_drugs(det, txtlst):
    "assign (drugs_name, drugs_type) to trial detail JSON"
    det["drugs_name"] = txtlst[txtlst.index(u"药物名称：")+1]
    det["drugs_type"] = txtlst[txtlst.index(u"药物类型：")+1]

def parse_sponsors(det, txtlst):
    "assign a list of sponsors from 二、申办者信息"
    stid = txtlst.index(u"二、申办者信息") + 2
    edid = txtlst.index(u"联系人姓名：")
    # remove the index and tailing backslash if there is
    splst = [s.strip("/") for s in txtlst[stid:edid] if not re.match(string=s, pattern="[0-9]+")]
    det["sponsors"] = list(set(splst))

def parse_clinical(det, txtlst):
    "directly modify the det JSON object from table: 三、临床试验信息"
    # narrow down the txtlst first
    clinSt = txtlst.index(u"三、临床试验信息") + 1
    clinEd = txtlst.index(u"四、第一例受试者入组日期")
    clinlst = txtlst[clinSt:clinEd]
    det["purpose"] = clinlst[clinlst.index(u"1、试验目的")+1]
    det["phase"] = clinlst[clinlst.index(u"试验分期：")+1]

    parse_clinical_design_info(det, clinlst)
    parse_eligibility(det, clinlst)
    det["enrollment_anticipated"] = clinlst[clinlst.index(u"目标入组人数")+1]
    det["enrollment_real"] = clinlst[clinlst.index(u"实际入组人数")+1]
    # Note that I haven't parsed all the info in this table, leaving arms and endpoints for future
    # Treat has_dmc to boolean
    has_dmc = clinlst[clinlst.index(u"6、数据安全监察委员会（DMC）：")+1]
    if has_dmc == u"有":
        det["has_dmc"] = True
    elif has_dmc == u"无":
        det["has_dmc"] = False
    else:
        det["has_dmc"] = None

def parse_clinical_design_info(det, clinlst):
    "assign clincical design information to detail JSON"
    det["study_design_info"]["intervention_model"] = clinlst[clinlst.index(u"设计类型：")+1]
    det["study_design_info"]["study_classification"] = clinlst[clinlst.index(u"试验分类：")+1]
    det["study_design_info"]["allocation"] = clinlst[clinlst.index(u"随机化：")+1]
    det["study_design_info"]["masking"] = clinlst[clinlst.index(u"盲法：")+1]
    det["study_design_info"]["scope"] = clinlst[clinlst.index(u"试验范围：")+1]

def parse_eligibility(det, clinlst):
    "assign eligibility information to detail JSON"
    # age
    minstr = clinlst[clinlst.index(u"年龄")+1]
    maxstr = clinlst[clinlst.index(u"年龄")+2]
    m = re.search(u"(?P<min>\S+)岁", minstr)
    if m:
        if re.match("[0-9]+$]", m.group("min")):
            det["eligibility"]["minimum_age"] = int(m.group("min"))
    else:
        det["eligibility"]["minimum_age"] = None
        
    m = re.search(u"(?P<max>\S+)岁", maxstr)
    if m:
        if re.match("[0-9]+$", m.group("max")):
            det["eligibility"]["maximum_age"] = int(m.group("max"))
    else:
        det["eligibility"]["minimum_age"] = None
    
    # gender, healthy_volunteers
    det["eligibility"]["gender"] = clinlst[clinlst.index(u"性别")+1]
    det["eligibility"]["healthy_volunteers"] = clinlst[clinlst.index(u"健康受试者")+1]

    # inclusion, exclusion
    incSt = clinlst.index(u"入选标准")+1
    incEd = clinlst.index(u"排除标准")
    det["eligibility"]["inclusion"] = [s for s in clinlst[incSt:incEd] 
                                       if not re.match(string=s, 
                                                       pattern="[0-9]+$")]
    excSt = clinlst.index(u"排除标准")+1
    excEd = clinlst.index(u"目标入组人数")
    det["eligibility"]["exclusion"] = [s for s in clinlst[excSt:excEd] 
                                       if not re.match(string=s, 
                                                       pattern="[0-9]+$")]

def parse_recr_start_date(det, txtlst):
    "date of first participant enrollment"
    doe = txtlst[txtlst.index(u"四、第一例受试者入组日期")+1]
    date_pattern = re.compile("(?P<date>[0-9]{4}-[0-9]{2}-[0-9]{2})")
    m = date_pattern.match(doe)
    if m:
        det["start_date"] = m.group("date")
    else:
        det["start_date"] = None

def parse_anticipated_complete_date(det, txtlst):
    doc = txtlst[txtlst.index(u"五、试验终止日期")+1]
    date_pattern = re.compile("(?P<date>[0-9]{4}-[0-9]{2}-[0-9]{2})")
    m = date_pattern.match(doc)
    if m:
        det["completion_date_anticipated"] = m.group("date")
    else:
        det["completion_date_anticipated"] = None

def parse_researchers(det, txtlst, soup):
    "assign researcher related information to trial detail JSON"
    resSt = txtlst.index(u"六、研究者信息")
    resEd = txtlst.index(u"七、伦理委员会信息")
    reslst = txtlst[resSt:resEd]
    parse_lead_researcher(det, reslst)
    parse_research_locations(det, soup)

def parse_lead_researcher(det, reslst):
    "parse researcher name and agency name"
    leadname = reslst[reslst.index(u"1、主要研究者信息")+2]
    leadagency = reslst[reslst.index(u"单位名称")+1]
    det["researchers"]["lead_researcher"]["name"] = leadname
    det["researchers"]["lead_researcher"]["agency"] = leadagency

def parse_research_locations(det, soup):
    REASERCHER_TABLE_TITLE = [u"序号", u"机构名称", u"主要研究者", 
                              u"国家", u"省（州）", u"城市"]
    REASERCHER_TABLE_STRING = "".join(REASERCHER_TABLE_TITLE)
    
    locRecs = []
    trs = soup.find_all("tr")
    titletr = None
    for tr in trs:
        if len(tr.find_all("td")) == 6:
            titles = [txt.strip() for txt in tr.get_text().strip().split()]
            if "".join(titles) == REASERCHER_TABLE_STRING:
                titletr = tr
                break
    
    if titletr:
        for tr in titletr.next_siblings:
            if isinstance(tr, bs4.element.Tag):
                rec = [td.get_text().strip() for td in tr.find_all("td")]
                # remove redundant
                if rec[1] in [row[1] for row in locRecs]:
                    continue
                else:
                    locRecs.append(rec)
    
    locs = []
    for locrec in locRecs:
        loc = {"agency":None, 
               "researcher": None, 
               "address": {"country":None,
                           "state":None,
                           "city":None}}
        loc["agency"] = locrec[1] if locrec[1] else None
        loc["researcher"] = locrec[2] if locrec[2] else None
        loc["address"]["country"] = locrec[3] if locrec[3] else None
        loc["address"]["state"] = locrec[4] if locrec[4] else None
        loc["address"]["city"] = locrec[5] if locrec[5] else None
        locs.append(loc)
    det["researchers"]["locations"] = locs

def parse_recr_status(det, txtlst):
    statSt = txtlst.index(u"八、试验状态")+1
    statEd = txtlst.index(u"信息更新记录")
    stat = "".join(txtlst[statSt:statEd])
    det["overall_status"] = stat

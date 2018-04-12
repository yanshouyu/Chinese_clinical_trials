
# Overview

This is a data science project aimed to take a look at the Chinese clinical trials published on CFDA's clinical trial information platform [药物临床试验登记与信息公示平台](http://www.chinadrugtrials.org.cn). There will be a preparation phase, an exploratory phase, and an insight generation phase:
1. Preparation: prepare methods, get data, purge data;
1. Exploratory: descriptive analysis on the Chinese clinical trials, get a basic understanding, e.g. data scope, data amount and data accuracy;
1. Insights: tell stories on data, e.g. Chinese clinical trial vs. FDA; proportion of CTs from Chinese or foreign pharma companies; distribution of recruitment. There can be a lot of potential analysis, given adequate data.  

Finally, I plan to create a dashboard for interactive exploration.

This is a *doing-by-learning* project and I hope it to be some initial steps toward a data scientist career.

# Progress update


* 180227: Pilot data scraper. Inital commit.
* 180412: Re-org package `chncts`.

# TODOs:

* Data purging: records from old trials (before 2015) tend to have bad quality. 
* (opt) Set trial date filter in scraper.
* Exploratory data analysis

# Background on www.chinadrugtrials.org.cn

## Website

This website is very old fashioned and doesn't have API. I'll have to scrape data for preparation phase. The website offers search by keywords. We can access trial detail by clicking the returned meta-table.   
To scrape data, I inspected the network and found both GET and POST method can be used. Advanced search from web page used GET method. Secondary search used POST method. To use POST method, make sure the `"Content-Type": "application/x-www-form-urlencoded"` is in request header. GET method can also take all the parameters even some not available from web page.

## Keywords

Param (Default) | Param in Chinese | advanced search on browser | data scrape (GET/POST)
---|---|---|---
reg_no (CTR) | 登记号 | Y | Y
indication | 适应症 | Y | Y
case_no | 试验方案编号 | Y | Y
drugs_name | 药物名称 | Y | Y
drugs_type | 药物类型("中药/天然药物", "化学药物", "生物制品") | Y | Y
appliers | 申办者| Y | Y
communities|伦理委员会| Y | Y
researchers|主要研究者| Y | Y
agencies|临床参加机构| Y | Y
state | 试验状态 | Y | Y
ckm_id |  | | Y
ckm_index| | | Y
sort (desc)| 登记号排序 | | Y
sort2 (desc)| 试验状态排序 | | Y
rule (CTR)| | | Y
currentpage (1)| | | Y
pagesize (20)| | | Y
keywords| 查询关键字 | | Y

## Trial detail structure

Everytime we access the detail page, the server returns an HTML. However, the HTML contains endless recursion of tables. What's worse, there are missing tag ends. Pay special attention to parse by BeautifulSoup.

I store the detail of trials in JSON format. Not all fields of the trial detail are parsed. The JSON schema of a trial is:


```python
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
```

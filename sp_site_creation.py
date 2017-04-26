#!/usr/bin/python
# -*- coding: utf-8 -*-
import requests
import getpass
import logging
from urllib.parse import urlparse
import json
from lxml import etree
import xml.etree.ElementTree as etree
from requests_ntlm import HttpNtlmAuth
import configparser
from logging.handlers import RotatingFileHandler
import time
config = configparser.ConfigParser()
myvars = {}
results = []
empty = ""
#password = input("Enter Password To Run The Site Creation Script--------->")
password = getpass.getpass('Enter Password To Run The Site Creation Script--------->')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s(%(lineno)d) %(message)s')
logger = logging.getLogger('root')
handler = RotatingFileHandler('Log.txt', mode='a', maxBytes=5*1024*1024, 
                                 backupCount=2, encoding=None, delay=0)
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)
with open("site_config.txt") as myfile:
    var = ""
    name = ""
    for line in myfile:
        if(not line.startswith("#")):
            name, var = line.partition(":")[::2]
        
        if (var == empty and not line.startswith("#")):
            myvars['Site Description'] = myvars['Site Description'] + name
       
        myvars[name.strip()] = var
 

username = myvars['Username'].strip(' \t\n\r')
site_name = myvars['Site Name'].strip(' \t\n\r')
site_collection_name = myvars['Site Collection Name'].strip(' \t\n\r')

print(username)
   

    
def GetNTLMAuthToken(base_url):
    #check this path again
    try:
        token_url = base_url + '/_api/contextinfo'
    
        tr = requests.post(token_url, auth=HttpNtlmAuth(username,
                       password), verify=False, timeout=1000)
    
        tokenRoot = etree.fromstring(tr.content)
    
        global token
        token = tokenRoot.find('{http://schemas.microsoft.com/ado/2007/08/dataservices}FormDigestValue'
                       ).text
        global headers
        headers = {'X-RequestDigest': token,
               'Accept': 'application/json; odata=verbose',
               'Content-Type': 'application/json; odata=verbose'}
        logger.debug('Authorization Status Code %s',  token)
    except Exception as e:
        print(e)
        print("Invalid password or authentication. check your password!!!")
        sys.exit(1)
        
def CreateSubSite(base_url):
    post_url = base_url + '_api/web/webinfos/add'
    #print(post_url)
    payload = {'parameters': {
        '__metadata': {'type': 'SP.WebInfoCreationInformation'},
        'Url': myvars['Site URL'].strip(' \t\n\r'),
        'Title': myvars['Site Name'].strip(' \t\n\r'),
        'Description': myvars['Site Description'].strip(' \t\n\r'),
        'Language': 1033,
        'WebTemplate': 'BICENTERSITE',
        'UseUniquePermissions': 'true'
              
        }}

    r = requests.post(post_url, data=json.dumps(payload),
                      auth=HttpNtlmAuth(username,
                      password), headers=headers, verify=False, timeout=60)
    logger.debug("SubSiteCreation Status Code % d", r.status_code)
    return r.status_code
 
# Step 4
def CreateGroup(root_url):    
    post_url = root_url + 'SiteGroups'
    
    title_power_users = site_name + ' Power Users'
    title_report_viewers = site_name + ' Report Viewers'
    

    payload_power_users = {'__metadata': {'type': 'SP.Group'},
                           'Title': title_power_users}
    payload_report_viewers = {'__metadata': {'type': 'SP.Group'},
                              'Title': title_report_viewers}
   
    r1 = requests.post(post_url, data=json.dumps(payload_power_users),
                       auth=HttpNtlmAuth(username,
                       password), headers=headers, verify=True, timeout=180)
    r2 = requests.post(post_url,
                       data=json.dumps(payload_report_viewers),
                       auth=HttpNtlmAuth(username,
                       password), headers=headers, verify=True, timeout=180)
    #print(r1.text)
    logger.debug("Creation of Groups Power Users Status Code %s", str(r1.status_code))
    logger.debug("Creation of Groups Report Viewers Status Code %s" ,  str(r2.status_code))
#Step 4
def AssignPermissionsToTheGroup(root_url):
    title_power_users = site_name + ' Power Users'
    title_report_viewers = site_name + ' Report Viewers'
    title_site_collection_owners = site_collection_name + ' Owners'
    title_site_collection_visitors =site_collection_name + ' Visitors'
    title_site_collection_members = site_collection_name + ' Members'
    post_url_power_users = root_url + 'SiteGroups/getByName(\''+title_power_users+'\')'
    post_url_site_collection_owners = root_url + 'SiteGroups/getByName(\''+title_site_collection_owners+'\')'
    post_url_site_collection_members = root_url + 'SiteGroups/getByName(\''+title_site_collection_members+'\')'
    post_url_site_collection_visitors = root_url + 'SiteGroups/getByName(\''+title_site_collection_visitors+'\')'
    L =list()
    L = [post_url_site_collection_owners, post_url_site_collection_members, post_url_site_collection_visitors]
     
    r = requests.get(post_url_power_users,
                      auth=HttpNtlmAuth(username,
                      password), headers=headers, verify=False, timeout=30)
    value = json.loads(r.text)
    #print(value)
    global power_Id
    power_Id = value['d']['Id']
    post_url_report_viewers = root_url + 'SiteGroups/getByName(\''+title_report_viewers+'\')'
     
    r1 = requests.get(post_url_report_viewers,
                      auth=HttpNtlmAuth(username,
                      password), headers=headers, verify=False, timeout=30)
    value = json.loads(r1.text)
    #print(value)
    global report_Id
    report_Id = value['d']['Id']
    List = list()
    for i in L:
        r = requests.get(i,
                      auth=HttpNtlmAuth(username,
                      password), headers=headers, verify=False, timeout=30)
        value = json.loads(r.text)
        print(value)
        List.append(value['d']['Id'])
        
        
    #below roledefId's are constants as per the sharepoint standards
    assign_permission_power_users_post_url = root_url +"roleassignments/addroleassignment(principalid="+str(power_Id)+", roledefid=1073741930)"
   
    assign_permission_report_viewers_post_url = root_url + "roleassignments/addroleassignment(principalid="+str(report_Id)+",roledefid=1073741929)"
    assign_permission_site_collection_owners_post_url = root_url + "roleassignments/addroleassignment(principalid="+str(List[0])+",roledefid=1073741829)"
    assign_permission_site_collection_visitors_post_url = root_url + "roleassignments/addroleassignment(principalid="+str(List[2])+",roledefid=1073741826)"
    assign_permission_site_collection_members_post_url = root_url + "roleassignments/addroleassignment(principalid="+str(List[1])+",roledefid=1073741827)"
    List2 = list()
    List2 = [assign_permission_site_collection_owners_post_url, assign_permission_site_collection_visitors_post_url,assign_permission_site_collection_members_post_url]
    r2 = requests.post(assign_permission_power_users_post_url, auth=HttpNtlmAuth(username, password), headers = headers, verify=True, timeout=30)
    r3 = requests.post(assign_permission_report_viewers_post_url, auth=HttpNtlmAuth(username, password), headers = headers, verify=True, timeout=30)
    for k in List2:
         r4 = requests.post(k, auth=HttpNtlmAuth(username, password), headers = headers, verify=True, timeout=30)    
    
    logger.debug("Assign permissions to power users status code %s" , str(r2.status_code))
    logger.debug("Assign permissions to report viewers status code %s" , str(r3.status_code))


def AddUsersToTheGroup():
    title_power_users = site_name + 'Power Users'
    title_report_viewers = site_name + 'Report Viewers'
    title_site_collection_owners = site_collection_name + ' Owners'
    title_site_collection_visitors =site_collection_name + ' Visitors'
    title_site_collection_members = site_collection_name + ' Members'
    post_url_power_users = root_url + 'SiteGroups/getByName(\''+title_power_users+'\')'
    post_url_site_collection_owners = root_url + 'SiteGroups/getByName(\''+title_site_collection_owners+'\')'
    post_url_site_collection_members = root_url + 'SiteGroups/getByName(\''+title_site_collection_members+'\')'
    post_url_site_collection_visitors = root_url + 'SiteGroups/getByName(\''+title_site_collection_visitors+'\')'
    L =list()
    L = [post_url_site_collection_owners, post_url_site_collection_members, post_url_site_collection_visitors]
     
    r = requests.get(post_url_power_users,
                      auth=HttpNtlmAuth(username,
                      password), headers=headers, verify=False)
    value = json.loads(r.text)
    global power_Id
    power_Id = value['d']['Id']
    post_url_report_viewers = root_url + 'SiteGroups/getByName(\''+title_report_viewers+'\')'
     
    r1 = requests.get(post_url_report_viewers,
                      auth=HttpNtlmAuth(username,
                      password), headers=headers, verify=False)
    value = json.loads(r1.text)
    global report_Id
    report_Id = value['d']['Id']
    
    add_users_power_users_post_url = root_url + "SiteGroups("+str(power_Id)+")/users"
    add_users_report_viewers_post_url = root_url + "SiteGroups("+str(report_Id)+")/users"
    
    payload_power_users =   { '__metadata':{ 'type': 'SP.User' }, 'Title':myvars['Power Users'], 'Email': 'BI.ENT.Datagov@exchange.asu.edu','LoginName':'c:0+.w'}
    payload_report_viewers = { '__metadata':{ 'type': 'SP.User' }, 'Title':myvars['Report Viewers'], 'Email':'BI.ENT.Datagov@exchange.asu.edu','LoginName':'c:0+.w'}

    r1 = requests.post(add_users_power_users_post_url,data=json.dumps(payload_power_users), auth=HttpNtlmAuth(username,password), headers = headers, verify=True, timeout=30)
    r2 = requests.post(add_users_report_viewers_post_url,data=json.dumps(payload_report_viewers), auth=HttpNtlmAuth(username,password), headers = headers, verify=True, timeout =30)
   

#Step5
def ManageFeatures(root_url):
    #below mentioned value is constant as per sharepoint standards
    post_url = root_url + "features/add(\'c769801e-2387-47ef-a810-2d292d4cb05d\')"
    r = requests.post(post_url, auth=HttpNtlmAuth(username, password), headers = headers, verify=True, timeout=30)
    logger.debug("Report File Sync Feature Status Code %s" , str(r.status_code))
   

#Step 6
def DeleteDashboards(root_url):
    post_url = root_url + 'lists/getByTitle(\'Dashboards\')'
    r1 = requests.post(post_url, auth=HttpNtlmAuth(username, password), headers = headers, verify=True, timeout=30)
    value = json.loads(r1.text)
    Id = value['d']['Id']
    post_url_delete = root_url + 'lists(guid\''+Id+'\')'
    headers_delete = {'X-RequestDigest': token,         
           'IF-MATCH': "*",
           'X-HTTP-Method': 'DELETE'
          }
    r2 = requests.post(post_url_delete, auth=HttpNtlmAuth(username, password), headers = headers_delete, verify=True, timeout=30)
    time.sleep(2)
    logger.debug("Delete Dashboards Library Status Code %s" ,str(r2.status_code))

#Step 8
def DeleteItemInDocumentsLibrary(root_url):
    
    post_url = root_url + 'lists/getByTitle(\'Documents\')/items'
    r1= requests.get(post_url, auth=HttpNtlmAuth(username, password), headers = headers, verify=True, timeout=30)
    value = json.loads(r1.text)
    Id = value['d']['results'][0]['Id']
    post_url_delete = root_url + 'lists/GetByTitle(\'Documents\')/items('+str(Id)+')'
    headers_delete = {'X-RequestDigest': token,         
           'IF-MATCH': "*",
           'X-HTTP-Method': 'DELETE'
          }
    r2= requests.post(post_url_delete, auth=HttpNtlmAuth(username, password), headers = headers_delete, verify=True, timeout=30)
    time.sleep(2)
    logger.debug("Delete Excel Services Sample file from Documents Library %s" , str(r2.status_code))
  
#Step 7
def ModifyingTheViewOfDataConnection(root_url):
    
    post_url_title = root_url + 'lists/GetByTitle(\'Data Connections\')/Views/getByTitle(\'All Items\')/viewfields/removeviewfield(\'Title\')'

    post_url_document_modified_by = root_url + 'lists/GetByTitle(\'Data Connections\')/Views/getByTitle(\'All Items\')/viewfields/removeviewfield(\'Modified_x0020_By\')'

    post_url_keywords = root_url + 'lists/GetByTitle(\'Data Connections\')/Views/getByTitle(\'All Items\')/viewfields/removeviewfield(\'Keywords\')'
    
    post_url_modified_by = root_url + 'lists/GetByTitle(\'Data Connections\')/Views/getByTitle(\'All Items\')/viewfields/addviewfield(\'Editor\')'
    headers_merge = {'X-RequestDigest': token,         
               'Accept': 'application/json; odata=verbose',
               'Content-Type': 'application/json; odata=verbose',
                'IF-MATCH':"*",
                'X-HTTP-Method': 'MERGE'
           }
   
  
    headers_delete = {'X-RequestDigest': token,         
               'Accept': 'application/json; odata=verbose',
               'Content-Type': 'application/json; odata=verbose',
                'IF-MATCH':"*",
                'X-HTTP-Method': 'DELETE'
           }
    
    r2 = requests.post(post_url_title, auth=HttpNtlmAuth(username, password), headers = headers_delete, verify=True, timeout=30)
    time.sleep(2)
    r3 = requests.post(post_url_document_modified_by, auth=HttpNtlmAuth(username, password), headers = headers_delete, verify=True, timeout=30)
    time.sleep(2)
    r4 = requests.post(post_url_keywords, auth=HttpNtlmAuth(username, password), headers = headers_delete, verify=True, timeout=30)
    time.sleep(2)
    r5 = requests.post(post_url_modified_by, auth=HttpNtlmAuth(username, password), headers = headers_merge, verify=True, timeout=30)
    logger.debug("Remove Title from DataConnection %s" , str(r2.status_code))
    logger.debug("Remove Document Modified BY From Data Connection %s" , str(r3.status_code))
    logger.debug("Remove keywords BY From Data Connection %s", str(r4.status_code))
    
    logging.debug("Add Modified BY To Data Connection %s"  , str(r5.status_code))
#Step 7
def ModifyContentTypeOfTheList(root_url):
    post_url_id = root_url + "AvailableContentTypes?$select=Name, Id, StringId&$filter=Name eq 'Report Data Source'"
  
    r1 = requests.get(post_url_id, auth=HttpNtlmAuth(username, password), headers = headers, verify=True, timeout=30)
   
    value = json.loads(r1.text)
    Id = value['d']['results'][0]['StringId']
    post_url_update = root_url + 'lists/GetByTitle(\'Data Connections\')/contenttypes/addAvailableContentType(\''+Id+'\')'
    time.sleep(2)
    r2 = requests.post(post_url_update, auth=HttpNtlmAuth(username, password), headers = headers, verify=True, timeout=30)
    time.sleep(2)    
    post_url_id_2 = root_url + "AvailableContentTypes?$select=Name, Id, StringId&$filter=Name eq 'BI Semantic Model Connection'"  
    r3 = requests.get(post_url_id_2, auth=HttpNtlmAuth(username, password), headers = headers, verify=True, timeout=30)
    value = json.loads(r3.text)
    Id = value['d']['results'][0]['StringId']
    post_url_update_2 = root_url + 'lists/GetByTitle(\'Data Connections\')/contenttypes/addAvailableContentType(\''+Id+'\')'
    time.sleep(2)
    r4 = requests.post(post_url_update_2, auth=HttpNtlmAuth(username, password), headers = headers, verify=True, timeout=30)
    logger.debug("Content Type Of Data COnnections %s" , str(r4.status_code))
#Step 7 & Step 11 & step 10
def updateListVersion(root_url):
    post_url_update = root_url + 'lists/getByTitle(\'Data Connections\')'
    post_url_update_1 = root_url + 'lists/getByTitle(\'PerformancePoint Content\')'
    post_url_update_2 = root_url + 'lists/getByTitle(\'Pages\')'
    payload = {
        '__metadata': {'type': 'SP.List'},
        'MajorVersionLimit' : 10
        }
    headers_merge = {'X-RequestDigest': token,         
               'Accept': 'application/json; odata=verbose',
               'Content-Type': 'application/json; odata=verbose',
                'IF-MATCH':"*",
                'X-HTTP-Method': 'MERGE'
           }
    r = requests.post(post_url_update, data=json.dumps(payload),
                      auth=HttpNtlmAuth(username,
                      password), headers=headers_merge, verify=False, timeout=30)
    time.sleep(2)
    logger.debug ("List Version settings of Data COnnections %s" ,str(r.status_code))
   
    r = requests.post(post_url_update_1, data=json.dumps(payload),
                      auth=HttpNtlmAuth(username,
                      password), headers=headers_merge, verify=False, timeout=30)
    time.sleep(2)
    logger.debug ("List Version settings of Performance Content %s" ,str(r.status_code))
 
    r = requests.post(post_url_update_2, data=json.dumps(payload),
                      auth=HttpNtlmAuth(username,
                      password), headers=headers_merge, verify=False, timeout=30)
    time.sleep(2)
    logging.debug("List Version settings of pages %s" ,str(r.status_code))
def ChangeDraftVersionVisibilityOfPages(root_url):
    payload = {
        '__metadata': {'type': 'SP.List'},
        'EnableMinorVersions' : 'false',
        'DraftVersionVisibility': 0
        }
    post_url_update = root_url + 'lists/getByTitle(\'Pages\')'
    headers_merge = {'X-RequestDigest': token,         
               'Accept': 'application/json; odata=verbose',
               'Content-Type': 'application/json; odata=verbose',
                'IF-MATCH':"*",
                'X-HTTP-Method': 'MERGE'
           }
    r = requests.post(post_url_update, data=json.dumps(payload),
                      auth=HttpNtlmAuth(username,
                      password), headers=headers_merge, verify=False, timeout=30)
    time.sleep(5)
    logger.debug("Change Draft Version visibility of Pages %s" ,str(r.status_code))

def AddNavigationQuickLaunchAttribute(base_url, root_url):
    server_relative_url = base_url+ '/_api/web/webinfos'
   
    r1 = requests.get(server_relative_url, auth=HttpNtlmAuth(username, password), headers = headers, verify=True, timeout=30)
    value = json.loads(r1.text)
    for row in value['d']['results']:
        if(row['Title'] == myvars['Site Name'].strip(' \t\n\r')):
            Id= row['ServerRelativeUrl']
    post_url_update = root_url + "navigation/QuickLaunch"
  
    payload = {
        '__metadata':{'type': 'SP.NavigationNode'},
        'Title': 'Pages',
        'Url': Id + '/Pages/Forms/AllItems.aspx'
       
        }
    payload_content_repository = {
        '__metadata':{'type': 'SP.NavigationNode'},
        'Title': 'Content Repository',
        'Url': Id + '/Content Repository/Forms/AllItems.aspx'
       
        }
    time.sleep(2)
    r = requests.post(post_url_update, data=json.dumps(payload),
                      auth=HttpNtlmAuth(username,
                      password), headers=headers, verify=False, timeout=30)
    logger.debug("Navigation Inheritance of pages %s" ,str(r.status_code))
    time.sleep(2)
    r = requests.post(post_url_update, data=json.dumps(payload_content_repository),
                      auth=HttpNtlmAuth(username,
                      password), headers=headers, verify=False, timeout=30)
    logger.debug("Navigation Inheritance of Content Repository %s" ,str(r.status_code))
                                        
#step 9
def CreateDashBoardsLibrary(root_url):
    post_url = root_url + 'lists'
    payload =  {'__metadata': { 'type': 'SP.List' },
                'TemplateFeatureId' : 'F979E4DC-1852-4F26-AB92-D1B2A190AFC9',
                'BaseTemplate' : '480',
                'BaseType':1,
                'MajorVersionLimit' : 10,
                'Description': 'Content Repository library stores your reports, dashboards, models, excel files and documents',
                'Title': 'Content Repository'}
    string = len(json.dumps(payload))
    headers = {'X-RequestDigest': token,         
           'Accept': 'application/json; odata=verbose',
           'Content-Type': 'application/json; odata=verbose',
           'Content-Length': str(string)}
    time.sleep(2)
    r = requests.post(post_url, data=json.dumps(payload),
                      auth=HttpNtlmAuth(username,
                      password), headers=headers, verify=False, timeout=5)
    logger.debug("Create Content Repository %s" ,str(r.status_code))
   
#Step 9
def ModifyDashBoardsLibraryContentType(root_url):
    post_url_id = root_url + "AvailableContentTypes?$select=Name, Id, StringId&$filter=Name eq 'Report Builder Report'"
    r1 = requests.get(post_url_id, auth=HttpNtlmAuth(username, password), headers = headers, verify=True, timeout=30)
 
    value = json.loads(r1.text)
    Id = value['d']['results'][0]['StringId']
    post_url_update = root_url + 'lists/GetByTitle(\'Content Repository\')/contenttypes/addAvailableContentType(\''+Id+'\')'
    time.sleep(2)
    r2 = requests.post(post_url_update, auth=HttpNtlmAuth(username, password), headers = headers, verify=True, timeout=30)
    logger.debug("Content Repository Content Type to Report Builder Report %s" , str(r2.status_code))
  
    post_url_id_2 = root_url + "AvailableContentTypes?$select=Name, Id, StringId&$filter=Name eq 'BI Semantic Model Connection'"
    time.sleep(2)
    r3 = requests.get(post_url_id_2, auth=HttpNtlmAuth(username, password), headers = headers, verify=True, timeout=30)
    value = json.loads(r3.text)
    Id = value['d']['results'][0]['StringId']
    post_url_update_2 = root_url + 'lists/GetByTitle(\'Content Repository\')/contenttypes/addAvailableContentType(\''+Id+'\')'
    time.sleep(2)
    r4 = requests.post(post_url_update_2, auth=HttpNtlmAuth(username, password), headers = headers, verify=True, timeout=30)
    logger.debug("Content Repository Content Type to BI Semantic Model Connection %s" ,str(r4.status_code))
    post_url_id_2 = root_url + "AvailableContentTypes?$select=Name, Id, StringId&$filter=Name eq 'PowerPivot Gallery Document'"
    time.sleep(2)
    r3 = requests.get(post_url_id_2, auth=HttpNtlmAuth(username, password), headers = headers, verify=True, timeout=30)
    value = json.loads(r3.text)
    Id = value['d']['results'][0]['StringId']
    post_url_update_2 = root_url + 'lists/GetByTitle(\'Content Repository\')/contenttypes/addAvailableContentType(\''+Id+'\')'
    time.sleep(2)
    r4 = requests.post(post_url_update_2, auth=HttpNtlmAuth(username, password), headers = headers, verify=True, timeout=30)
    logger.debug("Content Repository Content Type to PowerPivot Gallery Document %s" , str(r4.status_code))

#Step 9
def ModifyDashBoardsLibraryView(root_url):
      
    post_url_title = root_url + 'lists/GetByTitle(\'Content Repository\')/Views/getByTitle(\'All Items\')/viewfields/removeviewfield(\'Title\')'
    post_url_keywords = root_url + 'lists/GetByTitle(\'Content Repository\')/Views/getByTitle(\'All Items\')/viewfields/removeviewfield(\'Keywords\')'
    
   
    post_url_pages_columns_contact = root_url + 'lists/GetByTitle(\'Pages\')/Views/getByTitle(\'All Documents\')/viewfields/removeviewfield(\'PublishingContact\')'
    post_url_pages_columns_pagelayout = root_url + 'lists/GetByTitle(\'Pages\')/Views/getByTitle(\'All Documents\')/viewfields/removeviewfield(\'PublishingPageLayout\')'
    headers_delete = {'X-RequestDigest': token,         
               'Accept': 'application/json; odata=verbose',
               'Content-Type': 'application/json; odata=verbose',
                'IF-MATCH':"*",
                'X-HTTP-Method': 'DELETE'
           }
    time.sleep(2)
    r2 = requests.post(post_url_title, auth=HttpNtlmAuth(username, password), headers = headers_delete, verify=True, timeout=30)
    time.sleep(2)
    r4 = requests.post(post_url_keywords, auth=HttpNtlmAuth(username, password), headers = headers_delete, verify=True, timeout=30)
    time.sleep(2)
    r5 = requests.post(post_url_pages_columns_contact, auth=HttpNtlmAuth(username, password), headers = headers_delete, verify=True,timeout=30)
    time.sleep(2)
    r6 = requests.post(post_url_pages_columns_pagelayout, auth=HttpNtlmAuth(username, password), headers = headers_delete, verify=True,timeout=30)
    time.sleep(2)
    logger.debug("Remove Title from COntent Repository %s" , str(r2.status_code))
    logger.debug("Remove contact from DataConnection %s" ,str(r5.status_code))
    logger.debug("Remove pagelayout from DataConnection %s"  ,str(r6.status_code))
#step 10


def DeleteItemsFromPageList(base_url, root_url):
    #TODO: change SANDBOX, RAGINI DEMO TEST to variables
    server_relative_url = base_url + '/_api/web/webinfos'
   
    r1 = requests.get(server_relative_url, auth=HttpNtlmAuth(username, password), headers = headers, verify=True, timeout=30)
    value = json.loads(r1.text)
    for row in value['d']['results']:
        if(row['Title'] == myvars['Site Name'].strip(' \t\n\r')):
            Id= row['ServerRelativeUrl']
    
    post_url_excelfile = root_url + 'GetFileByServerRelativeUrl(\'/'+Id+'/Pages/excelservicessample.aspx\')'
    post_url_ppssample = root_url + 'GetFileByServerRelativeUrl(\'/'+Id+ '/Pages/ppssample.aspx\')'
    #post_url_default = root_url + 'GetFileByServerRelativeUrl(\'/'+config['Credentials']['Site URL']+ config['Credentials']['Site Name']+'/Pages/default.aspx\')'
    headers_delete = {'X-RequestDigest': token,         
               'Accept': 'application/json; odata=verbose',
               'Content-Type': 'application/json; odata=verbose',
                'IF-MATCH':"*",
                'X-HTTP-Method': 'DELETE'
           }
    time.sleep(2)    
    r2 = requests.post(post_url_excelfile, auth=HttpNtlmAuth(username, password), headers = headers_delete, verify=True, timeout=30)
    time.sleep(2)
    r4 = requests.post(post_url_ppssample, auth=HttpNtlmAuth(username, password), headers = headers_delete, verify=True, timeout=30)
    #r3 = requests.post(post_url_default, auth=HttpNtlmAuth(username, password), headers = headers_delete, verify=True)
    logger.debug("Delete excelservicessample from page %d", r2.status_code)
    #print(r3.text)
    logger.debug("Delete ppsample from Page %d", r4.status_code)
    #print(r3.status_code)

def CreateHomePage(base_url,root_url):
    server_relative_url = base_url+ '/_api/web/webinfos'
   
    r1 = requests.get(server_relative_url, auth=HttpNtlmAuth(username, password), headers = headers, verify=True, timeout=30)
    
    value = json.loads(r1.text)
    for row in value['d']['results']:
        if(row['Title'] == myvars['Site Name'].strip(' \t\n\r')):
            Id= row['ServerRelativeUrl']
  
    #Add Template and create file simultaneously
    title = myvars['Site Name'].strip(' \t\n\r')  
    post_url = root_url +'GetFolderByServerRelativeUrl(\'/'+Id+'/Pages\')/Files/addtemplatefile(urloffile=\'/'+Id+'/Pages/Home.aspx\',templatefiletype=0)'
    #post_url = root_url +'GetFolderByServerRelativeUrl(\'/'+Id+'/Pages\')/Files/add(url=\'Home.aspx\',overwrite=true)'
    time.sleep(2)
    r2 = requests.post(post_url, auth=HttpNtlmAuth(username, password), headers = headers, verify=True, timeout=30)
    time.sleep(2)   
    logger.debug("Creation of home page %d", r2.status_code)
    
    #--------------------------------------------------------------------------------------------------------------------------
    #updation of home page 
    post_url = root_url + 'GetFileByServerRelativeUrl(\'/' + Id + '/Pages/Home.aspx\')/ListItemAllFields'
   
    r2 = requests.get(post_url, auth=HttpNtlmAuth(username, password), headers = headers, verify=True, timeout=30)
    
    value = json.loads(r2.text)
    id = value['d']['__metadata']['id'] 
   
    root_url_split = site_url + '/_api/'
    post_url = root_url_split + id
  
    #payload =[{ '__metadata': { 'type': 'SP.Data.PagesItem' }, 'Title': config['Credentials']['Site Name'],'SeoMetaDescription':'Some description ragini to fill'},
                #{'__metadata': {'type' : 'SP.FieldUrlValue'},'Url' : 'https://analytics-dev.asu.edu/_catalogs/masterpage/ASUHomeDefault1.aspx'}]

    
    payload ={ '__metadata': { 'type': 'SP.Data.PagesItem' }, 'Title': myvars['Site Name'].strip(' \t\n\r'),'SeoMetaDescription':'Some description ragini to fill',
               
               #'PublishingPageLayout':{'type' : 'Url','Value': 'https://analytics-dev.asu.edu/'+ site_collection_name + '/_catalogs/masterpage/ASUHomeDefault.aspx'}}
               'PublishingPageLayout':{ '__metadata': {'type' : 'SP.FieldUrlValue'},'Description' : 'ASUHomeDefault', 'Url': 'https://analytics-dev.asu.edu/_catalogs/masterpage/ASUHomeDefault.aspx'}}
    headers_merge = {'X-RequestDigest': token,         
               'Accept': 'application/json; odata=verbose',
               'Content-Type': 'application/json; odata=verbose',
                'IF-MATCH':"*",
                'X-HTTP-Method': 'MERGE'
           }
    time.sleep(2)
    r2 = requests.post(post_url,data=json.dumps(payload), auth=HttpNtlmAuth(username, password), headers = headers_merge, verify=True, timeout=30)
   
    logger.debug("Updating Page Layout to ASUHOMEDefault, Title %d", r2.status_code)
    # Make home page as default page at the root level
    
    post_url = root_url + 'GetFolderByServerRelativeUrl(\'/' + Id + '/Pages\')'

    payload ={ '__metadata': { 'type': 'SP.Folder' }, 'WelcomePage': 'Home.aspx'}
               
    headers_merge = {'X-RequestDigest': token,         
               'Accept': 'application/json; odata=verbose',
               'Content-Type': 'application/json; odata=verbose',
                'IF-MATCH':"*",
                'X-HTTP-Method': 'MERGE'
           }
    time.sleep(2)
    r2 = requests.post(post_url,data=json.dumps(payload), auth=HttpNtlmAuth(username, password), headers = headers_merge, verify=True, timeout=30)
   
    logger.debug("Making Home Page a default page at Root Level %d", r2.status_code)
    # Make home page as default page at Pages Level
    
    post_url = root_url + 'GetFolderByServerRelativeUrl(\'/' + Id + '\')'
   
    payload ={ '__metadata': { 'type': 'SP.Folder' }, 'WelcomePage': 'Pages/Home.aspx'}
               
    headers_merge = {'X-RequestDigest': token,         
               'Accept': 'application/json; odata=verbose',
               'Content-Type': 'application/json; odata=verbose',
                'IF-MATCH':"*",
                'X-HTTP-Method': 'MERGE'
           }
    time.sleep(2)
    r2 = requests.post(post_url,data=json.dumps(payload), auth=HttpNtlmAuth(username, password), headers = headers_merge, verify=True, timeout=30)
   
    logger.debug("Making Home Page default page at Pages Level %d", r2.status_code)

    # Delete default page
    server_relative_url = base_url + '/_api/web/webinfos'
   
    r1 = requests.get(server_relative_url, auth=HttpNtlmAuth(username, password), headers = headers, verify=True, timeout=30)
    value = json.loads(r1.text)
    for row in value['d']['results']:
        if(row['Title'] == myvars['Site Name'].strip(' \t\n\r')):
            Id= row['ServerRelativeUrl']
    
    
    post_url_defaultfile = root_url + 'GetFileByServerRelativeUrl(\'/'+Id+'/Pages/default.aspx\')'
    headers_delete = {'X-RequestDigest': token,         
               'Accept': 'application/json; odata=verbose',
               'Content-Type': 'application/json; odata=verbose',
                'IF-MATCH':"*",
                'X-HTTP-Method': 'DELETE'
           }
    time.sleep(2)
    r2 = requests.post(post_url_defaultfile, auth=HttpNtlmAuth(username, password), headers = headers_delete, verify=True, timeout=30)
    logger.debug("Delete Default Page from Pages %d", r2.status_code)
   
def ChangeTheContentTypeToArticlePage(base_url,root_url):
    server_relative_url = base_url + '/_api/web/webinfos'
   
    r1 = requests.get(server_relative_url, auth=HttpNtlmAuth(username, password), headers = headers, verify=True, timeout = 30)
    value = json.loads(r1.text)
    for row in value['d']['results']:
        if(row['Title'] == myvars['Site Name'].strip(' \t\n\r')):
            serverurl= row['ServerRelativeUrl']
    post_url_id_2 = root_url + "AvailableContentTypes?$select=Name, Id, StringId&$filter=Name eq 'Article Page'"  
    r3 = requests.get(post_url_id_2, auth=HttpNtlmAuth(username, password), headers = headers, verify=True, timeout = 30)
    value = json.loads(r3.text)
    Id = value['d']['results'][0]['StringId']
    post_url = root_url + 'GetFileByServerRelativeUrl(\'/' + serverurl + '/Pages/Home.aspx\')/ListItemAllFields'
    payload ={ '__metadata': { 'type': 'SP.Data.PagesItem' }, 'ContentTypeId' : Id}
               

    headers_merge = {'X-RequestDigest': token,         
               'Accept': 'application/json; odata=verbose',
               'Content-Type': 'application/json; odata=verbose',
                'IF-MATCH':"*",
                'X-HTTP-Method': 'MERGE'
           }
   
    time.sleep(2)
    r = requests.post(post_url, data=json.dumps(payload),
                      auth=HttpNtlmAuth(username,
                      password), headers=headers_merge, verify=False, timeout=30)
   
    logger.debug("Content type of Page to Article page %d", r.status_code)
    post_url = root_url + 'GetFileByServerRelativeUrl(\'/' + serverurl + '/Pages/Home.aspx\')/ListItemAllFields'
    """
    payload ={ '__metadata': { 'type': 'SP.Data.PagesItem' }, 'Title': myvars['Site Name'].strip(' \t\n\r'),'SeoMetaDescription':'Some description ragini to fill',
                'PublishingPageLayout':{ '__metadata': {'type' : 'SP.FieldUrlValue'},'Description' : 'ASUHomeDefault', 'Url': 'https://analytics-dev.asu.edu/_catalogs/masterpage/ASUHomeDefault.aspx'}
               }
               
    headers_merge = {'X-RequestDigest': token,         
               'Accept': 'application/json; odata=verbose',
               'Content-Type': 'application/json; odata=verbose',
                'IF-MATCH':"*",
                'X-HTTP-Method': 'MERGE'
           }
    
    r2 = requests.post(post_url,data=json.dumps(payload), auth=HttpNtlmAuth(username, password), headers = headers_merge, verify=True, timeout =30)
    """
def AllowAccessRequestDisable(root_url):
    post_url = root_url
    payload =  {'__metadata': { 'type': 'SP.Web' },
               'RequestAccessEmail':''
              
                }
    headers_merge = {'X-RequestDigest': token,         
               'Accept': 'application/json; odata=verbose',
               'Content-Type': 'application/json; odata=verbose',
                'IF-MATCH':"*",
                'X-HTTP-Method': 'MERGE'
           }
    time.sleep(2)
    r = requests.post(post_url,data=json.dumps(payload),
                      auth=HttpNtlmAuth(username,
                      password), headers=headers_merge, verify=False)
    logger.debug("Access Requests Disable %s",  str(r.status_code))
   

def StartScript(base_url, root_url):
    
    GetNTLMAuthToken(base_url)
    
    while True:
        return_value = CreateSubSite(base_url)
        if(return_value !=200):
            time.sleep(5)
            continue
        else:
            break
    
    CreateGroup(root_url)
    #GetUsersOfAGroup()
    AssignPermissionsToTheGroup(root_url)    
    #AddUsersToTheGroup()    
    ManageFeatures(root_url)
    try:
        DeleteDashboards(root_url)
    except:
        pass
    try:
        DeleteItemInDocumentsLibrary(root_url)
    except:
        pass    
    ModifyingTheViewOfDataConnection(root_url)    
    ModifyContentTypeOfTheList(root_url)
    updateListVersion(root_url)        
    CreateDashBoardsLibrary(root_url)
    AddNavigationQuickLaunchAttribute(base_url, root_url)
    ModifyDashBoardsLibraryContentType(root_url)
    ModifyDashBoardsLibraryView(root_url)
    DeleteItemsFromPageList(base_url, root_url)    
    ChangeDraftVersionVisibilityOfPages(root_url)
    try:
        CreateHomePage(base_url, root_url)
    except:
        pass
    
    ChangeTheContentTypeToArticlePage(base_url, root_url)   
    AllowAccessRequestDisable(root_url)
    
if __name__ == '__main__':
    import sys
    if(myvars['Site Creation Location'].strip(' \t\n\r')=='both'):
        print("The Site Creation Location is Both---> Creating Site in Prod Now")
        url = "analytics.asu.edu"
       
        base_url = myvars['Base URL'].strip(' \t\n\r')
        base_url = urlparse(base_url)
        base_url = base_url.scheme + "://" + url + base_url.path + '/'
        print(base_url)
        site_collection_name = myvars['Site Collection Name'].strip(' \t\n\r')
        #site_url is the location where site gets to be created.
        site_url = base_url + myvars['Site URL'].strip(' \t\n\r') + '/'
        #root_url is the url of the created site.
        root_url = base_url + myvars['Site URL'].strip(' \t\n\r') + '/_api/web/'
        
        StartScript(base_url, root_url)
        
        print("The Site Creation Location is Both---> Creating Site in Dev Now")
        url = "analytics-dev.asu.edu"
        base_url = myvars['Base URL'].strip(' \t\n\r')
        base_url = urlparse(base_url)
        base_url = base_url.scheme + "://" + url + base_url.path + '/'
        #site_url is the location where site gets to be created.
        site_url = base_url + myvars['Site URL'].strip(' \t\n\r') + '/'
        #root_url is the url of the created site.
        root_url = base_url + myvars['Site URL'].strip(' \t\n\r') + '/_api/web/'
        StartScript(base_url, root_url)
        
    elif (myvars['Site Creation Location'].strip(' \t\n\r')=='dev'):
        base_url = myvars['Base URL'].strip(' \t\n\r')
        base_url = urlparse(base_url)
        url = 'analytics-dev.asu.edu'
        base_url = base_url.scheme + "://" + url + base_url.path + '/'
        #site_url is the location where site gets to be created.
        site_url = base_url + myvars['Site URL'].strip(' \t\n\r') + '/'
        #root_url is the url of the created site.
        root_url = base_url + myvars['Site URL'].strip(' \t\n\r') + '/_api/web/'
        StartScript(base_url, root_url)


    elif (myvars['Site Creation Location'].strip(' \t\n\r')=='prod'):
        base_url = myvars['Base URL'].strip(' \t\n\r')
        base_url = urlparse(base_url)
        url = 'analytics.asu.edu'
        base_url = base_url.scheme + "://" + url + base_url.path + '/'
        #site_url is the location where site gets to be created.
        site_url = base_url + myvars['Site URL'].strip(' \t\n\r') + '/'
        #root_url is the url of the created site.
        root_url = base_url + myvars['Site URL'].strip(' \t\n\r') + '/_api/web/'
        print("The Site Creation Location is Not Both ---> Creating Site in Appropriate Location")
        StartScript(base_url, root_url)
        

			

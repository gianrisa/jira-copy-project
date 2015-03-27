# -*- coding: utf-8 -*-

__author__ = 'risalgia'

import re                                             
import time
import pprint

from jira.client import JIRA
from jira.client import GreenHopper
from optparse import OptionParser
from secret_file import secret_new, secret_old
                                                       
# 88b           d88        db        88888888ba   ad88888ba   
# 888b         d888       d88b       88      "8b d8"     "8b  
# 88`8b       d8'88      d8'`8b      88      ,8P Y8,          
# 88 `8b     d8' 88     d8'  `8b     88aaaaaa8P' `Y8aaaaa,    
# 88  `8b   d8'  88    d8YaaaaY8b    88""""""'     `"""""8b,  
# 88   `8b d8'   88   d8""""""""8b   88                  `8b  
# 88    `888'    88  d8'        `8b  88          Y8a     a8P  
# 88     `8'     88 d8'          `8b 88           "Y88888P"  

issue_status =  { 
                  'closed'            : [4,2],
                  'reopened'          : [4,2,3],
                  'inprogress'        : [4],
                  'resolved'          : [5]
                }

""" Issuelink type available in the new jira
    JIRA IssueLinkType: name=u'Blocks', id=u'10000'>,
    JIRA IssueLinkType: name=u'Cloners', id=u'10001'>,
    JIRA IssueLinkType: name=u'Duplicate', id=u'10002'>,
    JIRA IssueLinkType: name=u'Relates', id=u'10003'>
"""
linktype_map =  { 
                  'Dependency'        : 'Relates',
                  'Duplicate'         : 'Duplicate',
                  'Fixes'             : 'Relates', 
                  'implements'        : 'Relates',
                  'Interdependent'    : 'Relates',
                  'More Detail'       : 'Relates',
                  'Related'           : 'Relates',
                  'Reopened'          : 'Relates' 
                }               

issuetype_map = {
                  'Data Quality'      : 'Defect',
                  'Performance'       : 'Defect',
                  'Change Request'    : 'Improvement',
                  'Functional defect' : 'Defect',
                  'UI'                : 'Defect',
                  'Requirement'       : 'User Story',
                  'Sub-task'          : 'Sub-task',
                  'Bug'               : 'Defect',
                  'Technical Story'   : 'User Story',
                  'Technical task'    : 'Sub-task',
                  'Story'             : 'User Story',
                  'Epic'              : 'EPIC',
                  'Improvement'       : 'Improvement',
                  'Change Request'    : 'Improvement',
                  'Task'              : 'Task'
                }

priority_map =  {
                  'Critical/Blocker'  : 'High',
                  'High'              : 'High',
                  'Medium'            : 'Medium',
                  'Low'               : 'Low',
                  'None'              : 'Low'
                }

def jissue_field_prepare_dummy_s(project):
    """ This method returns a dummy string, it is a reference to understand how the issues
        are created and are working in jira, each field has specific attributes, depending
        on the field type. To get the attributes one easy whay is to check an issue directly
        in the browser and observer which fields have attribute : value or name. 
    """
    fields = """{ 'assignee'         : {'name':'risalgia'},
                  'description'      : 'DUMMY_REMOVE_ME',
                  'environment'      : 'DUMMY_REMOVE_ME',
                  'issuetype'        : {'name': 'Defect'},
                  'priority'         : {'name': 'High'},
                  'project'          : {'key':'%(project)s'},
                  'reporter'         : {'name':'risalgia'},
                  'summary'          : 'DUMMY_REMOVE_ME',
                  'customfield_10200': {'value' : 'System Integration Test'},
                  'customfield_10303': {'value' : 'Major'}}""" % {'project':project}
    return fields

def jissue_field_prepare_dummy_f(project):
    """ This method returns a dummy string, it is a reference to understand how the issues
        are created and are working in jira, each field has specific attributes, depending
        on the field type. To get the attributes one easy whay is to check an issue directly
        in the browser and observer which fields have attribute : value or name. 
    """
    fields = """{ 'assignee'         : {'name':'risalgia'},
                  'description'      : 'DUMMY_REMOVE_ME',
                  'environment'      : 'DUMMY_REMOVE_ME',
                  'issuetype'        : {'name': 'Defect'},
                  'versions'         : [{'name':'GNSE_TEST_v1.0'},{'name':'GNSE_TEST_v1.2'}],
                  'fixVersions'      : [{'name':'GNSE_TEST_v1.0'},{'name':'GNSE_TEST_v1.2'}],
                  'components'       : [{'name':'GNSE_TEST_C1'},{'name':'GNSE_TEST_C2'}],
                  'priority'         : {'name': 'High'},
                  'duedate'          : '2015-03-22',
                  'labels'           : ['GNSE_TEST_LL1','GNSE_TEST_LL2'],
                  'project'          : {'key':'%(project)s'},
                  'reporter'         : {'name':'risalgia'},
                  'summary'          : 'DUMMY_REMOVE_ME',
                  'customfield_10200': {'value' : 'System Integration Test'},
                  'customfield_10303': {'value' : 'Major'}}""" % {'project':project}
    return fields

def jissue_field_prepare_mapped(issue, jira, proj):
    """ This method returns a dictionary with the value mapped from the property
        in the dictionary.
    """
    fields_tmp ={ 'assignee'         : assignee(issue, jira, proj),
                  'description'      : description(issue),
                  'environment'      : environment(issue),
                  'issuetype'        : issuetype(issue),
                  'versions'         : versions(issue),
                  'fixVersions'      : fixVersions(issue),
                  'components'       : components(issue),      
                  'priority'         : priority(issue),
                  'duedate'          : duedate(issue),
                  'labels'           : labels(issue),
                  'parent'           : parent(issue),
                  'project'          : project(issue),
                  'reporter'         : reporter(issue, jira, proj),
                  'summary'          : summary(issue),
                  'customfield_10004': epic(issue),
                  'customfield_10200': phase(issue),
                  'customfield_10303': severity(issue),
                  'customfield_10203': rfctcnu(issue)  }
    # in case the fields are empty clean it up 
    tmp = {k:v for k,v in fields_tmp.items() if v}     
    ## pprint.pprint(tmp, indent=3)
    return tmp


                                                                                                  
# 88b           d88 88888888888 888888888888 88        88   ,ad8888ba,   88888888ba,    ad88888ba   
# 888b         d888 88               88      88        88  d8"'    `"8b  88      `"8b  d8"     "8b  
# 88`8b       d8'88 88               88      88        88 d8'        `8b 88        `8b Y8,          
# 88 `8b     d8' 88 88aaaaa          88      88aaaaaaaa88 88          88 88         88 `Y8aaaaa,    
# 88  `8b   d8'  88 88"""""          88      88""""""""88 88          88 88         88   `"""""8b,  
# 88   `8b d8'   88 88               88      88        88 Y8,        ,8P 88         8P         `8b  
# 88    `888'    88 88               88      88        88  Y8a.    .a8P  88      .a8P  Y8a     a8P  
# 88     `8'     88 88888888888      88      88        88   `"Y8888Y"'   88888888Y"'    "Y88888P"   
                                                                                                                                                                                              

# this are the helper methods to move/map remap the data 
def seekuser(issue, jira, project):
    try:
        users = jira.search_assignable_users_for_issues(issue.fields.assignee.name, project)
        return users
    except:
        return []

def assignee(issue, jira_out, project):
    if seekuser(issue, jira_out, project):
        username = seekuser(issue, jira_out, project)[0].key 
    else: 
        username = jira_out.project(project).lead.key
    return {'name':str(username)}
                  
def description(issue):
    if issue.fields.description:          
        description = issue.fields.description
        return str(clean(description))
    else:
        return "Empty description"

def epic(issue):
    if hasattr(issue.fields, 'customfield_10814'):
        return str(clean(issue.fields.customfield_10814))
    else:
        return []
   
def environment(issue):
    if issuetype_map[issue.fields.issuetype.name] == 'Defect':  
        return str(issue.fields.environment)
    else:
        return []

def issuetype(issue):
    if issuetype_map[issue.fields.issuetype.name]:
        issuetype = issuetype_map[issue.fields.issuetype.name]          
        return {'name': str(issuetype)}
    else:
        return {'name': 'Defect'}
   
def versions(issue):
    versions = issue.fields.versions
    return [ {'name':str(v)} for v in versions ]               
       
def fixVersions(issue): 
    fixVersions = issue.fields.fixVersions        
    return [ {'name':str(v)} for v in fixVersions ]        
   
def components(issue):               
    components = issue.fields.components
    return [ {'name':str(v)} for v in components ]  
   
def priority(issue):
    if hasattr(issue.fields, 'customfield_10627') and issue.fields.customfield_10627:
        priority = priority_map[issue.fields.customfield_10627.value]            
        return {'name': str(priority)}
    else:
        return []
      
def duedate(issue):
    if issue.fields.duedate:              
        str(issue.fields.duedate)
    else:          
        return []
   
def labels(issue):              
    labels = issue.fields.labels
    return [ str(clean(v)) for v in labels ]  
   
def project(issue):
    project = issue.fields.project.key
    return {'key' : str(project)}
   
def reporter(issue, jira_out, project):
    if seekuser(issue, jira_out, project):
        reporter = seekuser(issue, jira_out, project)[0].key 
    else: 
        reporter = jira_out.project(project).lead.key   
    return {'name':str(reporter)}
   
def summary(issue):
    summary = issue.fields.summary
    return str(clean(summary.replace('\n', '')))

def parent(issue):
    if issuetype_map[issue.fields.issuetype.name] == 'Sub-task':
        return {'key': str(issue.fields.parent.key)}
    else:
        return []

def phase(issue):
    if issuetype_map[issue.fields.issuetype.name] == 'Defect':
        try:
            customfield_10200 = issue.fields.customfield_10200.value
        except:
            customfield_10200 = 'System Integration Test'          
        return {'value' : str(customfield_10200)}
    else:
        return []

def severity(issue):
    if issuetype_map[issue.fields.issuetype.name] == 'Defect':
        try:      
            customfield_10303 = issue.fields.customfield_10303.value
        except:
            customfield_10303 = 'Major'  
        return {'value' : str(customfield_10303)}
    else:
        return []

def rfctcnu(issue):
    if hasattr(issue.fields, 'customfield_12016') and issue.fields.customfield_12016:
        return str(clean(issue.fields.customfield_12016))
    else:
        return []

                                                     
# 88        88 888888888888 88 88          ad88888ba   
# 88        88      88      88 88         d8"     "8b  
# 88        88      88      88 88         Y8,          
# 88        88      88      88 88         `Y8aaaaa,    
# 88        88      88      88 88           `"""""8b,  
# 88        88      88      88 88                 `8b  
# Y8a.    .a8P      88      88 88         Y8a     a8P  
#  `"Y8888Y"'       88      88 88888888888 "Y88888P"   

def timeit(method):
    """ This method is the time decorator """ 
    def timed(*args, **kw):
        print "Start of: ", method.__name__
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()
        print "End   of: ", method.__name__, "in: %2.2f sec" % (te-ts)
        return result
    return timed

iso885915_utf_map = { u"\u2019":  u"'", 
                      u"\u2018":  u"'",
                      u"\u201c":  u'"',
                      u"\u201d":  u'"'}

def clean(text):
    """ This method is the non utf cleaner """
    return re.sub(r'[^\x00-\x7F]+','_', text)
# remove the ugly stuff
utf_map = dict([(ord(k), ord(v)) for k,v in iso885915_utf_map.items()])


def banner(text, ch='=', length=78):
    spaced_text = ' %s ' % text
    banner = spaced_text.center(length, ch)
    return banner

#   ,ad8888ba,   ,ad8888ba,   88888888ba 8b        d8    88b           d88 88888888888 888888888888 88        88   ,ad8888ba,   88888888ba,    ad88888ba   
#  d8"'    `"8b d8"'    `"8b  88      "8b Y8,    ,8P     888b         d888 88               88      88        88  d8"'    `"8b  88      `"8b  d8"     "8b  
# d8'          d8'        `8b 88      ,8P  Y8,  ,8P      88`8b       d8'88 88               88      88        88 d8'        `8b 88        `8b Y8,          
# 88           88          88 88aaaaaa8P'   "8aa8"       88 `8b     d8' 88 88aaaaa          88      88aaaaaaaa88 88          88 88         88 `Y8aaaaa,    
# 88           88          88 88""""""'      `88'        88  `8b   d8'  88 88"""""          88      88""""""""88 88          88 88         88   `"""""8b,  
# Y8,          Y8,        ,8P 88              88         88   `8b d8'   88 88               88      88        88 Y8,        ,8P 88         8P         `8b  
#  Y8a.    .a8P Y8a.    .a8P  88              88         88    `888'    88 88               88      88        88  Y8a.    .a8P  88      .a8P  Y8a     a8P  
#   `"Y8888Y"'   `"Y8888Y"'   88              88         88     `8'     88 88888888888      88      88        88   `"Y8888Y"'   88888888Y"'    "Y88888P"   
                                                                                                                                                                                                                                                                                         

@timeit
def copy_components(jira_in, jira_out, project):
    """ This is the helper method to copy the components from jira_in to
        jira_out, related to the project, copy components inclue only the
        component name 
    """
    comps_c = []
    jira_proj  = jira_in.project(project)
    comps = jira_in.project_components(jira_proj)
    for c in comps:
        try:
            comps_c.append(jira_out.create_component(str(c), project))
        except Exception as e:
            print "Could not copy components :", e
    return comps_c

@timeit
def copy_versions(jira_in, jira_out, project):
    vers_c = []
    jira_proj  = jira_in.project(project)
    vers = jira_in.project_versions(jira_proj)
    for v in vers:
        try:
            vers_c.append(jira_out.create_version(str(v.name), project))
        except Exception as e:
            print "Could not copy version :", e
    return vers_c

@timeit
def copy_issues(jira_in, jira_out, project, issue_max_key, issues_old, start=0):
    """ This method get the max issues and the issue list - issue contains the issue 
        pointer to the old jira to be migrated like .. links .. attachment ..
        status.. this is pretty big anyway 
    """

    # list holder for the issues that need to be created in jira_new empty vector
    issues_list = ['']*(issue_max_key)
    
    for issue in issues_old:
        issues_list[int(issue.key.split("-")[1])-1]=issue

    # check and create the list of issue that need to be copying 
    for i, issue in enumerate(issues_list):
        # skip to the starting point 
        if i >= start:
            # create the issues in jira with reference list
            issue_dict = {}
            if issue:
                # good issue copy it
                try:
                    print "Copied from jira old    :", issue
                    issue_dict = jissue_field_prepare_mapped(issue, jira_out, project)

                except Exception as e:
                    print "Emergency issue created : %s-%s"%(project,i+1), e
                    issues_list_r.append(issue)
                    issue_dict = eval(jissue_field_prepare_dummy_s(project))
            else:
                # someone deleted that issue we need to create one empty minimum required
                # let's create a virtual issue key will be stored in a list and later on
                # will be used to delete all the dummy unused issues
                print "Created dummy issue     : %s-%s"%(project,i+1)
                issue_dict = eval(jissue_field_prepare_dummy_s(project))
            # here finally we create the issue and we place it in a list
            issue_created = jira_out.create_issue(fields=issue_dict, prefetch=True)
        else:
            print "Skiping issue      : %s-%s"%(project,i)

@timeit
def custom_isseue_comments(issue_in):
    """ This method can be extended from the end user in order to include in the issue comment
        the old issue unmapped fields
    """
    comment = """
            original field : assignee       :  %(assignee)s      
            original field : created        :  %(created)s       
            original field : creator        :  %(creator)s       
            original field : duedate        :  %(duedate)s       
            original field : reporter       :  %(reporter)s      
            original field : resolution     :  %(resolution)s    
            original field : resolutiondate :  %(resolutiondate)s
            original field : status         :  %(status)s        
            original field : updated        :  %(updated)s       
              """% {'assignee' : issue_in.fields.assignee.name,  'created'  :issue_in.fields.created, 
                    'creator'  : issue_in.fields.creator.name,  'duedate'   :issue_in.fields.duedate,
                    'reporter' : issue_in.fields.reporter.name, 'resolution':issue_in.fields.resolution, 
                    'resolutiondate' : issue_in.fields.resolutiondate, 'status': issue_in.fields.status.name,
                    'updated'  : issue_in.fields.updated}
    return str(comment)


@timeit
def copy_comments(jira_out, issue_in, issue_out):
    """ This is the helper method to copy the comments from jira_out to
        jira_out, related to the project, copy comments inclue only the
        commments body and inclue in the email of the writer
    """
    comments = []
    # need to bear in mind that issues need to be update before touched !!!
    # issue_in.update()
    try:
        issue_out.update()
        comments = [custom_isseue_comments(issue_in)]
        # get the comments from the in issue then copies them to the other issue in the other jira instance
        issue_comments = ["%s added by %s"%(comment.body, comment.author.emailAddress) for comment in issue_in.fields.comment.comments]
        # Add a comment to the issue.
        commnets.extned(issue_comments)

    except Exception as e:
        # no comment
        print "Could not get comments :", issue_in.key, e
        comments = []
    for c in comments:
        jira_out.add_comment(issue_out, str(clean(c)))

@timeit
def get_attachments(jira_in, issue_in):
    """ This method is the helper to get the attachments store them
        in temp directory and returns a list of filename to be uploaded 
    """ 
    path = r"C:\TEMP\%s"
    # remember to update the issue before touch it !!!
    # issue_in.update()
    filelist = []
    try:
        attachments = issue_in.fields.attachment
        for i in attachments:
            r = jira_in._session.get(i.content)
            if r.status_code == 200:
                with open(path%i.filename, 'wb') as f:
                    for chunk in r.iter_content():
                        f.write(chunk)
                    filelist.append(path%i.filename)
        return filelist
    except Exception as e:
        print "Could not get attachments :", issue_in.key, e
        return []

@timeit
def copy_attachment(jira_in, jira_out, issue_in):
    """ This is the method used to copy issues attachments form old to new
        get the old issue as input and copy the attachemnts from the location
        where were saved
    """
    filelist = get_attachments(jira_in, issue_in)
    try:
        for filename in filelist:
            with open(filename, 'rb') as f:
                issue_out = issue_in.key
                jira_out.add_attachment(issue_out, f)
    except Exception as e:
        print "Attachment not copyied :", issue_in.key, e

@timeit
def copy_issuelinks(jira_in, jira_out, issue_in):
    """ This is the method used to copy issues links from old to new, get the old
        issue links and iterate along the inwardIssuelink and outwardIssueLink, if 
        in or out refers to the issus itself then will be skip.
        This must be done only after the issued are created links can be create only
        if the outwardIssue is present.
    """
    for i in issue_in.fields.issuelinks:
        try:
            jira_out.create_issue_link(linktype_map[i.type.name], jira_in.issue_link(i.id).inwardIssue.key, 
                                                    jira_in.issue_link(i.id).outwardIssue.key)
        except Exception as e:
            print "Link issue not copyied :", jira_in.issue_link(i.id).inwardIssue.key, \
                                              jira_in.issue_link(i.id).outwardIssue.key, e
@timeit
def copy_epiclink(green_in, green_out, issue_in):
    try:
        if hasattr(issue_in.fields, 'customfield_10811') and issue_in.fields.customfield_10811:
            epicLink = str(issue_in.fields.customfield_10811)
            issuesToAdd = [str(issue_in.fields.key)]
            jira_out.add_issues_to_epic(epicLink, issuesToAdd)          
    except:
        print "Epic Link issue not copyied :", issue_in.key


@timeit                                              
def copy_issuestatus(jira_in, jira_out, issue_in):
    """ This is the method used to copy issues status from old to new, get the old
        issue links and iterate along the transition in order to reach the final status, 
        the copy status will refer to the jira_out status and will be mapped only open closed.
        This can be iterated per each issue
    """
    try:
        if issue_in.fields.status.name.lower() in issue_status:
            for t in issue_status[issue_in.fields.status.name.lower()]:
                issue_out = jira_out.issue(issue_in.key)
                jira_out.transition_issue(issue_out,t)
        else:
            print "Status not in map       :", issue_in.fields.status.name
    except Exception as e:
        print "Cannot change issue status :", e

@timeit
def copy_issueattribs(jira_in, jira_out, green_out, issues_in, options):
    """ This method is used to copy issue attributes, comments, attachments
        issuestatus and issuelinks.
    """
    for i in issues_in:
        # [] 
        i_old = jira_in.issue(i.key)
        i_new = jira_out.issue(i_old.key)  
        print "Copy issue attributes:", i_old.key

        if options.issuecomm:   copy_comments(jira_out, i_old, i_new)
        if options.issueattach: copy_attachment(jira_in, jira_out, i_old)
        if options.issuelinks:  copy_issuelinks(jira_in, jira_out, i_old)
        if options.issuelinks:  copy_epiclink(jira_in, green_out, i_old)
        if options.issuestatus: copy_issuestatus(jira_in, jira_out, i_old)


# 88        88 88888888888 88          88888888ba  88888888888 88888888ba   ad88888ba   
# 88        88 88          88          88      "8b 88          88      "8b d8"     "8b  
# 88        88 88          88          88      ,8P 88          88      ,8P Y8,          
# 88aaaaaaaa88 88aaaaa     88          88aaaaaa8P' 88aaaaa     88aaaaaa8P' `Y8aaaaa,    
# 88""""""""88 88"""""     88          88""""""'   88"""""     88""""88'     `"""""8b,  
# 88        88 88          88          88          88          88    `8b           `8b  
# 88        88 88          88          88          88          88     `8b  Y8a     a8P  
# 88        88 88888888888 88888888888 88          88888888888 88      `8b  "Y88888P"    

def jconnect(jira_param):
    """ This is the methos used as jira connector """
    jcon = JIRA(options={'server': jira_param[0]},basic_auth=(jira_param[1], jira_param[2]))
    return jcon

def jgreencon(jira_param):
    """ This is the methos used as jira connector """
    jcon = GreenHopper(options={'server': jira_param[0]},basic_auth=(jira_param[1], jira_param[2]))
    return jcon

def jissue_query(jinstance, jproj, startAt=0, maxResults=10):
    """ This method is the issues selector """
    jquery = '''project=%s'''%(jproj)
    issues = jinstance.search_issues('''project=%s'''%(jproj), startAt=startAt, maxResults=maxResults)
    return issues

def jissue_get_last(j_old, project_old):
    """ This method return the total issue count in project A - Max Key """
    j_issues_old_count = jissue_query(j_old, project_old)
    j_issue_max_key = int(j_issues_old_count[0].key.split("-")[1])
    return j_issue_max_key

@timeit
def jissue_get_chunked(jira_in, project, issue_max_count, chunks=100):
    """ This method is used to get the issue list with references, 
        in case the number of issues is more than 1000 
    """
    result = []
    # step and rest simple calc
    step = issue_max_count / chunks
    rest = issue_max_count % chunks
    # iterate the issue gathering
    for i in range(step):
        result.extend(jissue_query(jira_in, project, chunks*i, chunks))
    result.extend(jissue_query(jira_in, project, issue_max_count-rest, rest))
    return result

@timeit
def jissue_prepare(jira_in, project):
    """ This method gets the total number of issues and the relative list
        it returns two parameters first issue list second max count
    """
    # get the max issue number max key
    issue_max_key =  jissue_get_last(jira_in, project)    
    # get all the issues in the project pretty expensive operation, this will take a while
    issues_old = jissue_get_chunked(jira_in, project, issue_max_key)
    # return the issues list 
    return issues_old, issue_max_key

def jissue_field_parser(jira_in, issue_in):
    parsed_custom = []
    parsed_system = []
    try:
        issue = jira_in.issue(issue_in)
        for f in dir(issue.fields):
            if not f.startswith('__'):
                if f.startswith('customfield'):
                    parsed_custom.append( ('issue.fields.%s'%str(f),eval('issue.fields.%s'%str(f))) ) 
                else:
                    parsed_system.append( ('issue.fields.%s'%str(f),eval('issue.fields.%s'%str(f))) )
        return parsed_system, parsed_custom
    except Exception as e:
        print "Exception occurred :", e
        return 0, 0


# 88b           d88        db        88 888b      88  
# 888b         d888       d88b       88 8888b     88  
# 88`8b       d8'88      d8'`8b      88 88 `8b    88  
# 88 `8b     d8' 88     d8'  `8b     88 88  `8b   88  
# 88  `8b   d8'  88    d8YaaaaY8b    88 88   `8b  88  
# 88   `8b d8'   88   d8""""""""8b   88 88    `8b 88  
# 88    `888'    88  d8'        `8b  88 88     `8888  
# 88     `8'     88 d8'          `8b 88 88      `888  

# the main, combine all together, and get the needed parameters
# from option parser
def main():
    usage = "usage: %prog [options] arg"
    parser = OptionParser(usage)
    parser.add_option("-f", "--full", dest="full",
                      action="store_true", help="all options enabled", default=False)

    parser.add_option("--pc", "--components", help="copy project components",
                      action="store_true", dest="components", default=False)

    parser.add_option("--pv", "--versions", help="copy project versions",
                      action="store_true", dest="versions", default=False)   

    parser.add_option("--il", "--issue-link", help="copy issues links",
                      action="store_true", dest="issuelinks", default=False)

    parser.add_option("--ic", "--issue-comm", help="copy issues comments",
                      action="store_true", dest="issuecomm", default=False)

    parser.add_option("--ia", "--issue-attach", help="copy issues attachments",
                      action="store_true", dest="issueattach", default=False)

    parser.add_option("--is", "--issue-satus", help="copy issues status",
                      action="store_true", dest="issuestatus", default=False) 

    parser.add_option("--i", "--issues", help="copy issues",
                      action="store_true", dest="issues", default=False)

    parser.add_option("-b", "--begin", dest="start", default=0, type="int", 
                      help="issue to begin copy from")

    parser.add_option("-z", "--analyze",  dest="analyze", type="string",
                      help="issue customfield analyze")

    (options, args) = parser.parse_args()
    # check if the correct number of argument has been given to the
    # commandline

    if len(args) != 1:
        parser.error("incorrect number of arguments")

    # first stage issue creation in project from project reference.
    # connect to the old jira server parameters
    j_old_param = (secret_old['server'], secret_old['user'], secret_old['pass'])
    # connect to the new jira and create the issues with empty dummy values
    j_new_param = (secret_new['server'], secret_new['user'], secret_new['pass'])

    # the project name shall be given as external parameter
    j_project = args[0]
    # perform jira connection
    j_old = jconnect(j_old_param)
    # perform jira connection
    j_new = jconnect(j_new_param)
    # perform jira green hopper connection 
    j_green = jgreencon(j_new_param)
    # fetch the data this operation needs to be done before to start any kind of copy
    issue_old, issue_max_key = jissue_prepare(j_old, j_project)

    print banner("JIRA IN SERVER CONNECTED")
    pprint.pprint(j_old.server_info(), indent=3)

    print banner("JIRA OUT SERVER CONNECTED")
    pprint.pprint(j_new.server_info(), indent=3)

    print banner("COPY COMPONENTS")
    if options.components:
        # precondition prepare the components if any copy from old to new
        proj_componente = copy_components(j_old, j_new, j_project)

    print banner("COPY VERSIONS")
        # precondition prepare the versions if any copy from old to new
    if options.versions:
        proj_versions   = copy_versions(j_old, j_new, j_project)

    print banner("COPY ISSUES")
    if options.issues:
        # iterate along the issues and copy the issues to the new jira
        copy_issues(j_old, j_new, j_project, issue_max_key, issues_old, options.start)
    
    print banner("COPY ATTRIBUTES")
    if options.issuestatus or options.issuelinks or options.issuecomm or options.issueattach:
        # iterate along the issues in the old project and copy comments attachment links and change 
        # the issues status in the new jira
        copy_issueattribs(j_old, j_new, j_green, issues_old, options)

    print banner("ISSUE ANALYZER")
    if options.analyze:
        # this helps the user to understand which fields are availables in the wished issue.
        result = jissue_field_parser(j_old, options.analyze)
        # print the SYSTEM FIELDS
        print banner("SYSTEM FIELDS")
        pprint.pprint(result[0], indent=3)
        # print the CUSTOM FIELDS
        print banner("CUSTOM FIELDS")
        pprint.pprint(result[1], indent=3)
        
        print banner("Operation terminated, exit")

if __name__ == "__main__":
    main()
# -*- coding: utf-8 -*-

__author__ = 'risalgia'

from jira.client import JIRA
import pprint
from secret_file import secret_new, secret_old
import time
import re                                             

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
def copy_issues(jira_in, jira_out, project, start=0):
    """ This method get the max issues and the issue list - issue contains the issue 
        pointer to the old jira to be migrated like .. links .. attachment ..
        status.. this is pretty big anyway 
    """
    issue_max_key =  jissue_get_last(jira_in, project)    
    # get all the issues in the project pretty expensive operation, this will take a while
    issues_old = jissue_get_chunked(jira_in, project, issue_max_key)
    # list holder for the issues that need to be created in jira_new empty vector
    issues_list = ['']*(issue_max_key)
    # list holder for the new created issues
    issues_list_c = []
    # list holder for issue to be deleted
    issues_list_r = []
    # place the value in the right position
    
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
                issues_list_r.append(issue)
                issue_dict = eval(jissue_field_prepare_dummy_s(project))
            # here finally we create the issue and we place it in a list
            issues_list_c.append(jira_out.create_issue(fields=issue_dict, prefetch=True))
        else:
            print "Skiping issue      : %s-%s"%(project,i)
    return issues_old, issues_list_c, issues_list_r

@timeit
def copy_comments(jira_out, issue_in, issue_out):
    """ This is the helper method to copy the comments from jira_out to
        jira_out, related to the project, copy comments inclue only the
        commments body and inclue in the email of the writer
    """
    comments = []
    # need to bear in mind that issues need to be update before touched !!!
    issue_in.update()
    issue_out.update()
    try:
        # get the comments from the in issue then copies them to the other issue in the other jira instance
        comments = ["%s added by %s"%(comment.body, comment.author.emailAddress) for comment in issue_in.fields.comment.comments]
        # Add a comment to the issue.
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
    issue_in.update()
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
def copy_issuestatus(jira_in, jira_out, issue_in):
    """ This is the method used to copy issues status from old to new, get the old
        issue links and iterate along the transition in order to reach the final status, 
        the copy status will refer to the jira_out status and will be mapped only open closed.
        This can be iterated per each issue
    """

    if issue_in.fields.status.name.lower() in issue_status:
        for t in issue_status[issue_in.fields.status.name.lower()]:
            issue_out = jira_out.issue(issue_in.key)
            jira_out.transition_issue(issue_out,t)
    else:
        print "Status not in map       :", issue_in.fields.status.name


@timeit
def copy_issueattribs(jira_in, jira_out, issues_in):
    """ This method is used to copy issue attributes, comments, attachments
        issuestatus and issuelinks.
    """

    for i_old in issues_in:
        print "Copy issue attributes:", i_old.key
        i_new = j_new.issue(i_old.key)  

        copy_comments(jira_out, jira_in, i_new)
        copy_attachment(jira_in, jira_out, i_old)
        copy_issuestatus(jira_in, jira_out, i_old)
        copy_issuelinks(jira_in, jira_out, i_old)


def jconnect(jira_param):
    """ This is the methos used as jira connector """
    jcon = JIRA(options={'server': jira_param[0]},basic_auth=(jira_param[1], jira_param[2]))
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
def jissue_get_chunked(jira, project, issue_max_count, chunks=100):
    """ This method is used to get the issue list with references, 
        in case the number of issues is more than 1000 
    """
    result = []
    # step and rest simple calc
    step = issue_max_count / chunks
    rest = issue_max_count % chunks
    # iterate the issue gathering
    for i in range(step):
        result.extend(jissue_query(jira, project, chunks*i, chunks))
    result.extend(jissue_query(jira, project, issue_max_count-rest, rest))
    return result

def jissue_field_parser(issue):
    parsed_custom = []
    parsed_system = []
    for f in dir(issue.fields):
        if not f.startswith('__'):
            if f.startswith('customfield'):
                parsed_custom.append( ('issue.fields.%s'%str(f),eval('issue.fields.%s'%str(f))) ) 
            else:
                parsed_system.append( ('issue.fields.%s'%str(f),eval('issue.fields.%s'%str(f))) )
    return parsed_system, parsed_custom

def seekuser(issue, jira, project):
    try:
        users = jira.search_assignable_users_for_issues(issue.fields.assignee.name, project)
        return users
    except:
        return []

# this are the helper methods to move/map remap the data 
def assignee(issue, jira, project):
    if seekuser(issue, jira, project):
        username = seekuser(issue, jira, project)[0].key 
    else: 
        username = j_new.project(project).lead.key
    return {'name':str(username)}
                  
def description(issue):
    if issue.fields.description:          
        description = issue.fields.description
        return str(clean(description))
    else:
        return "Empty description"
   
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
   
def reporter(issue, jira, project):
    if seekuser(issue, jira, project):
        reporter = seekuser(issue, jira, project)[0].key 
    else: 
        reporter = j_new.project(project).lead.key   
    return {'name':str(reporter)}
   
def summary(issue):
    summary = issue.fields.summary
    return str(clean(summary))

def parent(issue):
    if issuetype_map[issue.fields.issuetype.name] == 'Sub-task':
        return issue.fields.parent.key
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
                  'Sub-task'          : 'Sub-task'
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
                  'customfield_10200': phase(issue),
                  'customfield_10303': severity(issue),
                  'customfield_10203': rfctcnu(issue)  }
    # in case the fields are empty clean it up      
    return {k:v for k,v in fields_tmp.items() if v}

if __name__ == "__main__":

    # first stage issue creation in project from project reference.
    
    # connect to the old jira server parameters
    j_old_param = (secret_old['server'], secret_old['user'], secret_old['pass'])
    # connect to the new jira and create the issues with empty dummy values
    j_new_param = (secret_new['server'], secret_new['user'], secret_new['pass'])

    # the project name shall be given as external parameter
    j_project = "DIT"
    # perform jira connection
    j_old = jconnect(j_old_param)
    # perform jira connection
    j_new = jconnect(j_new_param)

    # precondition prepare the versions and the components if any copy from old to new
    proj_versions   = copy_versions(j_old, j_new, j_project)
    proj_componente = copy_components(j_old, j_new, j_project)
    # iterate along the issues and copy the issues to the new jira
    issues_old, issues_new, not_issues  = copy_issues(j_old, j_new, j_project, start=0)
    # iterate along the issues in the old project and copy comments attachment and change status in the
    # new jira issues
    copy_issueattribs(j_old, j_new, issues_old)
    
    print "Copy operation terminated, exit"

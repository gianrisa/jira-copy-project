# jira-copy-project
This script as been created to cover a basic challenge that every person
that uses jira from long time in the incorect way. The challenge in this
case is how can I copy a project form an old jira instance to a new jira
instance ? And how can I get rid of all  the  junk and clean the project
while copying it to the new instance ?

Moreover here you will be able to implement the mapping, famous word that
hides a lot of moment when you want to give up in changing the old world
and keep the junk.

This script at this point in time is version 1.1 with a lot of  room for 
improvement and to be more user friendly.

To use it you need to modify the methods related to the fields mapping and
to the attributes.

For now I've only implemented these features:
   
   # precondition prepare the versions and the components if any copy from old to new
   copy_versions(j_old, j_new, j_project)
   copy_components(j_old, j_new, j_project)

   # iterate along the issues and copy the issues to the new jira
   copy_issues(j_old, j_new, j_project, start=0)
 
   # iterate along the issues in the old project and copy comments attachment and change status in the
   # new jira issues
   copy_issueattribs(j_old, j_new, issues_old)

The issues attribs are at the moment are :

   copy_comments(jira_out, jira_in, i_new)
   copy_attachment(jira_in, jira_out, i_old)
   copy_issuestatus(jira_in, jira_out, i_old)
   copy_issuelinks(jira_in, jira_out, i_old)

To use it as precondition you need to install the jira-python package:
   
   Download and install using pip install jira or easy_install jira
   You can also try pip install --user --upgrade jira which will install or upgrade jira to your user directory

   1) Then need to change the jira_secret.py file there you have the two jira instances the source is the secret_old
   the destination is the secret_new.
   there you place your credentials and the urls for the both servers.

   2) Create the project in the new jira with the same key, so if your source project is called PRJ the destination
   project needs to have the same key, the project shall be empty.

   3) Now you are ready to run it:
   Start to copy the component --pc and the version --pv in production -P
   
   $>python jira_copy_project.py PRJ -P --pc --pv
   
   Once it is ready then, you start to copy the issues

   $>python jira_copy_project.py PRJ -P --i
   
   Once it is ready then you can copy the issues attributes.
   which are comments, attachments

   $>python jira_copy_project.py PRJ -P --ia --ic 

   If you are linking issues outside the project, then you need to get the other project already copied in the new jira
   instance then you can link the issues, if the issues are only linked locally then you can run it whenever you want.

   $>python jira_copy_project.py PRJ -P --il

   Once the linkage is completed, then you can proceed with the Status. NOTE: the status must be every time the last step because
   if you have closed issues, usually you cannot update those anymore. There is here a workaround, that is to change the permission 
   scheme then you can also change the status whenever you want.

   $>python jira_copy_project.py PRJ -P --is

   There is a special customization that you need to do and are dependent on the jira configuration, at this point in time the custom
   fields need to be changed manually directly in the code. This is a future improvement that need to be done. Next version.

   If you need the help here the command to get a small remind about the available combinations:

   $> python jira_copy_project.py -h
   Usage: jira_copy_project.py <project_key> [options]

   Options:
     -h, --help            show this help message and exit
     --pc, --components    copy project components
     --pv, --versions      copy project versions
     --il, --issue-link    copy issues links
     --ic, --issue-comm    copy issues comments
     --ie, --issue-estim   copy issues estimation
     --ia, --issue-attach  copy issues attachments
     --is, --issue-satus   copy issues status
     --i, --issues         copy issues
     -b START, --begin=START
                        issue to begin copy from
     -z ANALYZE, --analyze=ANALYZE
                        issue customfield analyze
     -P, --production      copy to production

_______________________________________________________________________________________________________________

Author  - Gianfranco Risaliti
Date    - 29-Sept-2015
Version - 1.1






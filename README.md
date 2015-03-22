# jira-copy-project
This script as been created to cover a basic challenge that every person
that uses jira from long time in the incorect way. The challenge in this
case is how can I copy a project form an old jira instance to a new jira
instance ? And how can I get rid of all  the  junk and clean the project
while copying it to the new instance ?

Moreover here you will be able to implement the mapping, famous word that
hides a lot of moment when you want to give up in changing the old world
and keep the junk.

This script at this point in time ( 22-March-2015 ) is version 1.0 with a
lot of room to improve and to be more user friendly.

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

To configure it you need to:
   
   modify the project variable and select the project name you want to copy

    # the project name shall be given as external parameter
      j_project = "DIT"
    # perform jira connection
      j_old = jconnect(j_old_param)
   
   then you need to modify the server and credential present on the jira_secret.py
   
Then python jira_copy_project.py
_______________________________________________________________________________________________________________

Author  - Gianfranco Risaliti
Date    - 22-March-2015
Version - 1.0






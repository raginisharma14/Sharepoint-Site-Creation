Python Version -3.4

Packages to be installed - requests_ntlm, lxml and urllib.parse

Instructions: Place the site_config.txt file in the same folder as that of the script. Run the command "python sp_site_creation.py"

Script promts for the password, Enter the password to run the script for creation of Sharepoint Site. 

Reasons for not Automating above steps:
Navigation attributes are part of rest API AllProperties and AllProperties API does not support modify or merge patch yet. Hence could not modify navigation attributes through the Script.
There is no rest API for Add WebPart yet. Hence could not Add web part content repository through Script.  
PowerUsers and Report viewers login names are formatted in a form where SID is appended to it. This can be automated if we can access the active directory and search for the SID of the group.(Can be Automated)
Python Version:3.4.2
Instructions: To run the script, the user should input the required fields inside a file named InputInformation.txt.
InputInformation.txt and the python script must reside in the same folder. Sample InputInformation.txt file and the script file are attached below
Command To Run The Script: python formatdemo.py
Issues: If the script fails for some reason, rerun the script. 
	

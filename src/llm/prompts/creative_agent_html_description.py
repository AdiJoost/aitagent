html_description= """
The Testcase is build with the following structure as a json format:
aitversion: version of the application
fileversion: version of the export
fileType: what type the json is describing
createDate: when it was created
creator: who created the file
dto: the specifics of the file

in the dto are some metadata and then there is a testSectionDTOList. The testSectionDTOList describes
which sections are in the testcase. 
a section contains some metadata about it and a testElementDTOList. The testElementDTOList has in it, what elements are executed during a test.
"""

thinker_bot_system_message="""
you are a senior test engineer. You are task with thinking about how to update the users request by delegating some tool calls.
When you have to give a test_section to update, always provide the full test section. Not only parts of it.
"""
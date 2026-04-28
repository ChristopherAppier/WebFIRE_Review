WebFIRE Deviation Scanner Workflow

Main Workflow
Document Retrieval and Routing (Python)
* Automated timer triggers the script to run
* Check last run timestamp
* Create Pull request for all reports since last timestamp
* Download all reports returned
* Extract documents from zip/database structure
* OCR all PDFs (if needed)
* Split route based on PDF vs spreadsheet

Spreadsheet Review (Python) - Loop
* Scan for deviation / excess emission flags
* Output all compliance info to JSON
* Output all scan stats to JSON

PDF Review (AI + Python) - Loop
* PDF chunking (python)
* PDF chunk review and summary output as JSON (AI)
* Save X% of reviews marked as in compliance to audit folder
* Send all reviews marked as out of compliance to Live Auditor workflow
* Output all compliance info to JSON
* Output all scan stats to JSON

Summary Reporting (Python)
* Compiles all JSONs into human readable spreadsheets
* Packages the Further Review Spreadsheet into an email summary with the spreadsheet linked
* Includes links to further information for QA reviews (auditor information, etc.)

Accuracy Oversight Workflows
Live AI Auditor (Non-compliance Flag Audit)
* When compliance issue is flagged by the standard AI workflow, an auditor AI agent is passed the information that was used to create the flag and the output JSON. The auditor scrutinizes the review to ensure that it is correct
* Increases confidence in reports flagged for further review by humans (save time)
* This live auditor is used to review all non-compliance flags
* The results of the live auditor’s review will be presented alongside the compliance summary spreadsheet in the emails to staff

Random AI Auditor (Compliance Flag Audit)
* X% of the compliance determinations made (only in compliance determinations) by the AI in the standard workflows will save their information reviewed and output JSON to a random auditor folder that will run after the main workflow. 
* The random auditor agent will scrutinize the work of the main workflow AI agents and create a report on their accuracy
* This random auditor is used to review X% of all compliance flags
* The results of the random auditor’s review will be presented to workflow manager (human) when the audit is ran and will include stats.

Random Python Auditor
* X% of the spreadsheets that were reviewed via python scripts will be set aside for random AI auditor agent review
* Ensures that the python script isn’t creating unexpected errors due to its hard coded logic
* Report results to workflow manager

Poor Accuracy Handling
* If the live or random audits fall below a certain percentage (decided later), then the entire process will be reviewed and overhauled to maintain accurate checks
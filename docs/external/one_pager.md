R7 AI Document Review Pipeline Pilot
Problem
R7 ECAD receives a large number of compliance reports to review. Reviewing these reports consumes constrained agency resources. Currently available AI systems at EPA (chat bots) are not ideal for reviewing reports en masse due to number and length of the reports.
Proposed Solution
Using computer coding (python) and AI, an automated document review pipeline is being created, tested, and refined. This pilot project will download Clean Air Act compliance reports and review them using a large language model (LLM). Any potential compliance issues will be flagged, summarized, and directed to R7 ECAD staff for further investigation. 
This pipeline will run on an automated schedule and review all reports submitted to EPA’s publicly accessible database, WebFIRE. The LLM will run locally using a free publicly available model.
Value
The AI document review pipeline will be designed to be reusable in other projects, and this pilot will serve as a test bed for its implementation. The true value of this project is not being able to review the documents in WebFIRE, but to create a generalized approach to using AI to review large sets of documents and is intended to save valuable time for staff throughout the agency.
How It Works
1.	All new reports submitted to EPA R7 are downloaded from the WebFIRE database.
2.	Any reports that use EPA’s template spreadsheet (structured) are reviewed using python scripting to check for self-reported compliance issues. Any other reports (unstructured) are sent to the AI review pipeline. 
3.	Any reports that do not have selectable text (e.g. scanned reports) are made selectable using optical character recognition.
4.	Each report is sent to an LLM to determine the type of report (e.g. stack test).
5.	Each report is broken down into chunks to avoid LLM context overload. Each chunk and a prompt, customized for the report type, are sent to an LLM to screen for potential compliance issues.
6.	If a reference to the CFR is needed by the LLM to help make a determination, it can request the relevant text from the eCFR.gov website.
7.	Reports that are flagged for potential compliance issues are sent to an LLM to be audited. The initial review is over-eager to flag potential issues (reduces false negatives), while the auditor is more discerning (reduces false positives).
8.	A summary spreadsheet is then created for enforcement staff that lists all reports flagged for potential compliance issues. ECAD staff will then review the corresponding reports to make their own determination of compliance and the appropriate follow-up action.

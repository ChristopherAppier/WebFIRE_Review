# R7 AI Document Review Pipeline Pilot

## Problem

R7 ECAD receives a significant number of compliance reports from the regulated community. Reviewing every report consumes constrained agency resources. The AI tools currently available to EPA staff (chat-bots) are impractical for reviewing reports en masse due to number and length of the reports.

## Proposed Solution

Using coding and AI, an automated document review pipeline is being developed, tested, and refined. This pilot project downloads Clean Air Act compliance reports and reviews them using large language models (LLM). Any potential compliance issues are flagged, summarized, and directed to R7 ECAD staff for further investigation. 

This pipeline can run on an automated schedule and review all reports submitted to EPA’s publicly accessible database, WebFIRE. It currently uses free and publicly available LLMs running on local hardware.

## Value

The project's code is designed to be easily adaptable to similar projects and this pilot will serve as a test bed for its implementation. The main value of this project is not being able to review the documents in WebFIRE, but to create a generalized approach to using AI to review large sets of documents, saving valuable time for staff throughout the agency.

## How It Works

1.	Electronically submitted reports are downloaded in batches from the WebFIRE database.
2.	Any reports that do not have selectable text (e.g. scanned reports) are made selectable using optical character recognition.
3.	Each report is sent to an LLM to determine the type of report (e.g. emissions test report).
4.	Each report is broken down into chunks to avoid LLM context overload. Each chunk and a prompt, customized for the type of report, are sent to an LLM to screen for potential compliance issues.
5.	Reports that are flagged for potential compliance issues are sent to a larger LLM to be audited. The initial review is over-eager to flag potential issues (reduces false negatives), while the audit is more discerning (reduces false positives).
6.	A summary is provided to enforcement staff containing a list of reports flagged for potential compliance issues. ECAD staff can then review the flagged reports to make their own determination of compliance and the appropriate follow-up action.

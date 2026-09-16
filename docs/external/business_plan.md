# Proposal: Controlled AI-Assisted WebFIRE Review Pilot

## Executive Summary 
###### REDO THIS ENTIRE SECTION #########
This proposal requests approval to pilot **WebFIRE Review**, an AI-assisted screening tool for publicly available Clean Air Act compliance reports submitted through EPA's WebFIRE database.

The system would not make compliance determinations, initiate enforcement, contact facilities, or replace professional judgment. It would identify documents and passages that may warrant staff attention and present them in a consolidated review spreadsheet. EPA staff would decide whether any item merits further investigation or action using existing enforcement and inspection processes.

The proposed pilot would cover EPA Region 7: Kansas, Missouri, Nebraska, and Iowa. It would focus on recent WebFIRE submissions within the practical five-year enforcement window, with the precise date range determined by the pilot design.

The principal justification for this pilot is not cost reduction. It is that the project provides a relatively low-risk, bounded way to evaluate AI assistance while preserving data control, human authority, and traditional agency decision-making.

## Management Decision Requested
###### CONFIRM THIS IS THE ACTUAL DECISION #########
Approve a controlled Region 7 pilot that permits:

- Reviewing publicly available WebFIRE documents with the system.
- Use of the resulting summary spreadsheet by designated EPA staff for screening and investigative prioritization.
- Evaluation of the system's accuracy, usefulness, limitations, and operational risks.
- Development of requirements for any future operational release.

## Program Need

WebFIRE contains a large and varied collection of facility-submitted Clean Air Act reports. Staff generally do not review this repository comprehensively due to time constraints. Existing review is typically limited to specific facilities selected for inspection and physical reports received via mail.

This creates an opportunity to identify potentially valuable information that may otherwise remain unreviewed.

WebFIRE Review would provide staff with a narrowed list of potentially relevant reports and issues. Staff could then decide whether to:

- Review the source document in greater detail.
- Consider the facility as an inspection target.
- Conduct additional fact gathering.
- Take no further action if the issue is minor, unsupported, or not useful.

The system would support prioritization. It would not determine which facilities are in violation.

##### DISCUSS ADAPTABILITY AND OTHER PROJECTS #######

## Proposed Solution

The pipeline performs the following steps:

1. Retrieves recent WebFIRE submissions for Region 7 states.
2. Extracts files from downloaded submissions and identifies their file types.
3. Applies OCR where necessary.
4. Divides documents into reviewable text sections.
5. Uses a locally hosted open-weight language model to identify potentially important issues.
6. Validates and records the model's structured responses.
7. Produces a consolidated summary spreadsheet containing the potential issues and source-document information.

The output is designed for human review. Each potential issue can be traced back to the relevant facility, document, and source material.

##### DISCUSS ADAPTABILITY AND OTHER PROJECTS #######

## Safe and Responsible AI Use

### Local processing and data control

The pilot uses an open-weight model hosted on an EPA-owned local workstation. Documents are processed locally rather than transmitted to a commercial AI service.

The implementation can use an OpenAI-compatible endpoint, which provides flexibility if EPA later requires an approved internal server or another hosting arrangement.

WebFIRE is an appropriate pilot dataset because it is publicly available. The pilot would not require enforcement-confidential information.

### Human authority remains central

The system produces leads, not decisions.

It does not:

- Determine that a violation occurred.
- Assign legal conclusions.
- Select or mandate enforcement action.
- Contact facilities.
- Modify official records.
- Replace inspection, legal, scientific, or enforcement review.

A qualified EPA staff member would evaluate every item considered for follow-up. Existing enforcement discretion and agency procedures would remain controlling.

### Augmentation rather than replacement

The tool addresses work that is generally not being performed comprehensively today: broad screening of a large public document repository.

Its purpose is to help staff find potentially useful information that would otherwise be difficult to locate. It is not intended to automate work currently performed by staff or eliminate the need for professional review.

### Explicit uncertainty

The system records structured issue flags, descriptions, confidence values, importance values, and source metadata. These outputs are indicators for review, not findings of fact.

The pilot should treat false positives and false negatives as expected risks to measure, not as reasons to conceal uncertainty.

### Traceability

The pipeline retains intermediate artifacts, logs, source-document metadata, model outputs, and a compiled summary. This allows staff to compare a flagged issue with the underlying document and supports later evaluation of how the system performed.

## Pilot Scope

The proposed pilot would include:

- **Geography:** EPA Region 7: Kansas, Missouri, Nebraska, and Iowa.
- **Source:** Publicly available WebFIRE submissions.
- **Time period:** Recent submissions within the practical five-year statute-of-limitations window, with preference for more recent material.
- **Document volume:** No arbitrary document cap; volume would be governed by the selected date range, document types, available resources, and pilot controls.
- **Users:** Designated EPA staff with appropriate program, inspection, enforcement, or scientific knowledge.
- **Use:** Screening and prioritization only.
- **Excluded use:** Automated enforcement decisions or autonomous external communication.

## Evaluation Plan

Before any broader release, the pilot should evaluate five areas.

### 1. Technical reliability

Measure whether the pipeline:

- Retrieves the expected documents.
- Correctly extracts and routes files.
- Handles OCR and malformed files safely.
- Produces valid, traceable outputs.
- Preserves source-document metadata.
- Logs failures without silently presenting incomplete results as complete.

### 2. Review usefulness

Measure:

- Number of documents processed.
- Number of potential issues identified.
- Number of issues staff consider useful.
- Number of issues requiring additional investigation.
- Number of issues that are irrelevant or unsupported.
- Staff time required to review the output.
- Whether the output helps identify inspection or enforcement leads not otherwise found.

### 3. AI performance

Using a representative sample reviewed by qualified staff, measure:

- Potential issues correctly identified.
- Important issues missed.
- False-positive rate.
- Agreement between model outputs and staff assessments.
- Performance by document type and report category.
- Whether confidence and importance scores meaningfully assist triage.

A formal golden dataset and fixed pass thresholds should be developed with Steering Committee guidance rather than assumed in advance.

### 4. Human factors

Assess whether:

- Staff understand that outputs are suggestions rather than findings.
- The spreadsheet is easy to review.
- Source documents can be located quickly.
- The system creates inappropriate automation bias.
- Staff can override, disregard, or annotate model suggestions.
- The workflow fits existing inspection and enforcement practices.

### 5. Governance and security

Confirm:

- The selected hosting environment is approved.
- No restricted data is introduced without authorization.
- Model and prompt versions are recorded.
- Pilot results are retained appropriately.
- Access is limited to authorized users.
- Any future server-based deployment receives the required review.
- The pilot can be stopped without affecting official records or ongoing enforcement work.

## Proposed Pilot Phases

### Phase 1: Controlled preparation

- Confirm the approved data scope.
- Confirm local-workstation or server requirements.
- Establish designated users.
- Define the evaluation sample and review form.
- Document prohibited uses.
- Establish data retention and output-handling procedures.

### Phase 2: Limited operational pilot

- Run the pipeline on the approved Region 7 WebFIRE scope.
- Provide outputs to designated staff.
- Require human review of potential issues.
- Record useful findings, false positives, missed issues, and operational problems.
- Do not use outputs as standalone evidence for enforcement action.

### Phase 3: Evaluation and governance review

- Analyze technical, performance, usability, and safety results.
- Review representative flagged and unflagged documents.
- Identify model, prompt, OCR, and workflow limitations.
- Determine whether additional controls are needed.
- Decide whether the system should be revised, expanded, paused, or discontinued.

### Phase 4: Future operational release decision

A transition from pilot to broader use should require explicit approval based on:

- Acceptable evaluation results.
- Approved deployment architecture.
- Defined responsible officials and users.
- Documented operating procedures.
- Ongoing monitoring and reevaluation.
- Clear limits on acceptable use.
- A process for reporting and correcting harmful or misleading outputs.

The Steering Committee can define the formal gates and thresholds as part of approving the pilot.

## Known Limitations

The current project is an MVP. In particular:

- The evaluation harness and golden dataset are still being developed.
- The automated audit stage is not yet fully implemented.
- Model performance may vary by report type and document quality.
- OCR errors may affect downstream review.
- The system may produce false positives or miss important issues.
- A summary spreadsheet does not replace review of the original document.
- Current output is best understood as a screening aid, not a validated enforcement tool.

These limitations support a controlled pilot with explicit evaluation rather than immediate enterprise deployment.

## Resource Requirements

The pilot would require:

- An EPA-owned workstation or approved internal model-hosting environment.
- Time from the project administrator.
- Designated staff to review sample outputs.
- Program, enforcement, scientific, information-security, and AI governance input.
- Agreement on evaluation methods and acceptance criteria.
- Procedures for handling, retaining, and sharing pilot outputs.

The project is designed to operate without sending documents to an external commercial AI provider. If local hosting is not approved, the architecture could be adapted to an approved EPA-managed server or other authorized environment.

## Risks and Mitigations

| Risk | Mitigation |
| --- | --- |
| Model generates incorrect or irrelevant issues | Human review, source-document traceability, evaluation sample, and no autonomous decisions |
| Important issue is missed | Treat outputs as supplemental screening, not evidence that no issue exists |
| Staff over-trust model output | Explicit training, labels, review procedures, and management expectations |
| Data is sent to an unauthorized service | Local or approved internal hosting; deployment review before use |
| OCR or parsing errors distort documents | Preserve source files, log failures, and allow source verification |
| Pilot results are mistaken for enforcement findings | Clearly label outputs as potential issues requiring independent review |
| Model or prompt changes alter results | Version tracking and repeat evaluation after changes |
| Outputs are incomplete due to pipeline failures | Run logs, failure reporting, and completeness checks |

## Success Definition

The pilot should not be judged solely by the number of issues identified. A successful pilot would demonstrate that the system can:

1. Process public WebFIRE material within approved controls.
2. Produce traceable and understandable screening results.
3. Help staff locate potentially valuable information.
4. Preserve human decision authority.
5. Operate without unacceptable data, security, legal, or program risks.
6. Generate enough evidence to determine whether further development is warranted.

## Conclusion

WebFIRE Review offers EPA a bounded opportunity to learn how AI can assist environmental compliance work without beginning with sensitive enforcement data or delegating agency decisions to a model.

Its value is not that AI replaces professional judgment. Its value is that a locally controlled system may help staff examine a broader set of publicly available information and focus their expertise where it is most useful.

Approval of the pilot would allow EPA to evaluate that proposition under defined safeguards, while giving the Steering Committee an opportunity to establish the agency's expectations for responsible AI deployment.

**Requested action:** Approve the controlled Region 7 pilot and authorize the Steering Committee to define the evaluation criteria, deployment requirements, and transition gates for any future operational release.

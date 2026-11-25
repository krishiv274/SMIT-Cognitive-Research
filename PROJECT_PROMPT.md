# MASTER PROMPT — Cognitive Psychology Research Project

## 1. Role and objective

Act as a multidisciplinary expert in:

- Cognitive psychology
- Experimental psychology
- Cognitive neuroscience
- Research methodology
- Statistical analysis
- Full-stack software engineering
- UI/UX design
- Data engineering
- Academic research writing
- Scientific software testing

Your objective is to independently design, develop, test and document a complete, submission-ready university Cognitive Psychology research project.

Do not merely explain what should be developed. Implement the actual working project, including all source code, dependencies, configuration files, documentation, data templates, analysis scripts and report-generation functionality.

The only component that should remain incomplete is the collection of genuine human participant data.

Never fabricate participant data, research findings, statistical significance, pilot-testing observations or experimental conclusions.

The final application must allow us to conduct the experiment with real participants or directly upload a completed Excel/CSV data template. Once genuine data is available, it should automatically generate the statistical analysis, graphs and final research report.

## 2. University assignment requirements

The professor has provided the following instructions:

1. Use a framework of any pre-existing cognitive task or create a new cognitive task, including stimulus type, fixation time, interference, delay in recall and other relevant parameters.
2. Dry run the task to verify that it runs correctly.
3. Conduct the cognitive test on at least 20 individuals. Collect age, course, gender and email alongside experimental performance data.
4. Design a research question to assess how the cognitive ability being tested changes across different variables.
5. Analyse the collected data across different experimental conditions, individuals and variables, including correlations.

Additional marks are available for designing a new cognitive task, provided the underlying cognitive psychology and experimental reasoning are clearly understood and explained.

### Mandatory deliverables

1. A functional cognitive task with its running files.
2. Collected participant data under different experimental conditions in Excel or Google Sheets.
3. A research report containing statistical analysis and graphs, including appropriate t-tests, correlations and group comparisons.

## 3. Primary academic reference

I have attached the following lecture material:

`CognitivePsychology_Week14_All.pdf`

Read and thoroughly understand every page before designing or implementing the project.

Treat this PDF as the primary academic reference for the assignment.

The project must demonstrate understanding and application of the concepts taught in the lecture, including:

- Goals and subgoals
- Cues and indicators
- Mental models
- Cognitive demands
- Information filtering
- Simulation and prediction
- Action and remediation
- Alerting network
- Orienting network
- Executive network
- Fixation
- Stimulus duration
- Inter-Stimulus Interval (ISI)
- Stimulus Onset Asynchrony (SOA)
- Inter-Trial Interval (ITI)
- Working memory consolidation
- Selective attention
- Cognitive interference
- Complex Span paradigm
- Change Detection paradigm
- Floor and ceiling effects
- Order effects
- Fatigue effects
- Counterbalancing
- Latin Square design
- Speed-accuracy trade-off
- Inverse Efficiency Score
- Hardware latency
- Monitor refresh rate limitations
- Pilot testing
- Exposure timing calibration

Apply these concepts where relevant rather than artificially forcing every concept into the experiment.

Create a document mapping the project's experimental design decisions to the relevant lecture slides.

Clearly distinguish concepts directly supported by the lecture from additional scientific literature and independently proposed design decisions.

## 4. Proposed cognitive task

### Project name

**SMIT — Spatial Memory Interference Task**

### Full research title

**Investigating the Effects of Numerical and Visual Interference on Spatial Working Memory and Cognitive Performance Among University Students**

### Primary cognitive ability

Visuospatial working memory.

### Additional cognitive processes

- Selective attention
- Executive control
- Interference management
- Working memory encoding
- Working memory maintenance
- Memory recognition

Do not claim that the task independently isolates or clinically measures all these cognitive processes.

### Theoretical framework

Develop a custom experimental adaptation inspired by:

- Visual Change Detection Task
- Complex Span Task
- Working memory interference paradigms

The project should be sufficiently distinctive from a basic implementation of an existing task.

Conduct a literature review to identify similar published experiments, justify the adaptation and explain its contribution. Do not claim that it is a completely original psychological paradigm unless that claim is supported by evidence.

## 5. Research question

Use the following primary research question:

"How do different types of cognitive interference affect spatial working memory recognition accuracy and reaction time among university students?"

Secondary exploratory research question:

"How does spatial working memory performance vary with age, gender and academic course, and what relationships exist between accuracy, reaction time and interference-related performance costs?"

Refine the wording if scientifically necessary, but preserve the core objective.

## 6. Hypotheses

Define appropriate null and alternative hypotheses.

Include the following proposed hypotheses:

- H0: Interference type has no effect on spatial memory recognition performance.
- H1: Numerical interference reduces recognition accuracy relative to the control condition.
- H2: Visual interference reduces recognition accuracy relative to the control condition.
- H3: Visual interference produces greater spatial memory disruption than numerical interference.
- H4: Interference affects recognition reaction time.

Treat demographic analyses as exploratory unless there is a strong scientific justification for specific directional hypotheses.

Do not modify hypotheses after viewing genuine participant results.

## 7. Experimental design

Use a within-subjects repeated-measures experimental design.

Every participant completes all three conditions.

### Condition A — Control

Participants memorise a spatial pattern and maintain it during a delay without performing a secondary task.

### Condition B — Numerical interference

Participants memorise a spatial pattern and then verify a simple arithmetic equation as true or false.

Example:

`7 + 6 = 13`

### Condition C — Visual interference

Participants memorise a spatial pattern and then perform a secondary visual-spatial judgement task.

For example, determine whether the central cell in a newly presented grid is highlighted.

The secondary visual pattern must not systematically reveal the answer to the primary memory recognition task.

Attempt to match the numerical and visual secondary tasks in difficulty, duration and response demands.

Record secondary-task performance so that interference-task engagement can be assessed.

## 8. Experimental trial sequence

Implement the following initial experimental configuration:

| Stage | Duration | Purpose |
|---|---:|---|
| Fixation cross | 500 ms | Centre attention |
| Memory stimulus | 500 ms | Encode spatial information |
| Interference phase | 3,000 ms | Manipulate cognitive interference |
| Additional retention interval | 1,000 ms | Maintain memory representation |
| Recognition stimulus and response window | Maximum 2,000 ms | Measure recognition accuracy and RT |
| Inter-Trial Interval | Randomised 800–1,200 ms | Reduce temporal anticipation |

These timings are initial design parameters and must be configurable before the main study.

Pilot testing should determine whether they produce meaningful performance variation.

Once the main study begins, lock the experiment configuration and assign it a version identifier.

### Memory stimulus

Display a centrally positioned 3×3 grid containing nine cells.

Randomly highlight four distinct cells.

Participants must remember the spatial positions of the highlighted cells.

Use consistent cell sizes, colours, spacing, contrast and screen positioning.

### Recognition stimulus

After the interference and retention phases, display another grid.

The second grid must either:

- Match the original pattern exactly.
- Differ by moving exactly one highlighted cell to a previously unhighlighted position.

Both grids must contain the same number of highlighted cells.

The participant must determine whether the second pattern is identical to the first.

Clearly describe this outcome as delayed memory recognition, rather than free recall.

### Response keys

Primary recognition task:

- F = Same
- J = Different

Use an appropriately consistent and documented response mapping for secondary tasks.

Prevent repeated keypresses, premature responses and responses outside the designated response window from corrupting trial data.

## 9. Trials and counterbalancing

Implement:

- 6 practice trials, with 2 per condition.
- 60 experimental trials.
- 20 experimental trials per condition.
- 10 same-pattern trials per condition.
- 10 different-pattern trials per condition.

Practice trials must be excluded from primary statistical analyses.

Provide feedback during practice.

Avoid correctness feedback during experimental trials unless there is a documented scientific justification.

Randomise stimulus generation and trial order within blocks.

Support all six condition orders:

- ABC
- ACB
- BAC
- BCA
- CAB
- CBA

Distribute participants as evenly as possible across these orders.

Use a persistent, reproducible assignment mechanism rather than relying on uncontrolled randomisation alone.

Support reproducible experiment randomisation through random seeds.

Include short, standardised breaks between condition blocks.

Avoid unnecessary repetitions and systematic stimulus biases.

## 10. Scientific design requirements

Explicitly address the following:

### Goals and subgoals

Explain what participants are trying to achieve during each phase of the task.

### Cues and indicators

Identify fixation crosses, grid stimuli, interference instructions and response cues.

### Mental model

Explain the internal rules participants must understand to perform the task successfully.

### Cognitive demands

Explain memory encoding, maintenance, interference resistance, recognition and response selection.

### Floor and ceiling effects

Provide mechanisms to configure:

- Number of highlighted cells
- Memory stimulus exposure duration
- Interference duration
- Recognition difficulty
- Response deadline

Provide a pilot-testing protocol explaining how these parameters should be calibrated.

### Speed-accuracy trade-off

Measure accuracy and reaction time separately.

Optionally calculate Inverse Efficiency Score:

IES = Mean correct reaction time / Proportion correct

Explain its limitations and avoid interpreting it when accuracy is too low or the metric is otherwise unsuitable.

### Hardware and timing

Account for:

- Monitor refresh rate
- Frame duration
- Browser rendering delays
- Keyboard latency
- Focus loss
- Background tab throttling
- Dropped frames
- Timing deviations

Prefer standardised desktop or laptop testing.

Recommend the same monitor, computer and wired keyboard for all participants where feasible.

Do not claim laboratory-grade timing precision without validation.

## 11. Technology and implementation

Develop a complete, professional research application.

Preferred technology stack:

### Frontend

- React
- TypeScript
- Vite
- Tailwind CSS
- jsPsych, where suitable for the experimental engine

### Backend

- Python
- FastAPI
- Pydantic
- SQLAlchemy

### Database

- SQLite for a simple local setup.
- Optional PostgreSQL configuration for deployment.

### Statistical analysis

- pandas
- NumPy
- SciPy
- statsmodels
- pingouin, where appropriate

### Visualisation

- Plotly or equivalent interactive charts
- Matplotlib for publication-quality report figures

### File processing

- openpyxl
- CSV import/export support

### Report generation

Use a reliable Python-based approach capable of producing:

- PDF
- DOCX
- HTML
- Excel

You may change the stack if a simpler or scientifically more reliable architecture is preferable. Document your decisions.

Avoid unnecessary architectural complexity.

Use current, compatible, stable dependencies and pin their versions.

The entire project should be runnable locally without requiring paid services, subscriptions or external API keys.

Provide Docker and Docker Compose support if practical.

## 12. Participant-facing application

Create a dedicated participant interface.

### Screen 1 — Welcome

Display:

- Research title
- Brief research purpose
- Estimated duration
- General participation instructions
- Privacy information

Avoid revealing directional hypotheses that could bias behaviour.

### Screen 2 — Informed consent

Include:

- Voluntary participation
- Right to withdraw
- Purpose of the study
- Data being collected
- Data handling and confidentiality
- Relevant minimal risks
- Researcher contact placeholder
- Explicit consent checkbox

Clearly identify this as a student research study and provide editable institutional details.

Do not claim institutional ethics approval unless it has actually been granted.

### Screen 3 — Participant registration

Collect:

- Participant ID, generated automatically
- Age
- Gender, including prefer-not-to-answer
- Academic course
- Email address
- Consent status

Use adults aged 18 or older unless appropriate institutional permission and a separate consent procedure are established for minors.

Validate inputs.

Store identifying contact information separately from experimental performance data.

### Screen 4 — Instructions

Explain:

- Memory grid rules
- Recognition decisions
- Response keys
- Interference tasks
- Importance of speed and accuracy
- Time limits

Use clear visual examples.

### Screen 5 — Practice

Provide six practice trials.

Record practice data separately.

Allow the participant to repeat instructions or practice if necessary.

### Screen 6 — Main experiment

Provide:

- Full-screen experiment mode
- Standardised stimulus presentation
- Automatically assigned condition order
- Accurate reaction-time measurement
- Minimal distracting UI
- Appropriate break screens
- Automated trial-level data storage

The experiment interface must not show live performance scores that could affect behaviour.

### Screen 7 — Completion

Display a completion message and participant ID.

Confirm whether the data has been successfully saved.

Provide a recovery mechanism for interrupted or failed submissions without creating duplicate sessions.

## 13. Researcher dashboard

Create a separate researcher/admin dashboard.

Include the following pages:

### Overview

Display:

- Total registered participants
- Completed participants
- Incomplete sessions
- Valid experimental trials
- Pilot sessions
- Condition distribution
- Participant demographic distribution
- Data collection progress

The research target is a minimum of 20 eligible participants who complete the experiment.

### Participant management

Allow researchers to:

- View participant IDs and session status
- Identify incomplete sessions
- Review consent status
- Export de-identified participant data
- Withdraw or exclude participants with documented reasons
- Delete data when required under the consent procedure

Restrict access to identifying contact information.

### Experiment configuration

Allow researchers to configure experimental parameters in pilot mode.

Prevent silently changing the active main-study configuration.

Maintain configuration versions and an audit history.

### Pilot-testing mode

Allow researchers to run pilot trials without contaminating the main dataset.

Provide debugging information, event timestamps, timing deviations and stimulus previews.

### Data import/export

Support:

- Excel (.xlsx)
- CSV (.csv)
- JSON (.json)

### Statistical analysis

Provide an interactive analysis dashboard with tables, graphs and statistical test results.

### Report generation

Generate a complete academic research report from the current validated dataset.

## 14. Data collection and storage

Design a well-structured relational database.

At minimum, include:

### Participants

- participant_id
- age
- gender
- academic_course
- consent_status
- created_at

### Participant contacts

- participant_id
- email

### Experiment sessions

- session_id
- participant_id
- experiment_version
- session_type: pilot or main
- condition_order
- random_seed
- device_information
- browser_information
- estimated_refresh_rate
- start_time
- completion_time
- completion_status

### Experimental trials

- trial_id
- session_id
- participant_id
- trial_number
- block_number
- condition
- practice_trial
- original_pattern
- recognition_pattern
- correct_answer
- participant_response
- is_correct
- reaction_time_ms
- response_timeout
- interference_stimulus
- interference_correct_answer
- interference_response
- interference_accuracy
- interference_reaction_time_ms
- planned_fixation_duration_ms
- actual_fixation_duration_ms
- planned_stimulus_duration_ms
- measured_stimulus_duration_ms
- planned_interference_duration_ms
- measured_interference_duration_ms
- planned_retention_duration_ms
- measured_retention_duration_ms
- inter_trial_interval_ms
- focus_loss
- timing_quality_flag
- exclusion_status
- exclusion_reason
- timestamp

### Additional records

Include configuration versions, import history, audit logs and analysis metadata where appropriate.

Use data validation, database constraints, appropriate identifiers and duplicate prevention.

Ensure that trial data remains available even if the browser is accidentally closed after submission.

## 15. Excel data collection template

Create a ready-to-use Excel workbook named:

`SMIT_Data_Collection_Template.xlsx`

The workbook must contain:

### Sheet 1 — Instructions

Explain all columns, accepted values, required fields, validation rules and data-entry instructions.

### Sheet 2 — Participants

Include participant ID, age, gender, academic course and consent status.

### Sheet 3 — Contacts

Include participant ID and email.

Make clear that this sheet contains confidential identifying information.

### Sheet 4 — Sessions

Include experimental session identifiers, condition order, experiment version and completion status.

### Sheet 5 — Raw_Trials

Include all trial-level measurements required by the analysis.

### Sheet 6 — Participant_Summary

Include:

- Participant ID
- Age
- Gender
- Academic course
- Control accuracy
- Numerical interference accuracy
- Visual interference accuracy
- Control mean correct RT
- Numerical mean correct RT
- Visual mean correct RT
- Interference costs
- Timeout rate
- Overall accuracy
- Overall reaction time

Calculate summaries from raw trials rather than requiring researchers to manually calculate values that the application can derive.

### Sheet 7 — Data_Dictionary

Document every variable, its data type, units, allowed values, missing-value conventions and scientific interpretation.

### Sheet 8 — Experiment_Configuration

Include the exact configuration and version associated with the data.

### Template requirements

- Professionally formatted.
- Clear headers.
- Freeze panes.
- Filters.
- Data validation dropdowns.
- Appropriate numeric formats.
- Blank data-entry rows.
- Separate input and calculated fields.
- No invented participant data.

Also generate corresponding CSV templates.

Provide a simpler participant-summary-only template as an optional import format. Clearly explain which statistical analyses and quality checks are unavailable when trial-level data is missing.

## 16. Direct Excel/CSV upload functionality

This is a critical requirement.

The researcher must be able to collect the real data separately, complete the provided template and upload the completed workbook directly into the application.

Implement a drag-and-drop file upload interface.

The import system must:

1. Detect the file format.
2. Validate required sheets and columns.
3. Validate variable types.
4. Check participant and session identifiers.
5. Detect duplicate records.
6. Detect missing values.
7. Validate experimental condition names.
8. Validate reaction-time values.
9. Verify participant-to-trial relationships.
10. Verify same/different trial balance.
11. Detect inconsistent experiment versions.
12. Recalculate derived metrics from raw data.
13. Display a validation preview.
14. Show understandable row-level error messages.
15. Allow the researcher to confirm or cancel the import.
16. Commit valid data transactionally.
17. Record the import in an audit log.
18. Trigger analysis on the validated dataset.

Do not silently correct ambiguous or scientifically important data errors.

Prevent accidental overwriting and duplicate imports.

Both automatically collected experiment data and externally uploaded data must feed into the same analysis pipeline.

Do not require us to change source code, manually execute statistical scripts or rebuild the application when genuine data becomes available.

## 17. Statistical analysis engine

Implement a complete, reproducible statistical analysis pipeline.

### Data cleaning

Include:

- Missing-data assessment
- Duplicate detection
- Trial-count validation
- Practice-trial exclusion
- Pilot-session exclusion
- Timeout handling
- Invalid reaction-time detection
- Timing-quality assessment
- Incomplete-session handling
- Secondary-task engagement assessment

Define scientifically justified exclusion rules before analysing the main study.

Do not automatically exclude legitimate poor performers simply because their results contradict the hypotheses.

Document every exclusion.

Distinguish missing responses, incorrect responses and technically invalid trials.

### Descriptive statistics

Calculate:

- Participant count
- Trial count
- Mean
- Median
- Standard deviation
- Minimum
- Maximum
- Interquartile range
- Confidence intervals
- Accuracy
- Error rate
- Timeout rate
- Mean correct reaction time
- Median correct reaction time

Generate these overall and by condition.

### Condition comparisons

Primary analysis:

- Repeated-measures ANOVA for the three interference conditions, where assumptions and data quality support it.

Additional analyses:

- Paired t-test: control versus numerical interference.
- Paired t-test: control versus visual interference.
- Paired t-test: numerical versus visual interference.

Implement appropriate multiple-comparison correction, such as Holm correction.

Assess assumptions, including the distribution of paired differences and repeated-measures ANOVA sphericity where applicable.

Use appropriate corrections or nonparametric alternatives when necessary, including:

- Friedman test
- Wilcoxon signed-rank test

Report why each test was selected.

### Correlation analysis

Support:

- Age versus overall accuracy
- Age versus overall correct reaction time
- Age versus interference cost
- Accuracy versus reaction time

Use Pearson or Spearman correlation as appropriate.

Report correlation coefficients, confidence intervals where available, p-values and sample sizes.

Do not interpret correlations as causal relationships.

Do not assign numerical codes to nominal categories and treat those codes as continuous variables.

### Demographic analysis

Provide exploratory analysis for:

- Age
- Gender
- Academic course

Use suitable independent-group tests where subgroup sample sizes permit meaningful analysis.

Use Welch's t-test for appropriate independent two-group comparisons.

Use suitable ANOVA or nonparametric alternatives for multiple groups.

Suppress or qualify inferential results when groups are too small.

### Effect sizes

Report appropriate effect sizes, including:

- Paired Cohen's dz
- Independent-group effect sizes where relevant
- Partial eta-squared for relevant ANOVA results
- Appropriate nonparametric effect sizes
- Correlation coefficients

Report effect sizes alongside statistical significance.

### Interference cost

Calculate and clearly define:

- Numerical interference accuracy cost
- Visual interference accuracy cost
- Numerical interference reaction-time cost
- Visual interference reaction-time cost

Use consistent sign conventions.

### Important statistical requirements

The participant, not the individual trial, is the independent observational unit for participant-level analyses.

Do not treat 1,200 trials from 20 participants as 1,200 independent participants.

Distinguish confirmatory primary analyses from exploratory analyses.

Use a default significance level of 0.05, with appropriate adjustments.

Explain that a non-significant result does not prove the absence of an effect.

Include limitations arising from small sample size, convenience sampling, demographic imbalance and restricted age ranges.

## 18. Graphs and visualisations

Automatically generate publication-quality graphs using genuine uploaded or collected data.

Include:

1. Mean accuracy by experimental condition.
2. Mean correct reaction time by experimental condition.
3. Accuracy distributions by condition.
4. Reaction-time distributions by condition.
5. Individual participant performance across conditions.
6. Paired participant-level line plots.
7. Accuracy interference costs.
8. Reaction-time interference costs.
9. Age versus accuracy scatter plot.
10. Age versus reaction time scatter plot.
11. Accuracy versus reaction time scatter plot.
12. Correlation heatmap for suitable numerical variables.
13. Exploratory gender comparisons.
14. Exploratory academic course comparisons.
15. Participant demographic distributions.
16. Trial-level learning or fatigue trends.
17. Secondary interference-task accuracy.
18. Timing quality and missing-data summaries.

Use appropriate uncertainty indicators, including confidence intervals.

Show individual observations where useful.

Do not generate misleading charts for unavailable or insufficient data.

All graphs should include:

- Descriptive titles
- Clearly labelled axes
- Units
- Legends where necessary
- Participant sample sizes
- Consistent formatting
- Accessible colours

Provide PNG, SVG and PDF exports where practical.

## 19. Automatic research report generation

Build a report-generation engine capable of creating a complete academic research report once real data is available.

The report should contain:

### Title page

- Research title
- University name placeholder
- Department placeholder
- Course name
- Student names
- Student IDs
- Professor name
- Submission date

### Abstract

Automatically summarise:

- Research objective
- Methodology
- Actual participant count
- Main findings
- Conclusion

Do not populate findings before genuine data exists.

### Introduction

Explain spatial working memory, cognitive interference and the importance of the research question.

### Literature review

Research relevant peer-reviewed academic literature.

Discuss the theoretical basis of:

- Working memory
- Visuospatial working memory
- Visual change detection
- Complex Span tasks
- Interference
- Selective attention

Use accurate APA 7 citations and references.

Verify author names, titles, publication years and DOIs against reliable sources.

Never invent references.

### Theoretical framework

Explain the existing paradigms and how SMIT adapts their principles.

### Research question and hypotheses

Include all predefined research questions and hypotheses.

### Methodology

Include:

- Experimental design
- Participant recruitment
- Inclusion criteria
- Exclusion criteria
- Apparatus
- Software
- Stimuli
- Experimental conditions
- Timing parameters
- Counterbalancing
- Variables
- Data collection
- Ethics
- Statistical analysis plan

### Cognitive task design

Explicitly explain the lecture concepts applied to this experiment.

Include task-flow diagrams, stimulus illustrations and a temporal layout diagram.

### Pilot testing

Include automated technical test results.

Provide an editable section for genuine human pilot-testing observations and any resulting design changes.

Do not misrepresent software testing as human pilot testing.

### Results

Dynamically populate:

- Actual participant demographics
- Descriptive statistics
- Statistical tests
- Effect sizes
- Correlations
- Graphs
- Data exclusions
- Hypothesis outcomes

### Discussion

Generate an evidence-based interpretation of the actual results.

Discuss:

- Whether hypotheses were supported
- Potential cognitive explanations
- Alternative explanations
- Comparison with previous literature
- Unexpected findings
- Methodological limitations

Do not imply that a statistical association proves causation.

### Limitations

Include relevant limitations, including:

- Sample size
- Convenience sampling
- Demographic imbalance
- Browser and hardware timing
- Secondary-task difficulty differences
- Construct validity
- Practice effects
- Fatigue
- Generalisability

### Conclusion

Answer the research question using genuine results.

### References

Use verified APA 7 references.

### Appendices

Include:

- Participant instructions
- Informed consent
- Experiment screenshots
- Data dictionary
- Technical configuration
- Statistical methodology
- Pilot-testing protocol
- Additional figures

### Output formats

Generate:

- `SMIT_Research_Report.pdf`
- `SMIT_Research_Report.docx`
- `SMIT_Research_Report.html`
- `SMIT_Statistical_Results.xlsx`

Before genuine data collection, generate a preliminary research protocol/report containing all completed theoretical and methodological sections.

Mark Results, Discussion and data-dependent conclusions as pending.

Provide a clear distinction between preliminary and final reports.

## 20. Presentation and viva preparation

Create a presentation-ready slide deck explaining:

1. Project introduction
2. Research problem
3. Cognitive ability being investigated
4. Theoretical framework
5. Proposed cognitive task
6. Goals, cues, mental model and cognitive demands
7. Experimental conditions
8. Stimulus timing
9. Experimental variables
10. Research question
11. Hypotheses
12. Counterbalancing
13. Pilot-testing methodology
14. Data collection
15. Statistical analysis
16. Actual results, when available
17. Discussion
18. Limitations
19. Conclusion
20. References

Create a preliminary version without fabricated results.

Provide a mechanism to regenerate data-dependent slides after real data is imported.

Also create:

`VIVA_Preparation.md`

Include at least 30 likely viva questions and scientifically accurate answers.

Questions should cover:

- What is a cognitive task?
- What is an experimental paradigm?
- Why did you choose this framework?
- What makes the proposed task distinctive?
- What cognitive ability are you measuring?
- Why did you choose these stimulus timings?
- What is fixation?
- What are ISI, SOA and ITI?
- What is a mental model?
- What is interference?
- What is the difference between recall and recognition?
- What is the independent variable?
- What are the dependent variables?
- Why use a within-subjects design?
- Why counterbalance condition order?
- What are floor and ceiling effects?
- What is the speed-accuracy trade-off?
- What is Inverse Efficiency Score?
- Why use paired t-tests?
- Why use repeated-measures ANOVA?
- What is statistical significance?
- What is an effect size?
- Why does correlation not imply causation?
- How did you account for hardware limitations?
- What are the limitations of your task?

## 21. UI/UX requirements

Create a clean, modern, professional academic research application.

Researcher interface:

- Dashboard-based layout
- Clear navigation
- Responsive design
- Light and dark modes
- Accessible typography
- Consistent spacing
- Appropriate charts
- Data tables
- Progress indicators
- Import/export controls
- Clear empty states
- Useful validation messages

Participant experiment interface:

- Minimal distractions
- Fixed stimulus positioning
- Standardised visual appearance
- Consistent contrast
- No unnecessary animations
- No decorative elements interfering with stimuli
- No live performance dashboards during trials

Ensure that visual design never compromises experimental validity.

## 22. Testing and dry run

Do not merely write the source code and claim it works.

Execute the application and conduct automated testing in the available environment.

Implement:

### Unit tests

Test:

- Pattern generation
- Same/different pattern logic
- Stimulus balance
- Randomisation
- Counterbalancing
- Response handling
- Accuracy calculations
- Reaction-time calculations
- Interference-cost calculations
- Statistical calculations
- Data validation

### Integration tests

Test:

- Participant registration
- Consent
- Session creation
- Trial storage
- Database relationships
- Excel import
- CSV import
- Data export
- Analysis pipeline
- Report generation

### End-to-end tests

Use Playwright or an equivalent testing tool to verify:

- Complete participant workflow
- Practice trials
- Experimental trials
- Condition transitions
- Experiment completion
- Researcher dashboard
- Dataset upload
- Statistical analysis
- Report download

### Timing tests

Verify:

- Planned versus measured phase durations
- Response-window handling
- Duplicate keypress prevention
- Focus loss
- Timeout behaviour
- Session interruption handling

### Synthetic testing fixtures

Use synthetic fixtures only for software verification.

Keep them strictly isolated from the main research database.

Clearly label every synthetic fixture as synthetic.

Never include synthetic participant results in the final research submission or present them as genuine observations.

### Test report

Generate:

`Technical_Dry_Run_Report.md`

Include:

- Tests actually executed
- Pass/fail status
- Bugs discovered
- Fixes implemented
- Remaining limitations
- Manual verification requirements

Do not claim that tests were executed if the available environment did not permit execution.

Provide a separate human pilot-testing checklist that we can complete ourselves.

## 23. Privacy and security

Implement appropriate protections for participant information.

Requirements:

- Separate email addresses from research measurements.
- Use participant IDs in analysis.
- Do not expose identifying information in reports.
- Protect researcher/admin functionality.
- Validate and sanitise uploaded files.
- Prevent malicious spreadsheet content from being executed.
- Prevent SQL injection and common web vulnerabilities.
- Avoid logging private participant information unnecessarily.
- Provide data withdrawal and deletion functionality.
- Document data retention and backup procedures.
- Do not transmit participant data to third-party services without explicit authorisation.

The default application should store data locally.

Include guidance for secure deployment if online testing is required.

## 24. Expected project structure

Create a well-organised repository similar to the following:

```
SMIT-Cognitive-Research/
├── frontend/
│   ├── src/
│   ├── public/
│   ├── tests/
│   └── package.json
├── backend/
│   ├── app/
│   ├── api/
│   ├── models/
│   ├── services/
│   ├── analysis/
│   ├── reports/
│   ├── tests/
│   └── requirements.txt
├── experiment/
│   ├── configuration/
│   ├── stimuli/
│   ├── trial_engine/
│   └── documentation/
├── database/
│   ├── migrations/
│   └── schema/
├── templates/
│   ├── SMIT_Data_Collection_Template.xlsx
│   ├── Participant_Template.csv
│   ├── Session_Template.csv
│   ├── Trial_Data_Template.csv
│   └── Participant_Summary_Template.xlsx
├── research/
│   ├── Research_Protocol.md
│   ├── Literature_Review.md
│   ├── Theoretical_Framework.md
│   ├── Research_Question_and_Hypotheses.md
│   ├── Statistical_Analysis_Plan.md
│   ├── Experimental_Design.md
│   ├── Lecture_Concept_Mapping.md
│   ├── Informed_Consent.md
│   └── Participant_Instructions.md
├── pilot/
│   ├── Human_Pilot_Testing_Checklist.xlsx
│   └── Technical_Dry_Run_Report.md
├── reports/
│   ├── Preliminary_Research_Report.pdf
│   ├── Preliminary_Research_Report.docx
│   └── report_templates/
├── presentation/
│   ├── SMIT_Presentation.pptx
│   └── VIVA_Preparation.md
├── tests/
├── scripts/
├── docs/
├── .env.example
├── .gitignore
├── docker-compose.yml
├── README.md
├── SETUP.md
├── USER_GUIDE.md
└── RESEARCHER_GUIDE.md
```

You may improve this structure as necessary.

Avoid creating empty placeholder files when the corresponding functionality can be implemented.

## 25. Documentation

Provide comprehensive but understandable documentation.

### README.md

Include:

- Project overview
- Features
- Scientific purpose
- Technology stack
- Repository structure
- Installation
- Running the application
- Experiment workflow
- Data upload
- Analysis generation
- Report generation
- Troubleshooting

### SETUP.md

Provide step-by-step setup instructions for:

- macOS
- Linux
- Windows
- Docker, if included

### USER_GUIDE.md

Explain how participants complete the cognitive test.

### RESEARCHER_GUIDE.md

Explain:

1. How to configure the experiment.
2. How to run a technical dry run.
3. How to conduct human pilot testing.
4. How to finalise and lock the configuration.
5. How to recruit participants.
6. How to conduct the main experiment.
7. How to collect participant information.
8. How to export data.
9. How to complete the Excel template.
10. How to upload genuine participant data.
11. How to validate the dataset.
12. How to generate statistical analyses.
13. How to download graphs.
14. How to generate the final research report.
15. How to regenerate the final presentation.
16. How to prepare the submission.

## 26. Project execution instructions

Work autonomously.

First, inspect the attached lecture PDF and the existing workspace.

If the workspace is empty, initialise the complete project.

If files already exist, inspect them before making changes and preserve unrelated work.

Maintain an implementation checklist.

Execute the project in the following stages:

### Phase 1 — Academic research

- Analyse the lecture PDF.
- Review relevant scientific literature.
- Finalise the research methodology.
- Define experimental variables.
- Define hypotheses.
- Create the statistical analysis plan.
- Justify experimental parameters.

### Phase 2 — Architecture

- Design the application architecture.
- Design the database schema.
- Define the experiment state machine.
- Define the data import/export formats.
- Establish privacy and security requirements.

### Phase 3 — Cognitive task

- Implement participant registration.
- Implement informed consent.
- Implement instructions.
- Implement practice trials.
- Implement all experimental conditions.
- Implement randomisation and counterbalancing.
- Implement timing and response measurement.
- Implement reliable data logging.

### Phase 4 — Researcher dashboard

- Implement participant management.
- Implement experiment configuration.
- Implement pilot mode.
- Implement data management.
- Implement import/export functionality.

### Phase 5 — Statistical analysis

- Implement data validation.
- Implement data cleaning.
- Implement descriptive statistics.
- Implement inferential statistics.
- Implement effect sizes.
- Implement correlation analysis.
- Implement visualisations.

### Phase 6 — Academic deliverables

- Generate Excel templates.
- Generate the preliminary report.
- Implement final report generation.
- Generate the preliminary presentation.
- Implement data-dependent presentation updates.
- Generate viva preparation material.

### Phase 7 — Quality assurance

- Install dependencies.
- Build the application.
- Run the application.
- Execute automated tests.
- Fix errors.
- Validate the data import/export workflow.
- Test the statistical analysis pipeline using isolated synthetic fixtures.
- Verify report generation.
- Document remaining limitations.

### Phase 8 — Final handover

- Provide the finished project files.
- Provide startup commands.
- Provide a researcher workflow.
- Explain exactly what remains for genuine human data collection.
- Provide a submission checklist.

Do not stop after producing an architectural plan or a basic prototype.

Continue implementation until all feasible deliverables are complete.

If a tool, dependency or environmental limitation prevents completion of a specific feature, document the actual blocker and implement the best supported alternative.

Do not repeatedly ask for approval of routine implementation decisions.

Use reasonable defaults and document important assumptions.

## 27. Definition of done

The project is considered complete when:

- The cognitive task runs successfully.
- The participant can complete all experimental conditions.
- Registration and consent work.
- Trial data is reliably recorded.
- Reaction time and accuracy are measured.
- Randomisation and counterbalancing work.
- Pilot and main study data are separated.
- Excel/CSV templates exist.
- Genuine datasets can be uploaded directly.
- Uploaded datasets are validated.
- Statistical analysis is automatically generated.
- Graphs are automatically generated.
- PDF and DOCX report generation works.
- Research documentation is complete.
- Presentation and viva preparation material exist.
- Technical testing has been performed and documented.
- The application can be started using documented commands.
- No fabricated human participant data exists in the research database.
- Results and conclusions remain pending until genuine data is available.

## 28. Required final workflow

Design the project so that our remaining workflow is as simple as:

1. Start the application.
2. Conduct human pilot testing.
3. Finalise and lock the experimental configuration.
4. Conduct the cognitive task on at least 20 real participants.
5. Collect participant data automatically through the application or fill the provided Excel template.
6. Upload the completed Excel/CSV file if data was collected externally.
7. Validate and review the dataset.
8. Click "Run Analysis".
9. Review the statistical results and graphs.
10. Click "Generate Research Report".
11. Download the completed report, Excel results, graphs and presentation.
12. Review and approve all interpretations before academic submission.

The application must not require source-code modifications after data collection.

## 29. Non-negotiable requirements

- No fabricated human participant data.
- No fabricated research findings.
- No fabricated citations.
- No fabricated pilot observations.
- No fabricated test execution claims.
- No unsupported originality claims.
- No hardcoded research conclusions.
- No hardcoded statistical significance.
- No misleading statistical analyses.
- No identifying participant information in research reports.
- No unnecessary paid service dependencies.
- No incomplete critical functionality disguised as a finished product.
- No manual coding required after uploading genuine participant data.

Prioritise scientific validity, reproducibility, usability, privacy and completeness over unnecessary visual effects or architectural complexity.

## 30. Final instruction

Begin by reading the attached lecture PDF completely.

Then design, implement, test and document the entire project directly in the workspace.

Create the actual files, not merely code snippets or descriptions of files.

At completion, provide:

1. A concise overview of the completed project.
2. The final repository structure.
3. Application startup commands.
4. Features implemented.
5. Tests executed and their results.
6. Generated academic deliverables.
7. Excel and CSV template locations.
8. Instructions for uploading genuine participant data.
9. Instructions for generating the final analysis and report.
10. Outstanding limitations or manual verification requirements.
11. A checklist of the remaining human research activities.

Build this as a complete, functional, scientifically justified university research project ready for genuine data collection and subsequent academic submission.

Start implementation now.
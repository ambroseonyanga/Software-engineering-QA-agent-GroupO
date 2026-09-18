## Group O

## Week 1

## Project name: Software-Engineering QA Agent

## Week ending: 4th September 2026

### Work Completed Against Weekly Objectives

This week was about picking a workable problem and getting the boundaries of it straight before writing any code. We went with the Software-Engineering QA Agent use case from the recommended list, since it fits our combined coursework/repository access and gives us a codebase we're already authorised to use.

Selected the QA-agent use case and defined a single end-to-end workflow: requirements in ,candidate tests,  approval ,sandbox execution,  failure analysis ,and QA documentation.

Drafted the Project Charter, covering the problem, target user, current pain points, AI value, in/out of scope, assumptions, and constraints.

Wrote 11 user stories (US-01 to US-11) with acceptance criteria, covering the full pipeline from providing requirements through to reviewing and restricting agent actions.

Built the AI Boundary Matrix, splitting responsibilities into what the AI may reason about, what stays deterministic, and what needs human sign-off before it happens.

Set up the GitHub repository with the recommended folder structure (docs/, prompts/, knowledge/, src/, tests/, evidence/) and created the ClickUp project with Week 1 tasks assigned.

### Key Engineering Decisions and Why They Were Made

Chose the QA-agent track over the other use cases mainly because we can generate our own requirements/test data from a project we already own, which avoids the data-access risk that some of the other use cases carry.

Decided early that test execution, sandboxing, and tool permissions will be handled entirely by deterministic code, with the model restricted to reasoning tasks (interpreting requirements, proposing tests, analysing failures). This was driven by the course's own boundary rule and by the QA domain itself,  letting a model decide what code actually runs felt like exactly the kind of thing that should stay rule-based.

Agreed that no test is executed without explicit developer approval (US-04), even for low-risk-looking cases, to keep a single, consistent approval gate rather than exceptions for 'safe' tests.

### Failures / Challenges and Current Response

Scoping the workflow small enough to finish in eight weeks took longer than expected, our first draft still implicitly allowed the agent to suggest code fixes, which we cut once we re-read the constraint against ‘unrestricted source-code changes.’ Current response: scope now stops at drafting the issue/PR note, not touching code.

### Links to Evidence

GitHub repository: https://github.com/ambroseonyanga/Software-engineering-QA-agent-GroupO

ClickUp board: https://app.clickup.com/1200410000000569/v/b/li/1200410000003842

### Individual Contribution Summary

### Ambrose- charter document and git setup

### Joyce user stories, acceptance criteria and quickup task setup

### Victor- initial architecture

### Macqline - Ai boundary matrix

### Jerome- week one progress report

### Plan for Next Week (Week 2)

Finalise the model choice and document capability/cost/latency/privacy trade-offs (Model Selection Note).

Integrate the chosen model into the application for a first working baseline interaction.

Write Prompt Specification v1.0 (role, task, context, constraints, output format, failure behaviour).

Build a 10-case test set and record expected vs. actual behaviour for the baseline prompt.

Lock in the demo repository/test suite so corpus work for Week 3 can start on time.

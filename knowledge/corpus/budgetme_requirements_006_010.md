# budgetme planning categories and periods

Source: https://github.com/Joritace/BudgetMe

Retrieved: 2026-10-22

Version: a55e0b28ba5ce00c0ca6034854abbab9ae444938

Evidence status

The FR records retain the supplied SRS source-derived (SD) baseline. Acceptance criteria describe checks to perform; they are not execution results or evidence of stakeholder approval. Related NFR records retain their original SD or proposed-target (PT) labels. Clarifications remain unresolved.

Specification: C:/Users/HP/Desktop/capstone/BudgetMe_Software_Requirements_Specification.docx

Specification version: 1.0; SHA-256 d90dd05f4a43bb17699eb6787672cc55571e65617c462fdcf08a26688eddad22

FR-006 Validate the planning limit

SD  |  P1  |  Evidence S03

The system shall reject a plan whose retained category allocations plus saving goal exceed the entered income for one pay period. Categories marked for deletion shall not be counted. The validation message shall explain the category total, saving goal and income cap.

FR-006-AC01: For income 100000, allocations 70000 and goal 30000, the plan is accepted at equality.

FR-006-AC02: For the same income and allocations with goal 30001, submission is rejected and the earlier saved plan is unchanged.

FR-006-AC03: Repeat with daily, biweekly and monthly frequency. The cap remains the entered 100000, and deleting a category excludes its allocation from the total.

FR-007 Manage budget categories

SD  |  P1  |  Evidence S03

The system shall support adding, changing and removing categories through the budget form. Each category shall belong to its profile and its name shall be unique within that profile. Category names are limited to 100 characters and allocations use whole-UGX values.

FR-007-AC01: Save two distinct named categories, reload the plan, and verify that names and amounts persist. Categories marked for removal are deleted on a valid save.

FR-007-AC02: A duplicate category name in one profile is rejected without leaving a partial save. The same name may exist in a different profile.

FR-007-AC03: Probe blank, overlength and negative allocation input. Invalid or incomplete rows must not silently produce unintended budget values.

The widget advertises a non-negative minimum, but server-side negative allocation enforcement requires CL-002. Treat that case as a validation investigation, not an assumed pass.

FR-008 Edit an existing plan

SD  |  P1  |  Evidence S03

The system shall display the owner’s saved profile and categories for editing and save a valid update as one database transaction. Editing income or frequency shall refresh the stored monthly equivalent while continuing to use pay-period income for the planning cap.

FR-008-AC01: Edit the name, income and goal with valid categories. The same owned profile is updated rather than replaced by another profile.

FR-008-AC02: Set daily income to 10000. The monthly equivalent is 300000; set biweekly income to 100000 and the equivalent is 200000.

FR-008-AC03: An invalid edit preserves the previous profile and categories. Changes to historical period interpretation must be assessed under CL-004.

FR-009 Delete the owned budget

SD  |  P1  |  Evidence S03

The system shall accept budget deletion only through an authenticated POST request. Deleting the profile shall remove its dependent category, transaction, movement, savings and legacy expense rows through their cascading relationships. The account itself shall remain available.

FR-009-AC01: Delete user A’s profile and verify that its dependent financial rows are removed, user A’s account remains, and user B’s records are unchanged.

FR-009-AC02: GET /budget/delete/ returns method rejection rather than deleting data. A POST without a valid CSRF token is rejected by the configured protection.

FR-009-AC03: If the user has no budget, the request returns to Home with an informational message instead of failing.

This is destructive budget deletion; recovery and stronger confirmation are open in CL-009.

FR-010 Determine the active budget period

SD  |  P1  |  Evidence S04

The system shall use today for daily budgets, a calendar month for monthly budgets, and consecutive 14-day intervals anchored on profile creation for biweekly budgets. Both boundary dates are included when selecting expenses.

FR-010-AC01: For a monthly plan, February ends on day 28 or 29 as applicable. The period starts on the first day and crosses a year boundary correctly.

FR-010-AC02: For a profile created on 1 October 2026, biweekly periods include 1–14 October and 15–28 October; 14 October and 15 October belong to different periods.

FR-010-AC03: For a daily plan, yesterday’s expenses are excluded and today’s expenses are included. Repeat boundary checks near local midnight under CL-005.

Related quality requirements

NFR-003 Monetary accuracy and input limits

PT / P1 / related S03 S05 S06 S07

Supported whole-UGX amounts shall retain exact values through validation, storage, aggregation and presentation. Acceptance: exercise 0 where permitted, 499, 500, 501, 999999999999 and an over-limit amount in isolated valid fixtures. Compare summaries with an independent exact-integer or decimal calculation. There shall be no lost unit, silent truncation, overflow or acceptance of fractional UGX. Aggregate values may exceed an individual field value and require a documented handling rule.

NFR-004 Concurrent writes and retry safety

PT / P1 / related FR-017 FR-018 FR-020 FR-022

Concurrent accepted spending and savings requests shall not consume more than the available funds, and retrying the same logical submission shall not create an unintended duplicate financial operation. Acceptance: against balance 100000, submit two simultaneous spends of 70000; both must not commit. Repeat with a spend and a savings deposit. Simultaneous closure calls shall produce one closure row and no unhandled database error. Request identity and retry policy need CL-010; current atomic blocks alone do not establish these guarantees.

Open clarifications

CL-002 Are negative category allocations forbidden on the server?

Affected: FR-007 NFR-003

The category amount widget declares min=0, but the model field and model form do not visibly declare the same minimum validator. Confirm that all submitted category allocations must be non-negative and define treatment of whitespace-only or case-variant duplicate names. A browser control is not sufficient evidence of server enforcement.

CL-004 Which historical plan applies after an edit?

Affected: FR-008 FR-010 FR-022

Current profile income and frequency are reused for historical interpretation, and a monthly profile can be created part-way through a month. Decide whether to snapshot plans, prorate the first period, keep historical boundaries fixed, or explicitly accept the current behaviour. Clarify category renaming and deletion when old transactions retain text category names.

CL-005 Which date controls the midnight boundary?

Affected: FR-010 FR-013 NFR-003

The settings use Africa/Kampala and USE_TZ, but period services also call date.today() while ledger records use aware timestamps. Confirm that every period selection and rollover uses the Uganda local date regardless of server time zone. Include records immediately before and after local midnight in acceptance.

CL-009 What confirmation and recovery should deletion provide?

Affected: FR-009 NFR-008

Profile deletion cascades through financial records. Confirm the required warning, whether an explicit confirmation or recent authentication is needed, and whether recovery is expected. The source-derived POST and cascade behaviour does not establish a backup or restoration promise.

CL-010 How are retries and simultaneous writes controlled?

Affected: NFR-004

Define an idempotency policy, duplicate request lifetime and response on retry. Decide how balance checks and period closure should behave under competing requests. Unique row references and atomic paired writes do not settle these policies.

Source group map

S03: budgetbuddy/forms.py; budgetbuddy/views/budget.py; budgetbuddy/services/budget_validation.py; budgetbuddy/constants.py; budgetbuddy/models.py

S04: budgetbuddy/services/budget_period.py; budgetbuddy/services/period_filter.py

S05: budgetbuddy/services/dashboard.py; budgetbuddy/services/budget.py; budgetbuddy/services/transactions.py; budgetbuddy/views/dashboard.py

S06: budgetbuddy/services/savings.py; budgetbuddy/views/savings.py; budgetbuddy/forms.py; budgetbuddy/models.py

S07: budgetbuddy/services/transfers.py; budgetbuddy/views/transfer.py; budgetbuddy/forms.py; budgetbuddy/models.py


Sources

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/constants.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/forms.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/models.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/services/budget.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/services/budget_period.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/services/budget_validation.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/services/dashboard.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/services/period_filter.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/services/savings.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/services/transactions.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/services/transfers.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/views/budget.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/views/dashboard.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/views/savings.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/views/transfer.py

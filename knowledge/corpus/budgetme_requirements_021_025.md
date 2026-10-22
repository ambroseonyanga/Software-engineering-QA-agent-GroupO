# budgetme savings closure profile and form responses

Source: https://github.com/Joritace/BudgetMe

Retrieved: 2026-10-22

Version: a55e0b28ba5ce00c0ca6034854abbab9ae444938

Evidence status

The FR records retain the supplied SRS source-derived (SD) baseline. Acceptance criteria describe checks to perform; they are not execution results or evidence of stakeholder approval. Related NFR records retain their original SD or proposed-target (PT) labels. Clarifications remain unresolved.

Specification: C:/Users/HP/Desktop/capstone/BudgetMe_Software_Requirements_Specification.docx

Specification version: 1.0; SHA-256 d90dd05f4a43bb17699eb6787672cc55571e65617c462fdcf08a26688eddad22

FR-021 Display savings totals and history

SD  |  P1  |  Evidence S06

The system shall show total savings, current-period savings, the optional saving goal and a history of positive savings entries. Total savings sums the savings ledger across periods. Current-period savings includes manual deposits dated in that period and period-end rows associated with its start date.

FR-021-AC01: With manual savings 20000 this period and 30000 in an earlier period, total savings is 50000 and current-period savings is 20000.

FR-021-AC02: An applicable positive period-end entry contributes to total savings and the relevant period amount. The source label distinguishes manual savings from a pay-period remainder.

FR-021-AC03: Zero-value closure rows do not appear as positive deposits. No goal must not produce a divide-by-zero error or an invented target.

FR-022 Close an ended period into savings

SD  |  P1  |  Evidence S06

When period closure is invoked, the system shall move the non-negative remainder of an ended period into a period_end savings record. It shall exclude manual savings already moved during that period and shall not close a period that has not ended.

FR-022-AC01: For ended-period income 200000, expenses 50000 and manual savings 30000, the closure amount is 120000.

FR-022-AC02: If expenses and manual savings exhaust income, the closure amount is zero rather than negative. No entry is created for the active unended period.

FR-022-AC03: Sequential repeated closure calls do not create another period_end row for the same profile and start date. Test concurrent calls separately under NFR-004.

The implementation closes at most one ended period per invocation, scans at most 120 periods, and caches ordinary closure checks for 30 minutes. No scheduler is established; see CL-003.

FR-023 Maintain profile name and provider phones

SD  |  P2  |  Evidence S09

The system shall let the owner update their display name and optional MTN and Airtel numbers. Accepted Ugandan phone formats shall be normalised to +256 followed by the nine-digit number beginning with 7. The profile shall supply the correct stored number for each payment method.

FR-023-AC01: Save synthetic number 0770123456 and confirm it is stored as +256770123456. Equivalent supported international and space-separated inputs normalise to the same value.

FR-023-AC02: An empty phone is accepted and stored as empty. A nonmatching number is rejected with a valid-number explanation.

FR-023-AC03: Changing the MTN number does not replace the Airtel number. A subsequent MTN movement uses the saved MTN field.

The pattern does not verify provider ownership, SIM status or subscriber identity; none of those checks is claimed.

FR-024 Handle a signed in user without a budget

SD  |  P2  |  Evidence S02 S05 S09

The system shall provide setup guidance to a signed-in user who has no profile. Budget-dependent pages shall not display invented transactions or balances as if they belonged to that user. Protected summary and history APIs shall report a missing profile explicitly.

FR-024-AC01: Open Home after account creation without a budget. Setup guidance is visible and no other user’s history is returned.

FR-024-AC02: Open Transfer, Savings and Profile without a budget. The page provides the supported empty-state experience rather than performing a financial write.

FR-024-AC03: Call the transaction, movement or live-summary API without a profile. It returns a 404 error response identifying that no budget profile exists.

FR-025 Return structured form responses

SD  |  P2  |  Evidence S08

Movement and savings POST requests carrying X-BB-Ajax: 1 shall return JSON indicating success or form failure. Ordinary successful form submissions shall use the normal redirect and message flow. The response format shall not bypass authentication, CSRF checks or server-side validation.

FR-025-AC01: A valid asynchronous request returns ok true and a success message. The created data matches an equivalent ordinary form submission.

FR-025-AC02: An invalid asynchronous request returns HTTP 400, ok false, an explanatory message and field errors.

FR-025-AC03: A failed validation request does not add its intended movement or manual savings entry. Removing or changing the asynchronous header does not change monetary validation rules.

Related quality requirements

NFR-008 Persistent state and recoverability

PT / P1

Accepted financial data shall remain readable after an application restart, and the deployment shall have a documented database recovery procedure before production acceptance. Acceptance: record a spend and savings deposit, restart the application against the same database and confirm exact rows and totals. In an isolated environment, restore a designated backup and reconcile record counts and monetary totals. Recovery time, acceptable data loss and backup retention remain CL-012; no backup capability is claimed from source inspection.

NFR-010 Configuration and repeatable evaluation

PT / P2 / related S12

The evaluator shall be able to reproduce the tested setup from the recorded revision, dependency versions, configuration names and fixture procedure. Acceptance: a fresh disposable environment can apply migrations and run the selected tests without production secrets or undocumented manual data changes. Record any required OAuth SocialApp, static asset and Realtime policy setup. The existing dependency ranges and tests support investigation but do not prove repeatability.

Open clarifications

CL-003 When must all past periods be closed?

Affected: FR-022 FR-021

The closure service processes at most one ended period and can cache ordinary checks for 30 minutes. Its scan is bounded to 120 periods. Confirm the required trigger, maximum delay, catch-up behaviour after long absence and treatment of periods beyond the scan bound. No scheduled closure guarantee is established.

CL-004 Which historical plan applies after an edit?

Affected: FR-008 FR-010 FR-022

Current profile income and frequency are reused for historical interpretation, and a monthly profile can be created part-way through a month. Decide whether to snapshot plans, prorate the first period, keep historical boundaries fixed, or explicitly accept the current behaviour. Clarify category renaming and deletion when old transactions retain text category names.

CL-012 What are the production operating objectives?

Affected: NFR-008 to 010 NFR-012

Confirm the deployment platform, transport and cookie settings, backup frequency, retention, acceptable data loss, restoration time and diagnostic retention. These are needed to evaluate operational readiness and cannot be inferred from dependency declarations.

Source group map

S02: budgetbuddy/services/profile.py; budgetbuddy/services/page_context.py; budgetbuddy/views/dashboard.py; budgetbuddy/models.py

S05: budgetbuddy/services/dashboard.py; budgetbuddy/services/budget.py; budgetbuddy/services/transactions.py; budgetbuddy/views/dashboard.py

S06: budgetbuddy/services/savings.py; budgetbuddy/views/savings.py; budgetbuddy/forms.py; budgetbuddy/models.py

S08: budgetbuddy/views/http_helpers.py; budgetbuddy/views/partials.py; budgetbuddy/urls.py

S09: budgetbuddy/views/profile.py; budgetbuddy/forms.py; budgetbuddy/services/transfers.py

S12: requirements.txt; budgetbuddy/tests/test_dashboard.py; budgetbuddy/tests/test_savings.py; budgetbuddy/tests/test_supabase_realtime.py


Sources

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/forms.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/models.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/services/budget.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/services/dashboard.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/services/page_context.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/services/profile.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/services/savings.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/services/transactions.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/services/transfers.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/tests/test_dashboard.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/tests/test_savings.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/tests/test_supabase_realtime.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/urls.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/views/dashboard.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/views/http_helpers.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/views/partials.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/views/profile.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/views/savings.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/requirements.txt

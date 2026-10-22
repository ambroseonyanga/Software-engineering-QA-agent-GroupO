# budgetme reporting balance and movement selection

Source: https://github.com/Joritace/BudgetMe

Retrieved: 2026-10-22

Version: a55e0b28ba5ce00c0ca6034854abbab9ae444938

Evidence status

The FR records retain the supplied SRS source-derived (SD) baseline. Acceptance criteria describe checks to perform; they are not execution results or evidence of stakeholder approval. Related NFR records retain their original SD or proposed-target (PT) labels. Clarifications remain unresolved.

Specification: C:/Users/HP/Desktop/capstone/BudgetMe_Software_Requirements_Specification.docx

Specification version: 1.0; SHA-256 d90dd05f4a43bb17699eb6787672cc55571e65617c462fdcf08a26688eddad22

FR-011 Display dashboard budget totals

SD  |  P1  |  Evidence S05

The system shall show current-period allocations, spending and remaining amounts from the owner’s transaction ledger. Per-category summaries shall use expense transactions, and total spending shall also include expenses whose category is no longer a current allocation.

FR-011-AC01: With allocations Food 60000 and Transport 40000, and expenses Food 20000 and Transport 10000, totals are allocated 100000, spent 30000 and remaining 70000.

FR-011-AC02: An income transaction does not increase expense totals. An expense outside the active budget period is excluded.

FR-011-AC03: A category overspend is represented by a negative remaining amount and a capped bar. Zero allocation must not cause division by zero.

FR-012 Show spendable balance

SD  |  P1  |  Evidence S06

The system shall calculate available and spendable balance using period income less current-period expenses and manual savings, with a floor of zero. The configured saving goal is a plan target and does not itself reserve funds. The available balance is used by spending and manual savings validation.

FR-012-AC01: With income 200000, expenses 50000 and manual savings 30000 in the active period, available balance is 120000.

FR-012-AC02: Changing only the saving goal does not move money into savings or directly reduce the balance.

FR-012-AC03: Under the current source rule, recording an additional income deposit does not increase this balance. Report that result with CL-001 rather than silently substituting a different formula.

FR-013 Filter and order transaction history

SD  |  P2  |  Evidence S04 S05 S08

The system shall show newest transactions first and offer period filters appropriate to the income frequency. Monthly plans offer this month, this week and today; biweekly plans offer pay period, this week and today; daily plans offer today and this week. The weekly window is the trailing seven calendar dates including today.

FR-013-AC01: Seed entries on today, six days ago and seven days ago. The weekly filter includes the first two and excludes the third.

FR-013-AC02: The current-month history includes the first day through today, while pay-period history follows the active 14-day window.

FR-013-AC03: The transaction partial falls back to the frequency’s default for an unsupported filter and returns at most 40 matching rows in descending occurrence order.

History limits are presentation limits, not permission to omit rows from financial totals.

FR-014 Present dashboard insights

SD  |  P2  |  Evidence S05

The system shall present a time-based greeting, a largest-expense category and savings progress derived from the owner’s data. When a positive explicit saving goal exists, the progress amount shall use the savings ledger for that period. Without that goal, the source uses the Savings (SACCO) category as a fallback.

FR-014-AC01: With Food spending 30000 and Transport spending 10000, Food is the largest expense category. With no expenses, an empty-state value is shown.

FR-014-AC02: With goal 50000 and period savings 20000, progress is 40 percent; progress above the goal is visually capped at 100 percent.

FR-014-AC03: Examine the revenue insight using dated income rows. Its source window differs from the seven-date history filter and requires CL-006 before a single business interpretation is adopted.

FR-015 Select a movement method and category

SD  |  P1  |  Evidence S07

The system shall let the budget owner record a spend or deposit using cash, MTN Mobile Money or Airtel Money and one of the owner’s configured budget categories. A note is optional and limited to 255 characters. A provider phone is taken from Profile rather than entered as an arbitrary destination in this form.

FR-015-AC01: Each supported direction and method appears in the form. Valid categories correspond to the active profile.

FR-015-AC02: A submitted category outside that profile is rejected without a new movement or ledger transaction.

FR-015-AC03: Cash is accepted without a phone. MTN or Airtel without a stored provider number produces guidance to add the number in Profile.

Both deposit and spend currently require a category; the meaning of deposit categorisation is open in CL-001.

Related quality requirements

NFR-005 Response time and optional update delay

PT / P2

For a proposed reference load of 10 concurrent signed-in users and 10000 transaction rows per tested profile, 95 percent of core reads should complete within 2 seconds and valid financial POST responses within 3 seconds over a local test network, excluding external OAuth. Measure at least 100 requests of each type after warm-up and retain raw timings and environment details. When Realtime is available, a committed test change should appear within 5 seconds in at least 95 of 100 observations. These thresholds need adoption under CL-011.

NFR-006 Usability and responsive access

PT / P2

Core tasks shall remain usable at viewport widths of 360, 768 and 1366 CSS pixels at normal browser zoom. Acceptance: a user can create a plan, record a spend, save funds and edit a phone without clipped primary controls or horizontal scrolling of the main form. Errors identify the field or rule to correct and preserve non-sensitive submitted values where practical. Currency and direction remain understandable without relying only on colour.

NFR-007 Keyboard and assistive access

PT / P2

Core form controls shall have meaningful accessible names, visible keyboard focus and a logical tab sequence. Acceptance: complete the four core tasks from NFR-006 using only the keyboard, check that invalid submissions expose a readable error, and inspect labels and status messages with a screen reader. Progress indicators need a textual amount or percentage. This is an explicit test scope, not a claim of full accessibility certification.

Open clarifications

CL-001 How should deposits affect available funds?

Affected: FR-012 FR-015 FR-018

Recorded deposits create income transactions, but spendable balance uses configured period income and ignores those income rows. Confirm whether that is intentional or whether deposits should increase balance. Also decide how to prevent double counting planned income and actual receipts, and whether a deposit should require an expense-style category.

CL-006 What does revenue last week mean?

Affected: FR-014

The insight selects income from today minus seven days with no explicit upper date bound, while history uses today minus six days through today. Decide whether the insight means seven dates, a calendar week or another interval, and whether future-dated rows should be excluded.

CL-007 Should budget usage include savings?

Affected: FR-011 FR-026

Initial dashboard usage includes total_spent plus period_savings, while live-summary usage uses total_spent alone. Decide one formula and apply it to initial and refreshed displays. Until then, the QA Agent should report the differing outputs with the fixture that demonstrates them.

Source group map

S04: budgetbuddy/services/budget_period.py; budgetbuddy/services/period_filter.py

S05: budgetbuddy/services/dashboard.py; budgetbuddy/services/budget.py; budgetbuddy/services/transactions.py; budgetbuddy/views/dashboard.py

S06: budgetbuddy/services/savings.py; budgetbuddy/views/savings.py; budgetbuddy/forms.py; budgetbuddy/models.py

S07: budgetbuddy/services/transfers.py; budgetbuddy/views/transfer.py; budgetbuddy/forms.py; budgetbuddy/models.py

S08: budgetbuddy/views/http_helpers.py; budgetbuddy/views/partials.py; budgetbuddy/urls.py


Sources

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/forms.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/models.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/services/budget.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/services/budget_period.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/services/dashboard.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/services/period_filter.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/services/savings.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/services/transactions.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/services/transfers.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/urls.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/views/dashboard.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/views/http_helpers.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/views/partials.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/views/savings.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/views/transfer.py

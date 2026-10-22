# budgetme data rules and calculation boundaries

Source: https://github.com/Joritace/BudgetMe

Retrieved: 2026-10-22

Version: a55e0b28ba5ce00c0ca6034854abbab9ae444938

Evidence status

These rules come from the pinned model, form and service implementations. Numeric examples are calculations from those rules, not additional runtime tests.

Ownership and data relationships

BudgetProfile has an optional one-to-one relationship to the configured user model. Ordinary request-based get_active_profile selects the signed-in user. BudgetCategory, Transaction, MobileMoneyTransaction and SavingsDeposit belong to a profile. A category name is unique within its profile; deleting a profile cascades to these dependent records. The separate profile_id service argument is an internal capability and should not be treated as an authorization check.

Planning cap and income conversion

validate_budget_within_income accepts retained category allocations plus saving_goal_amount <= income_amount for one pay period. Deleted category forms, empty cleaned data and unnamed categories are excluded. period_income_from ignores frequency. For income 100000, allocations 70000 and saving goal 30000, the comparison accepts equality; goal 30001 exceeds the cap. BudgetProfile.monthly_equivalent separately multiplies daily income by 30 and biweekly income by 2. That stored approximation does not change the planning cap.

Spendable balance and recorded deposits

get_spendable_balance returns max(period income - current-period expense transactions - current-period manual savings, 0). Recorded deposit income rows do not increase that formula. For income 200000, expenses 50000 and manual savings 30000, the source formula gives 120000. Whether deposits should increase available funds is an unresolved SRS decision, CL-001, rather than an implemented promise.

Movement and savings validation

The public TransferForm and SavingsDepositForm require a whole-UGX amount of at least UGX 500, with at most 12 digits. Amount 501 is not excluded by the widget spinner step. A spend and a manual savings deposit cannot exceed the available balance; a recorded income deposit is not subject to that spending cap. Internal services enforce their own minimum and balance checks but do not duplicate every public-form limit. BudgetCategoryForm's widget min=0 does not by itself establish a server-side negative-allocation validator; SRS CL-002 leaves that investigation open.

Atomicity and closure

create_transfer writes a movement and its matching ledger transaction in one database transaction. Atomic paired writes do not prove concurrency-safe balance reservation or request idempotency. Savings closure records max(period income - expenses - manual savings, 0), processes at most one ended period per invocation, scans at most 120 periods and uses a 30-minute ordinary-check cache. A conditional uniqueness constraint covers period_end rows by profile and period_start. No scheduled catch-up service is established by that code. Concurrent calls and retry policy remain separate checks under SRS NFR-004 and CL-010.

Dates and summaries

Daily budgets use one date; monthly budgets use a calendar month; biweekly budgets use 14-day windows anchored on profile creation. History's weekly window is today minus six days through today. Several presentation helpers convert Decimal values to float. Exactness at large monetary limits and local-midnight behavior require explicit tests; they are not guaranteed by this source description.


Sources

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/forms.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/models.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/services/budget_period.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/services/budget_validation.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/services/period_filter.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/services/profile.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/services/savings.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/services/transfers.py

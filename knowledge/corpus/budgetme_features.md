# budgetme implementation and features

Source: https://github.com/Joritace/BudgetMe

Retrieved: 2026-10-22

Version: a55e0b28ba5ce00c0ca6034854abbab9ae444938 (clean local checkout; matched remote HEAD)

Evidence status

This is a source-derived description of BudgetMe, the application being tested. It is separate from the QA Agent's own charter and user stories. It is not an approved requirements specification. No tracked README or standalone requirements specification was found in this checkout; the external local SRS was not used for these documents.

Budget planning

BudgetProfile stores income amount, income frequency, an optional savings goal, currency and mobile phone details. BudgetCategory links category allocations to a profile and requires a unique category name within that profile. The default currency comes from the application constants; the budget view displays UGX.

The planning validation in validate_budget_within_income accepts category allocations plus the saving goal when their sum is less than or equal to income_amount for one pay period. period_income_from does not normalize income to a month. Deleted forms, empty cleaned data and unnamed categories are excluded from the category total. These are implementation facts, not independently approved acceptance criteria.

The budget view validates forms before saving. An over-income plan adds a form error. The accepted branch saves the profile and categories inside transaction.atomic. Budget setup accepts GET and POST and requires login. Budget deletion requires login and POST.

Money records and savings

The model layer includes Expense, Transaction, MobileMoneyTransaction and SavingsDeposit. Transaction distinguishes income and expense. SavingsDeposit distinguishes manual deposits and period-end remainder deposits, with a conditional uniqueness constraint on profile and period_start for period-end deposits.

The transfer service supports cash, MTN and Airtel records. The minimum transfer amount is UGX 500 (MIN_TRANSFER_AMOUNT). create_transfer rejects an invalid category outside the profile and an excessive withdrawal above available balance. Non-cash records require a normalized Ugandan phone number. It creates a completed MobileMoneyTransaction and a corresponding income or expense Transaction inside a database transaction. This function records movements locally; it contains no external payment-provider request. Real mobile-money settlement has not been verified.

Limits

Runtime behavior, stakeholder intent and full feature coverage were not verified by this source inspection. Possible test ideas must be reviewed separately before becoming approved requirements or executable tests.

Sources

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/models.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/forms.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/services/budget_validation.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/views/budget.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/services/transfers.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/services/savings.py

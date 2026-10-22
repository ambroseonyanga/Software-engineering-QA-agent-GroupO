# budgetme testing evidence and gaps

Source: https://github.com/Joritace/BudgetMe

Retrieved: 2026-10-22

Version: a55e0b28ba5ce00c0ca6034854abbab9ae444938 (clean local checkout; matched remote HEAD)

Evidence status

This inventory comes from reading test source. Tests were not executed during corpus creation. The presence of an assertion does not establish a passing result, adequate coverage or an approved requirement.

Existing test source

test_dashboard.py uses Django TestCase classes for budget periods, budget summaries, dashboard context, profile conversion, transaction conversion, budget setup, dashboard views, transfers and profile views. It includes tests named test_budget_rejects_over_income, test_budget_setup_saves_profile, test_budget_delete_removes_profile, test_auth_status_for_guest and test_auth_status_for_logged_in_user. Other tests inspect PWA assets, period filters and cash or mobile-money movement records.

test_savings.py contains SavingsServiceTests and SavingsViewTests. Its assertions cover a manual deposit reducing spendable balance, savings-goal accounting, rejection above available balance, period-end remainder handling, available balance, savings-page rendering and posting a deposit.

test_supabase_realtime.py uses override_settings with synthetic Supabase configuration. It checks login redirects, a returned token, status 404 when disabled, selected live-summary fields and deposits_html. The token test asserts a token string longer than 20 characters; it does not establish signature verification or a successful live subscription. These are local Django tests, not evidence of a real Supabase environment passing.

Test execution boundaries

The conventional Django command for the existing suite is python manage.py test budgetbuddy.tests. It needs compatible installed dependencies and isolated test settings/database configuration. The application settings read DATABASE_URL; do not infer a safe test database merely from the presence of db.sqlite3. No production database or provider account was contacted for this inspection.

The QA Agent separately uses a BudgetMe sandbox adapter and requires explicit test approval before execution. Connecting the project and indexing corpus documents do not approve or run application tests.

Unverified coverage

Equality at the budget planning cap, each pay frequency, saved-plan preservation after invalid POST, cross-user isolation, payment settlement and live Realtime delivery require explicit coverage review and execution evidence. This list is a set of review questions, not a claim that all such tests are missing. No pass count, coverage percentage or defect finding is claimed.

Sources

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/tests/test_dashboard.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/tests/test_savings.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/tests/test_supabase_realtime.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/tests/helpers.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/services/budget_validation.py

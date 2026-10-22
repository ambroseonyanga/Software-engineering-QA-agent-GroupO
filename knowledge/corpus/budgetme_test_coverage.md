# budgetme test coverage and execution evidence

Source: https://github.com/Joritace/BudgetMe

Retrieved: 2026-10-22

Version: a55e0b28ba5ce00c0ca6034854abbab9ae444938

Evidence status

This document distinguishes existing test definitions, the retained isolated execution and unverified acceptance coverage. Test results apply to the recorded environment and commit, not to all SRS criteria or deployed services.

Execution record: evidence/traces/budgetme_tests_20261022T173303Z/verification.json

Executed: 2026-10-22T17:33:03.103538+00:00

Existing suite and recorded environment

The three repository modules contain 51 test methods. The retained run executed those tests plus two separately authored signup checks, for 53 checks total: 49 passed, four failed assertions, zero execution errors and zero skips. Both added signup checks passed. The container used disposable SQLite settings, no network, a read-only source mount and the recorded base image. No production database, payment provider or live OAuth account was exercised.

Results by test class

| Test class | Passed | Failed | Errors | Skipped |
| --- | --- | --- | --- | --- |
| budgetbuddy.tests.test_dashboard.BudgetPeriodTests | 3 | 0 | 0 | 0 |
| budgetbuddy.tests.test_dashboard.BudgetServiceTests | 1 | 0 | 0 | 0 |
| budgetbuddy.tests.test_dashboard.BudgetSetupViewTests | 13 | 3 | 0 | 0 |
| budgetbuddy.tests.test_dashboard.DashboardServiceTests | 2 | 0 | 0 | 0 |
| budgetbuddy.tests.test_dashboard.DashboardViewTests | 2 | 1 | 0 | 0 |
| budgetbuddy.tests.test_dashboard.ProfileServiceTests | 3 | 0 | 0 | 0 |
| budgetbuddy.tests.test_dashboard.ProfileViewTests | 3 | 0 | 0 | 0 |
| budgetbuddy.tests.test_dashboard.TransactionServiceTests | 1 | 0 | 0 | 0 |
| budgetbuddy.tests.test_dashboard.TransferViewTests | 7 | 0 | 0 | 0 |
| budgetbuddy.tests.test_savings.SavingsServiceTests | 5 | 0 | 0 | 0 |
| budgetbuddy.tests.test_savings.SavingsViewTests | 2 | 0 | 0 | 0 |
| budgetbuddy.tests.test_supabase_realtime.SupabaseRealtimeApiTests | 5 | 0 | 0 | 0 |
| target_signup_retest.SignupFixtureRetest | 2 | 0 | 0 | 0 |

Coverage interpretation

The existing classes check budget periods, dashboard summaries and rendering, budget setup/deletion, transaction conversion, local cash/mobile-money movements, profile phones, savings services/views and optional Realtime API responses with controlled configuration. Source test helpers provide username when creating users; a generated create_user call that omits username is a test-fixture problem to investigate before claiming a product defect.

Two separate planning-boundary assertions passed through the QA Agent's approved Docker execution path: category 80 plus savings 20 equals income 100 and is accepted; category 81 plus savings 20 exceeds income 100 and is rejected. Their actual result is in evidence/traces/final_evaluation_20261022T172723Z/approved_execution.json. The approval in that controlled run was an automated fixture, not a stakeholder acceptance review.

The SRS adds 30 FR records and 90 separately named acceptance criteria. No complete FR/AC coverage matrix or executed verdict for all 90 follows from the 53-check run. Concurrent spending, request idempotency, full two-user adversarial ownership checks, large-amount exactness, live OAuth, Realtime delivery/RLS installation, browser privacy and production recovery need their own retained evidence. PT quality targets remain proposed. QA Agent scenario scores are not BudgetMe product-test results.

Retained suite outcomes and their discrepancies are described in budgetme_observed_failures.md. The earlier budgetme_testing.md describes the initial source inspection; tests had not been executed at that earlier corpus-creation step.


Sources

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/services/budget_validation.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/tests/helpers.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/tests/test_dashboard.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/tests/test_savings.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/tests/test_supabase_realtime.py

Local execution sources

evidence/traces/budgetme_tests_20261022T173303Z/verification.json

evidence/traces/final_evaluation_20261022T172723Z/approved_execution.json

sandbox/workflow/_qa_settings.py

# budgetme observed test failures

Source: https://github.com/Joritace/BudgetMe

Retrieved: 2026-10-22

Version: a55e0b28ba5ce00c0ca6034854abbab9ae444938

Evidence status

These are retained assertion outcomes at the pinned commit, not automatically confirmed product defects or approved changes. Failed expectations must be reviewed against the intended configuration and interface contract.

Execution record: evidence/traces/budgetme_tests_20261022T173303Z/verification.json

Executed: 2026-10-22T17:33:03.103538+00:00

Google option expectations

test_empty_dashboard_shows_google_when_configured and test_login_page_shows_google_option each expected Continue with Google and failed. Their helper creates and associates a Google SocialApp. The auth_providers context processor instead reads GOOGLE_OAUTH_CONFIGURED; that flag is false in the isolated settings. This is a configuration/expectation mismatch to clarify, not evidence that a live Google OAuth request failed. SRS FR-003 and CL-008 describe the relevant intended behavior and identity-policy question; the SRS is not an approval to change either implementation or tests.

Service worker version expectation

test_service_worker_is_served_at_root expected bb-sw-1, while the inspected worker declares SW_VERSION = bb-sw-2. The retained request reached JavaScript successfully; this assertion fails on its version-string expectation. Review whether the test should assert a version-independent contract or a deliberately pinned cache version. It does not by itself establish a broken PWA installation.

Weekly label expectation

test_period_filter_weekly expected Weekly, while period_choices_for_frequency labels weekly as This week. The assertion tests display wording. It is not proof that date filtering or amounts are wrong. The source weekly window is today minus six days through today. SRS FR-013 and CL-006 distinguish history windows from the separate revenue insight calculation.

Resolved sandbox discrepancy

The initial isolated suite had six failed assertions. Its settings omitted the explicit template DIRS used by BudgetMe, so authentication pages could fall back to allauth templates. Adding /workspace/budgetbuddy/templates to the sandbox settings matched BudgetMe/settings.py. Repeating all 53 checks reduced failures to four; guest sign-in content and the disabled-Google setup notice then passed. The BudgetMe checkout was not modified. This was a sandbox configuration correction, not a target-product fix.

Retest boundary

The four assertions above remain failed in the selected retained run. No later passing retest or stakeholder decision is established in this record. The two added signup checks passed after supplying Django's required username and using an invalid-email request to verify that no invalid user was created. Those checks do not establish complete signup coverage.


Sources

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/BudgetMe/settings.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/context_processors.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/services/budget_period.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/static/budgetbuddy/js/sw.js

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/templates/account/login.html

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/tests/helpers.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/tests/test_dashboard.py

Local execution sources

evidence/traces/budgetme_tests_20261022T173303Z/verification.json

evidence/traces/budgetme_tests_20261022T172845Z/verification.json

sandbox/workflow/_qa_settings.py

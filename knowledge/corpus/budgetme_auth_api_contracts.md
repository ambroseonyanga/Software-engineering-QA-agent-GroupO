# budgetme authentication and api contracts

Source: https://github.com/Joritace/BudgetMe

Retrieved: 2026-10-22

Version: a55e0b28ba5ce00c0ca6034854abbab9ae444938

Evidence status

Route and response contracts below are implementation facts from the pinned source. They are separate from proposed acceptance checks and do not demonstrate a deployed Google or Supabase integration.

Accounts and ownership

Django allauth supplies account routes under /accounts/. Settings select email login, disable email verification and do not log out on GET. The public GET /auth/status/ returns an authenticated boolean without financial fields. Protected views use login_required; ordinary owner lookup uses the signed-in user. A SocialApp existing in a database does not alone establish the rendered Google option: auth_providers reads GOOGLE_OAUTH_CONFIGURED. Two retained target tests expose that configuration distinction.

History fragments

Authenticated GET /api/transactions/ returns html, period and label with at most 40 matching ledger rows. Authenticated GET /api/transfers/ returns the same three keys with at most 30 movements. Missing profiles return HTTP 404 with error No budget profile. Unsupported period values fall back to the frequency's default. These endpoints return rendered fragments, not a general transaction CRUD API; there is no inspected public transaction edit/delete contract here.

Live summary

Authenticated GET /api/live/summary/ resolves the owner's budget and returns currency, total_balance, total_spent, budget_used_percent, available_balance, total_savings, period_savings, goal_percent, saving_goal and period_label. The query include=deposits adds deposits_html. A missing budget returns HTTP 404. This endpoint computes budget_used_percent from spending divided by period income; the initial dashboard also includes period savings, an unresolved formula difference described by SRS CL-007.

Realtime token

Authenticated GET /api/supabase/realtime-token/ returns token when SUPABASE_REALTIME_ENABLED is true. When disabled it returns HTTP 404 with error Supabase Realtime is not configured. create_supabase_realtime_token signs HS256 claims role=authenticated, aud=authenticated, sub as a user-ID string, django_user_id as the user key, iat and exp one hour later. This is a Realtime JWT lifetime, not a password-reset expiry. The signing secret is server configuration and is not part of the response contract. Existing token tests do not prove a live subscription or full signature/policy verification.

Form responses and payment boundary

Transfer and savings submissions with X-BB-Ajax: 1 use JSON ok and message. Invalid form responses use HTTP 400 with ok=false, message and errors; ordinary form submissions use the redirect/message path. The header does not grant authorization or skip monetary validation. Cash, MTN and Airtel are locally recorded methods. The transfer service makes no provider payment request, and no production payment endpoint, settlement acknowledgement or webhook API is established.


Sources

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/BudgetMe/settings.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/BudgetMe/urls.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/context_processors.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/services/dashboard.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/services/profile.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/services/supabase_jwt.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/services/transfers.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/urls.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/views/auth_status.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/views/http_helpers.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/views/partials.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/views/supabase_api.py

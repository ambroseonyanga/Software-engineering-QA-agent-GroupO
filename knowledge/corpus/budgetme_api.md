# budgetme routes and api evidence

Source: https://github.com/Joritace/BudgetMe

Retrieved: 2026-10-22

Version: a55e0b28ba5ce00c0ca6034854abbab9ae444938 (clean local checkout; matched remote HEAD)

Evidence status

The routes below are implemented Django routes, read from URL configuration and view code. No OpenAPI specification was found in the inspected source. This is not a general CRUD REST API contract, and the endpoints were not called during this inspection.

JSON endpoints

GET /auth/status/ returns authenticated as a boolean from request.user.is_authenticated. This view does not require login.

GET /api/transactions/ and GET /api/transfers/ require login. They return JSON containing html, period and label. The HTML comes from Django partial templates. Without a budget profile they return error "No budget profile" with status 404. The optional period query parameter is checked against choices for the profile's income frequency; invalid values fall back to the default. Transactions are limited to 40 and transfer movements to 30.

GET /api/supabase/realtime-token/ requires login. When Supabase Realtime is disabled it returns error "Supabase Realtime is not configured" with status 404. Otherwise it returns a token produced for the authenticated user. A token response is not evidence that a live Supabase subscription succeeds.

GET /api/live/summary/ requires login and a budget profile. A missing profile returns status 404. Its JSON fields are currency, total_balance, total_spent, budget_used_percent, available_balance, total_savings, period_savings, goal_percent, saving_goal and period_label. With include=deposits it adds deposits_html rendered from a template. Budget-used and goal percentages are capped at 100 in this view.

Page and asset routes

budgetbuddy/urls.py maps / to dashboard_home, /transfer/ to transfer_home, /savings/ to savings_home, /budget/ to budget_setup, /budget/delete/ to budget_delete and /profile/ to profile_home. It also maps /site.webmanifest, /sw.js and icon paths. Root routing includes /accounts/ authentication and /admin/.

In-page form helpers

http_helpers.py recognizes the header X-BB-Ajax: 1. Its success helper returns ok and message; its form-error helper returns ok=false, message and errors, defaulting to status 400. This helper evidence does not imply every route uses that response shape.

Limits

Session authentication, redirects, CSRF behavior, payload correctness and external services need separate runtime tests. No undocumented endpoints or service guarantees are assumed here.

Sources

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/BudgetMe/urls.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/urls.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/views/auth_status.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/views/partials.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/views/supabase_api.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/views/http_helpers.py

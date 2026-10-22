# budgetme summary realtime and browser behavior

Source: https://github.com/Joritace/BudgetMe

Retrieved: 2026-10-22

Version: a55e0b28ba5ce00c0ca6034854abbab9ae444938

Evidence status

The FR records retain the supplied SRS source-derived (SD) baseline. Acceptance criteria describe checks to perform; they are not execution results or evidence of stakeholder approval. Related NFR records retain their original SD or proposed-target (PT) labels. Clarifications remain unresolved.

Specification: C:/Users/HP/Desktop/capstone/BudgetMe_Software_Requirements_Specification.docx

Specification version: 1.0; SHA-256 d90dd05f4a43bb17699eb6787672cc55571e65617c462fdcf08a26688eddad22

FR-026 Expose an owned live summary

SD  |  P2  |  Evidence S10

The system shall expose GET /api/live/summary/ to an authenticated budget owner. It shall return the currency, balance, spending, savings, goal and period fields computed for that owner. The include=deposits option shall add rendered savings-history HTML.

FR-026-AC01: A profile with known fixtures returns the expected total_balance, available_balance, total_spent, total_savings and period_label.

FR-026-AC02: With include=deposits, deposits_html contains only that owner’s applicable history. Without it, the optional fragment is not required.

FR-026-AC03: Missing profiles receive 404 and anonymous clients do not receive protected values. Compare budget_used_percent with the initial dashboard and report the discrepancy described in CL-007.

FR-027 Issue an optional Realtime token

SD  |  P2  |  Evidence S10

When Supabase Realtime is configured, the system shall issue a signed one-hour JWT to the authenticated user. It shall identify the Django user for ownership policies and use the server-held secret. Without the required integration configuration, the token endpoint shall report the integration as unavailable.

FR-027-AC01: A signed-in user receives a token whose sub and django_user_id identify that user, with authenticated role and audience, and expiration one hour after issue.

FR-027-AC02: An anonymous request cannot obtain a token. A disabled integration returns HTTP 404 with the configured-unavailable error.

FR-027-AC03: Validate the token signature using a test secret. The signing secret is never included in the response or page configuration.

FR-028 Refresh pages from owned Realtime events

SD  |  P3  |  Evidence S10

When the optional client is enabled, the browser shall subscribe to transaction, movement and savings changes filtered by the current profile and trigger the existing refresh mechanism. Database SELECT policies shall additionally restrict published financial rows using the Django user identifier in the token.

FR-028-AC01: A controlled event for the owner’s subscribed table triggers a refresh after the client’s debounce interval, nominally 350 milliseconds.

FR-028-AC02: A second user cannot read the first user’s published transaction, movement or savings row through an authenticated Realtime connection.

FR-028-AC03: With Realtime absent or unavailable, ordinary server requests remain the baseline way to read and write data. A failed subscription is not a successful update.

A client-side filter alone is not access control. Publication and row-level security installation must be checked in the test database.

FR-029 Provide installable browser metadata

SD  |  P2  |  Evidence S11

The system shall serve a web manifest identifying BudgetMe, standalone display mode, root start URL and 192-pixel and 512-pixel icon references. A service worker served from /sw.js shall have scope covering the application paths. Installation is subject to the browser’s own support.

FR-029-AC01: GET /site.webmanifest returns application/manifest+json with the BudgetMe name and expected icon sizes.

FR-029-AC02: GET /sw.js returns JavaScript with Service-Worker-Allowed set to / and no-cache response behaviour.

FR-029-AC03: Resolve the manifest icons and application static resources in the evaluation deployment. Missing assets are reported rather than assumed to exist from their manifest entries.

FR-030 Control stale page and session data

SD  |  P1  |  Evidence S11

The system shall send no-store and no-cache headers for HTML responses and exclude account, administration and API requests from application-page service-worker caching. Cached application pages use a network-first strategy with fallback. The service worker supports a CLEAR_CACHES message.

FR-030-AC01: Inspect an HTML response for no-store, no-cache and must-revalidate directives and the corresponding Pragma and Expires values.

FR-030-AC02: With a registered worker, verify that POST requests and account or API responses are not stored through the application-page cache path.

FR-030-AC03: After a CLEAR_CACHES message, stored caches are removed. Separately test logout, account switching and offline fallback against the privacy target NFR-002.

Header behaviour does not by itself prove that previously cached private pages are inaccessible. Offline writes are not supported by this requirement.

Related quality requirements

NFR-011 Browser compatibility and degraded operation

PT / P2

Core online form workflows shall operate in the current stable Chrome, Edge and Firefox versions selected at execution time. Record exact versions. Acceptance: exercise sign-in, budget save, cash spend and manual saving in each browser; ordinary navigation must continue when Realtime is disabled. Browser installation and service-worker capabilities are tested only where supported and must not be confused with a guarantee of offline editing.

NFR-012 Transport and secret management

PT / P1 / related S01 S10

A production deployment shall protect authenticated traffic with HTTPS and keep signing, database and OAuth secrets server-side. Acceptance: inspect the deployed redirect and cookie configuration, browser resources and representative responses for exposed secrets; anonymous access must not mint Realtime credentials. Use test credentials for these checks. Production cookie flags, transport enforcement and host configuration need deployment evidence rather than assumptions from development settings.

Open clarifications

CL-007 Should budget usage include savings?

Affected: FR-011 FR-026

Initial dashboard usage includes total_spent plus period_savings, while live-summary usage uses total_spent alone. Decide one formula and apply it to initial and refreshed displays. Until then, the QA Agent should report the differing outputs with the fixture that demonstrates them.

CL-011 Which quality targets are accepted?

Affected: NFR-005 to 007 NFR-011

Adopt or revise the proposed load, timing, viewport, browser and accessibility targets. Record the reference environment and the scope that must pass before acceptance. No stakeholder acceptance is recorded here.

CL-012 What are the production operating objectives?

Affected: NFR-008 to 010 NFR-012

Confirm the deployment platform, transport and cookie settings, backup frequency, retention, acceptable data loss, restoration time and diagnostic retention. These are needed to evaluate operational readiness and cannot be inferred from dependency declarations.

Source group map

S01: BudgetMe/settings.py; BudgetMe/urls.py; budgetbuddy/adapters.py; budgetbuddy/services/google_oauth.py; budgetbuddy/templates/account/login.html; budgetbuddy/templates/account/signup.html; budgetbuddy/views/auth_status.py

S10: budgetbuddy/views/supabase_api.py; budgetbuddy/services/supabase_jwt.py; budgetbuddy/static/budgetbuddy/js/supabase_realtime.js; supabase/rls.sql

S11: budgetbuddy/views/pwa.py; budgetbuddy/middleware.py; budgetbuddy/static/budgetbuddy/js/sw.js


Sources

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/BudgetMe/settings.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/BudgetMe/urls.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/adapters.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/middleware.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/services/google_oauth.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/services/supabase_jwt.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/static/budgetbuddy/js/supabase_realtime.js

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/static/budgetbuddy/js/sw.js

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/templates/account/login.html

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/templates/account/signup.html

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/views/auth_status.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/views/pwa.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/views/supabase_api.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/supabase/rls.sql

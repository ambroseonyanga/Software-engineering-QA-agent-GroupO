# budgetme account access and budget ownership

Source: https://github.com/Joritace/BudgetMe

Retrieved: 2026-10-22

Version: a55e0b28ba5ce00c0ca6034854abbab9ae444938

Evidence status

The FR records retain the supplied SRS source-derived (SD) baseline. Acceptance criteria describe checks to perform; they are not execution results or evidence of stakeholder approval. Related NFR records retain their original SD or proposed-target (PT) labels. Clarifications remain unresolved.

Specification: C:/Users/HP/Desktop/capstone/BudgetMe_Software_Requirements_Specification.docx

Specification version: 1.0; SHA-256 d90dd05f4a43bb17699eb6787672cc55571e65617c462fdcf08a26688eddad22

FR-001 Register using email

SD  |  P1  |  Evidence S01

The system shall allow a visitor to create an account using an email address, password and matching password confirmation. The current allauth settings require unique email addresses and sign the user in after successful registration. Email verification is disabled in this source baseline.

FR-001-AC01: Submit a new valid email and an acceptable matching password pair. An account is created and the user enters the signed-in experience.

FR-001-AC02: Submit a duplicate email, mismatched confirmation or a password rejected by the configured validators. An error is shown and no second account is created.

FR-001-AC03: A newly registered user without a budget is shown setup guidance and no other user’s financial data.

Password recovery and email delivery are not acceptance claims under this requirement.

FR-002 Sign in and end a session

SD  |  P1  |  Evidence S01

The system shall authenticate an existing account by email and password, direct successful sign-in to Home, and provide a POST-based logout flow. The configuration remembers sessions so that closing an installed browser application does not itself imply logout.

FR-002-AC01: Valid credentials open the account’s signed-in experience. Invalid credentials leave the user unauthenticated and show a usable error.

FR-002-AC02: Logout ends access to protected resources. A GET request must not perform logout, as ACCOUNT_LOGOUT_ON_GET is false.

FR-002-AC03: GET /auth/status/ returns an authenticated boolean corresponding to the current session, without including financial data.

FR-003 Offer optional Google sign in

SD  |  P2  |  Evidence S01

The system shall offer Google authentication when the site’s provider configuration is available. The configured callback is /accounts/google/login/callback/. When it is unavailable, the account page shall retain the email access path and provide the configuration notice represented in the templates.

FR-003-AC01: With a configured provider and a successful controlled OAuth response, sign-in returns to Home and associates the expected account.

FR-003-AC02: Without provider configuration, the page remains usable through email access and does not present Google as a working configured integration.

FR-003-AC03: Cancellation or an unsuccessful provider response must not be reported as a successful sign-in. Test this using a controlled integration response.

Automatic connection by matching email is configured; its identity assurance policy needs CL-008.

FR-004 Enforce budget ownership

SD  |  P1  |  Evidence S02

The system shall select an ordinary user’s active profile from the signed-in owner relationship. Protected budget, movement, savings and profile routes shall require authentication. A supplied object identifier must not grant access to another user’s financial records.

FR-004-AC01: Create users A and B with different profiles and transactions. Each page and protected JSON response returns only the signed-in user’s records.

FR-004-AC02: An unauthenticated request to a protected route is directed to authentication rather than returning private data.

FR-004-AC03: Tampering with category form identifiers or request fields cannot update or delete user B’s rows while user A is signed in.

Ownership checks for ordinary routes are source-derived; adversarial cases remain tests to execute.

FR-005 Create a budget profile

SD  |  P1  |  Evidence S03

The system shall let a signed-in user without a budget enter a name, income amount, income frequency and optional saving goal, together with category allocations. On successful submission, the profile shall belong to that user and the application shall return to the dashboard.

FR-005-AC01: Save a valid plan. Exactly one owned profile is created with the submitted values and the corresponding categories.

FR-005-AC02: Leaving the saving goal blank is accepted and does not create a positive goal. Name and required income fields remain subject to form validation.

FR-005-AC03: Invalid profile or category input leaves the submitted form available for correction and does not persist a partly created plan.

Related quality requirements

NFR-001 Authentication and request protection

SD / P1 / S01 S02

Protected requests shall use Django session authentication and configured CSRF protection for unsafe methods. Password checks shall use the configured allauth and Django validators. Acceptance: unauthenticated protected requests expose no private records, a POST with an invalid CSRF token is rejected, and a rejected password cannot establish an account. Exercise both ordinary and asynchronous submissions.

NFR-002 Privacy across sessions and cached pages

PT / P1 / related FR-004 FR-030

No financial page or fragment belonging to a logged-out user shall become readable by another user through back navigation, cached fallback or an installed application restart. Acceptance: seed recognisable data for user A, visit all main pages, log out, sign in as B, and repeat navigation online and offline. No A-specific amount, name, phone or history entry may be displayed. This target requires browser execution and is not established by the HTML cache headers.

Open clarifications

CL-008 What identity assurance is required?

Affected: FR-001 FR-003 NFR-001

Email verification is disabled, and social email authentication with automatic connection is enabled. Confirm the intended policy for linking Google identities to an existing email account, verification evidence and recovery. Do not claim those settings establish verified ownership by themselves.

Source group map

S01: BudgetMe/settings.py; BudgetMe/urls.py; budgetbuddy/adapters.py; budgetbuddy/services/google_oauth.py; budgetbuddy/templates/account/login.html; budgetbuddy/templates/account/signup.html; budgetbuddy/views/auth_status.py

S02: budgetbuddy/services/profile.py; budgetbuddy/services/page_context.py; budgetbuddy/views/dashboard.py; budgetbuddy/models.py

S03: budgetbuddy/forms.py; budgetbuddy/views/budget.py; budgetbuddy/services/budget_validation.py; budgetbuddy/constants.py; budgetbuddy/models.py


Sources

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/BudgetMe/settings.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/BudgetMe/urls.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/adapters.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/constants.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/forms.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/models.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/services/budget_validation.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/services/google_oauth.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/services/page_context.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/services/profile.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/templates/account/login.html

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/templates/account/signup.html

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/views/auth_status.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/views/budget.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/views/dashboard.py

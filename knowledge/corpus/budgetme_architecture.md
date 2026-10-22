# budgetme architecture

Source: https://github.com/Joritace/BudgetMe

Retrieved: 2026-10-22

Version: a55e0b28ba5ce00c0ca6034854abbab9ae444938 (clean local checkout; matched remote HEAD)

Evidence status

This text describes the inspected source structure. It is not an architecture diagram or a runtime deployment assessment.

Application structure

BudgetMe is a Django web application. manage.py is the management entry point. BudgetMe contains project configuration, root URL routing, ASGI and WSGI entry points. The budgetbuddy application contains models, forms, views, services, templates, static assets, migrations and tests.

BudgetMe/urls.py mounts budgetbuddy.urls at the root, admin at /admin/ and django-allauth under /accounts/. It overrides Google login and callback routes using BudgetGoogleOAuth2Adapter. Authentication configuration does not prove that a deployed Google account connection works.

Views are split by feature, including dashboard, budget, savings, transfer, profile, partials and Supabase support. Services contain budget calculations, period filtering, profile access, transactions, savings, transfers and JWT creation. Django models and migrations define the persisted records and constraints.

Configuration and dependencies

requirements.txt declares Django >=6.0,<7.0, django-allauth, requests, cryptography, PyJWT, python-dotenv, gunicorn, whitenoise, psycopg2-binary and dj-database-url. Declared version ranges are not an installed dependency inventory or lockfile.

BudgetMe/settings.py loads environment configuration and builds its database configuration from DATABASE_URL through dj_database_url. Supabase Realtime is enabled only when its URL, anonymous key and JWT secret are populated. supabase/rls.sql supplies database policy SQL. These files show integration configuration, not proof that policies are applied to a live database. No credentials or database contents were used for this corpus.

QA Agent connection

The QA Agent's workflow_service.connect delegates to create and snapshot. It accepts a local source directory, copies supported source files to a session outside the submission repository, and records a source manifest and snapshot hash. It does not clone a GitHub URL. The BudgetMe adapter checks for budgetbuddy/models.py and BudgetMe/urls.py. Snapshots exclude settings.py, environment files, database files and dependency directories according to the existing snapshot filters.

The connected input is the existing clean local checkout at C:/Users/HP/Desktop/capstone/BudgetMe. Its origin and HEAD were checked against the repository URL and remote HEAD on the retrieval date. This is a fixed snapshot connection; later GitHub changes require a refreshed local checkout and a new snapshot.

Sources

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/manage.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/requirements.txt

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/BudgetMe/urls.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/BudgetMe/settings.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/urls.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/models.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/supabase/rls.sql

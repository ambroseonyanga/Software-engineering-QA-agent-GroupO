# budgetme movement validation and manual savings

Source: https://github.com/Joritace/BudgetMe

Retrieved: 2026-10-22

Version: a55e0b28ba5ce00c0ca6034854abbab9ae444938

Evidence status

The FR records retain the supplied SRS source-derived (SD) baseline. Acceptance criteria describe checks to perform; they are not execution results or evidence of stakeholder approval. Related NFR records retain their original SD or proposed-target (PT) labels. Clarifications remain unresolved.

Specification: C:/Users/HP/Desktop/capstone/BudgetMe_Software_Requirements_Specification.docx

Specification version: 1.0; SHA-256 d90dd05f4a43bb17699eb6787672cc55571e65617c462fdcf08a26688eddad22

FR-016 Validate movement amounts

SD  |  P1  |  Evidence S07

The system shall require a whole-UGX movement amount of at least 500 and no more than 12 digits through the public form. A spend shall not exceed the current available balance. A deposit is not subject to that spending cap.

FR-016-AC01: With balance 100000, a spend of 500 and a spend of 100000 are each valid in independent fixtures. Amount 499 is rejected.

FR-016-AC02: A spend of 100001 is rejected with an insufficient-balance error. A deposit of 100001 is accepted if the remaining fields are valid.

FR-016-AC03: Negative, fractional, nonnumeric and 13-digit amounts are rejected. A valid amount such as 501 is accepted; the 1000-unit spinner step is not a divisibility rule.

FR-017 Record a spend atomically

SD  |  P1  |  Evidence S07

For a valid spend, the system shall create one movement record and one expense transaction within a database transaction. The movement shall contain a unique reference, payment method, whole-UGX amount, timestamp and completed status. The ledger transaction shall carry the selected category and descriptive label.

FR-017-AC01: Submit a cash spend of 25000. One cash movement and one expense of 25000 are created for the owner, and the available balance falls by 25000.

FR-017-AC02: Submit a provider spend with a valid stored number. The movement has the normalised phone, and the ledger note identifies the method and direction.

FR-017-AC03: Force a failure during the second row creation in an isolated service test. Neither row from the attempted spend remains committed.

No provider settlement, charge, PIN exchange or external payment acknowledgement occurs in this service.

FR-018 Record a deposit atomically

SD  |  P1  |  Evidence S07

For a valid deposit, the system shall create a completed movement and an income transaction in one database transaction, with a unique reference and the selected category. Deposits shall appear in movement and income history. Their effect on spendable funds follows the source formula in FR-012.

FR-018-AC01: Record a cash deposit of 10000. One deposit movement and one income transaction are persisted with equal amounts and matching ownership.

FR-018-AC02: The income row does not count as category spending. The available balance remains governed by period income, expenses and manual savings.

FR-018-AC03: A failure while writing the income transaction leaves no new movement committed. The success message describes the deposit as recorded, not externally settled.

FR-019 Show movement history

SD  |  P2  |  Evidence S07 S08

The system shall display recorded movements in descending timestamp order, including direction, method, reference, amount, currency, status and timestamp. The history shall use the selected period window and retain the distinction between cash and phone-based methods.

FR-019-AC01: After a spend and a deposit, both appear with their own references and correct direction labels. Cash has no provider phone.

FR-019-AC02: The movement partial includes at most the newest 30 matching rows and returns the selected period and label with its HTML.

FR-019-AC03: Data outside the selected date window and movements belonging to another profile do not appear. Totals must not be calculated solely from the displayed 30 rows.

FR-020 Create a manual savings deposit

SD  |  P1  |  Evidence S06

The system shall allow the budget owner to move at least UGX 500 from available funds to a manual savings entry, subject to the same whole-number and 12-digit form limits. The amount shall not exceed the spendable balance. A note of up to 255 characters may accompany the entry.

FR-020-AC01: With income 200000 and no expenses, saving 30000 creates one manual savings row and leaves available balance 170000.

FR-020-AC02: After expenses of 150000 against income 200000, an attempt to save 100000 is rejected and no manual savings row is added.

FR-020-AC03: Saving exactly the remaining balance is accepted. A fractional amount, amount 499, or overlength note is rejected without an unintended manual deposit.

A validation attempt may also invoke period closure. Compare manual rows separately from any legitimate historical closure row.

Related quality requirements

NFR-009 Failure messages and diagnostic privacy

PT / P2

A failed financial request shall not present a success message, expose credentials or return a stack trace to ordinary users. Acceptance: simulate database unavailability and malformed integration responses; verify the visible failure and absence of its intended committed operation. Diagnostic records should identify the operation and failure without plaintext passwords, session cookies, JWT secrets or full provider phones. Logging configuration and retention require deployment confirmation.

Open clarifications

CL-001 How should deposits affect available funds?

Affected: FR-012 FR-015 FR-018

Recorded deposits create income transactions, but spendable balance uses configured period income and ignores those income rows. Confirm whether that is intentional or whether deposits should increase balance. Also decide how to prevent double counting planned income and actual receipts, and whether a deposit should require an expense-style category.

CL-010 How are retries and simultaneous writes controlled?

Affected: NFR-004

Define an idempotency policy, duplicate request lifetime and response on retry. Decide how balance checks and period closure should behave under competing requests. Unique row references and atomic paired writes do not settle these policies.

Source group map

S06: budgetbuddy/services/savings.py; budgetbuddy/views/savings.py; budgetbuddy/forms.py; budgetbuddy/models.py

S07: budgetbuddy/services/transfers.py; budgetbuddy/views/transfer.py; budgetbuddy/forms.py; budgetbuddy/models.py

S08: budgetbuddy/views/http_helpers.py; budgetbuddy/views/partials.py; budgetbuddy/urls.py


Sources

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/forms.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/models.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/services/savings.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/services/transfers.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/urls.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/views/http_helpers.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/views/partials.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/views/savings.py

https://github.com/Joritace/BudgetMe/blob/a55e0b28ba5ce00c0ca6034854abbab9ae444938/budgetbuddy/views/transfer.py

## AI Boundary Matrix

Software-Engineering QA Agent — BSE4104 Capstone

| AI May Do (Autonomous Reasoning) | Stays Deterministic (Rule-Based) | Requires Human Approval |
| --- | --- | --- |
| Interpret natural-language requirements and identify testable behaviours | Test execution engine (running the test suite) | Any pull-request or issue actually being submitted/posted |
| Generate candidate test cases (normal, edge, negative scenarios) | Sandbox access control and isolation from production | Executing any test flagged as high-impact or destructive |
| Retrieve relevant requirements/project documentation for context | Tool permission checks (which functions the agent may call) | Any action outside the pre-approved tool list |
| Analyze test outputs and summarize failures | Input validation on tool calls | Merging code, deploying, or modifying the repo |
| Draft issue / pull-request notes (as a draft, not a submission) | Iteration limits and stop conditions | Accessing any credential, secret, or config outside test scope |
| Suggest likely root cause of a failure based on logs/output | Logging of every agent action, tool call, and outcome | Overriding a stop condition to continue after a limit is hit |
| Prioritize which failures to summarize first | Authorization checks before any tool executes | Test cases touching real user data (if any exists) |

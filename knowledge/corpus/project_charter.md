Problem

Software development teams often have requirements and source code but lack a systematic way to quickly determine whether the implemented software satisfies those requirements. The QA process requires developers or testers to manually read requirements, identify testable behaviours, write and execute test cases, inspect failures, determine what went wrong, and document defects. The specific problem this project addresses is the disconnect between software requirements and practical QA activities, where manually translating requirements into tests and interpreting test results can lead to incomplete test coverage, missed edge cases, and inconsistent failure documentation. The proposed system addresses this problem by creating a controlled agent that connects requirements → test proposals → approved test execution → failure analysis → QA documentation into one traceable workflow.

Target User

The primary users of the Software-Engineering QA Agent are software developers and QA engineers working on small development projects. The user provides the agent with an authorized software repository, relevant software requirements or project documentation, and an approved test environment. The agent then assists the user in understanding expected software behaviour, generating candidate test cases, executing approved tests in a sandbox, reviewing test failures, producing structured failure summaries, and drafting issue or pull-request notes. The system is intended to support developers and QA engineers in their quality-assurance activities rather than replace their judgment or decision-making.

Current Pain Points

Manual Conversion of Requirements into Tests. Developers and testers must manually interpret requirements and convert them into test cases, which can be time-consuming and may result in some requirements not being adequately tested.

Inconsistent Test-Case Design. Different developers or testers may interpret the same requirement differently, leading to variations in test coverage, particularly for edge and negative cases.

Manual Failure Investigation. When a test fails, developers or testers must manually examine the test output and logs to identify the affected functionality and determine the possible cause of the failure.

Repetitive QA Documentation. After identifying a failure, developers or testers must manually prepare defect reports containing the failed test, expected behaviour, actual behaviour, and supporting evidence.

Limited Traceability. The relationship between requirements, test cases, test results, and reported issues is often maintained manually, making it difficult to trace a defect back to the requirement and test that exposed it.

AI Value

AI is valuable in this project because QA activities such as interpreting natural-language requirements, identifying testable behaviours, generating test cases, and analyzing test failures require reasoning about software behaviour. The AI will interpret requirements, generate candidate tests, suggest normal, edge and negative scenarios, retrieve relevant project information, analyze test outputs, summarize failures, and draft issue or pull-request notes. However, AI will not control safety or authorization decisions. Deterministic components will manage test execution, tool permissions, sandbox access, input validation, allowed functions, iteration limits, test-result collection, and human approval. This separation ensures that AI is used for tasks requiring reasoning while rules, validation, authorization, and high-impact decisions remain under deterministic software or human control.

Scope

In Scope

The project will implement one bounded QA workflow covering requirements/repository retrieval, AI-assisted test generation, human approval, sandbox test execution, result and failure analysis, QA reporting, and issue/PR drafting. The system will retrieve relevant project information, generate candidate tests, execute approved tests using defined tools, analyze test results against expected behaviour, produce structured failure reports, and maintain logs of agent actions, tool calls, and outcomes for traceability. The agent will operate within defined iteration limits and stop conditions.

Out of Scope

The project will not support automatic pull-request merging, production deployment, access to passwords or other secrets, arbitrary shell-command execution, production-system modification, repository data deletion, unrestricted source-code changes, or autonomous decisions on whether defects should be fixed. The agent will also not operate continuously without defined iteration limits and human oversight. These boundaries ensure that the system remains a controlled QA-support tool rather than an unrestricted autonomous software-engineering agent.

Assumptions

The project assumes that:

The team has an authorized codebase that can be used for development and demonstration.

Requirements are available in machine-readable or document form, such as Markdown, PDF or project documentation.

The selected project has executable tests or can be configured with a manageable test suite.

The test environment can be isolated from production systems.

The team can provide approximately 10–50 controlled requirements/documents or equivalent project records for the retrieval component.

The selected foundation model is accessible throughout development and testing.

Users will review actions requiring approval before they are executed.

Test execution can be exposed through controlled functions/tools rather than unrestricted terminal access.

The project can be completed within the eight-week course period.

Constraints

Time Constraint. The system must be designed, implemented, evaluated, and demonstrated within the eight-week project period.

Scope Constraint. The system must address one clearly bounded software QA problem and must not expand into a general-purpose software-development assistant.

Security Constraint. The agent must not have unrestricted access to the host machine, repository secrets, or production infrastructure.

Autonomy Constraint. The agent must operate only through approved tools and predefined limits, with human approval required for higher-impact actions.

Data Constraint. The project must use team-owned, public, synthetic, or otherwise authorized project data and must not rely on confidential institutional or proprietary data.

Engineering Constraint. The final system must demonstrate more than an LLM-based chat interface by implementing a traceable multi-step workflow with explicit tools, bounded agent behaviour, state or memory, evaluation, and guardrails.

Evaluation Constraint. The final system must be evaluated using at least 30 scenarios covering normal, edge, failure, and adversarial cases.

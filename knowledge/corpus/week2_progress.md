Week 2 Progress Report

Introduction

During Week 2, the main focus of the project was to build and test the first model-backed capability of the Software Engineering QA Agent. The aim was to establish a working baseline before introducing more advanced components such as retrieval and agent-based tool use.

The baseline was designed to test whether a locally hosted language model could understand software requirements, identify testable behaviors, propose candidate QA tests, and identify areas where a requirement was unclear or incomplete.

Model Selection and Setup

A local model was selected because the project has a zero-cost requirement and should avoid depending on paid cloud APIs. After considering the available hardware and the needs of the project, Qwen3 8B was selected as the initial model.

The model was deployed locally using Ollama. The development machine has approximately 32 GB of RAM, an Intel Core i7-1360P processor, and integrated Intel Iris Xe graphics. Since there is no dedicated GPU, the model is mainly dependent on the CPU and available system memory.

The local setup was successfully completed and Qwen3 8B was able to generate responses to software engineering and QA-related prompts.

An initial end-to-end test using the Ollama command line took approximately 43.02 seconds. This measurement represents the overall command execution time and was recorded as an initial baseline rather than as a measurement of pure model generation speed.

Prompt Specification v1.0

A Prompt Specification v1.0 was created to define how the model should behave as a Software Engineering QA Assistant.

The prompt gives the model the role of assisting developers and QA engineers with requirement analysis, test generation, defect analysis, and QA recommendations. It also provides rules intended to prevent the model from inventing requirements, test results, or system behavior.

The output structure includes a summary, findings, severity or priority, recommended tests, recommendations, and missing information.

The initial prompt was intentionally kept focused on the smallest useful QA capability so that its behavior could be evaluated before adding retrieval or autonomous tool use.

Prompt Evaluation

A 10-case prompt evaluation was carried out using different types of software requirements. The cases included normal functional requirements, boundary cases, ambiguous requirements, incomplete requirements, conditional requirements, security requirements, and performance requirements.

The evaluation focused on whether the model could:

Understand the main behavior described by a requirement.

Generate useful candidate QA tests.

Identify boundaries and negative cases.

Recognize ambiguous or incomplete requirements.

Avoid inventing system behavior.

Clearly identify assumptions when additional information was needed.

All 10 cases passed at the baseline level. However, the evaluation also identified a repeated weakness in the model's responses.

The main issue was assumption leakage. In several cases, the model introduced reasonable QA practices or common implementation details that were not actually stated in the requirement. Examples included password reset token rules, cart behavior, login redirects, password storage methods, and specific performance targets.

This did not make the baseline unusable, but it showed that the prompt needed to be more specific about the difference between information directly supported by a requirement and information that is only an assumption or recommendation.

Prompt Specification v1.1

Based on the results from the 10-case evaluation, Prompt Specification v1.1 was developed to address the weaknesses found in the baseline.

The main improvement in v1.1 is that every proposed test must now be classified as either:

Requirement-supported

Assumption-dependent

Recommendation

The new version also requires the model to provide traceability between requirement-supported tests and the specific part of the requirement that supports each test.

Another change is that assumptions and recommendations must be kept separate from requirement-supported tests. The model is also instructed not to include an expected result unless it is stated or logically required by the requirement.

The purpose of these changes is to reduce unsupported assumptions while keeping the model's useful QA reasoning and test generation capabilities.

Initial v1.1 Testing

Testing of Prompt v1.1 has started using cases from the original evaluation that showed the largest weaknesses.

The first two cases tested with v1.1 showed an improvement in how the model separates requirement-supported behavior from assumptions. For example, in the password reset case, the model placed a test involving users without an email address under assumption-dependent testing instead of presenting it as a definite system behavior.

The cart requirement also showed better separation between the four behaviors explicitly stated in the requirement and additional scenarios involving stock, persistence, authentication, and validation.

Further v1.1 testing is being carried out on the remaining selected cases to determine whether the improvement is consistent.

Challenges Encountered

One of the main challenges during this stage was making sure the evaluation measured the model's actual QA capability rather than allowing it to fill gaps in requirements using general software knowledge.

Another challenge was the relatively high end-to-end response time observed during the initial local model test. Since the model is running locally on a machine without a dedicated GPU, response time will need to be considered when designing the final workflow.

The evaluation process also showed that prompt design has a significant effect on how the model handles ambiguous requirements. This made it important to record the weaknesses of the first prompt version instead of immediately moving to more complex components.

Progress Against the Project Plan

By the end of Week 2, the following work has been completed:

Selected Qwen3 8B as the initial model.

Set up Qwen3 8B locally using Ollama.

Confirmed that the model can generate QA-related responses.

Recorded an initial end-to-end latency measurement.

Created Prompt Specification v1.0.

Created and evaluated 10 prompt test cases.

Recorded expected and actual model behavior for the evaluation.

Identified weaknesses in the baseline prompt.

Created Prompt Specification v1.1 to address the identified weaknesses.

Started testing Prompt v1.1 against the problematic cases.

The project has therefore established the required baseline model-backed capability before moving into retrieval and agent functionality.

Next Steps

The immediate next step is to complete the selected Prompt v1.1 evaluation cases and compare their results with the original v1.0 results.

After the prompt evaluation is complete, the project will move toward the next stage of the QA workflow. This will involve preparing the project information and requirements that can later be retrieved by the system, followed by the development of the controlled workflow that connects requirements, test proposals, human approval, test execution, and failure analysis.

The results from Week 2 will be used as the baseline for evaluating whether the later system components improve the overall QA workflow.

Conclusion

Week 2 established the first working version of the model-backed capability for the Software Engineering QA Agent. Qwen3 8B was successfully deployed locally and demonstrated that it can analyze software requirements and generate useful QA test proposals.

The 10-case evaluation showed that the model is capable of useful requirement analysis, but it also highlighted a consistent problem with assumptions being mixed with requirement-supported behavior. Prompt v1.1 was created specifically to address this issue by introducing stronger classification and traceability rules.

Overall, the work completed in Week 2 provides a tested baseline for the project and gives a clear direction for improving the model before adding retrieval and agent functionality.

Model Selection Note

Project:  Software Engineering QA Agent
Selected Model: Qwen3 8B
Deployment: Local deployment using Ollama

Model Selection

Qwen3 8B was selected as the foundation model for the Software Engineering QA Agent. The model was chosen because the proposed system requires strong natural-language understanding and reasoning capabilities for software engineering tasks such as requirements analysis, test-case generation, defect identification, code analysis, and explanation of software quality issues.

Capability

Qwen3 8B provides general reasoning and coding capabilities that are suitable for the QA Agent's initial model-backed functionality. It can interpret software requirements, analyze technical information, generate structured responses, and assist with software testing and quality-assurance activities. These capabilities provide a suitable foundation for future integration of project-specific knowledge through RAG.

Cost and Access

The model will be deployed locally using Ollama rather than through a paid cloud API. This allows the project to operate with a zero model/API budget and avoids dependence on paid API credits or subscriptions. The model can be accessed directly from the local development environment.

Latency

An initial local latency test was performed using PowerShell's Measure-Command around an Ollama model invocation. The observed end-to-end execution time was 43.02 seconds for the test prompt. This measurement includes model invocation and response generation and is therefore treated as an initial baseline rather than pure token-generation latency. Further measurements will be collected during evaluation.

Privacy

Local deployment provides greater control over project information because source code, requirements, test cases, and other project data do not need to be sent to an external AI API for the baseline implementation. This is particularly appropriate for a software-engineering QA system that may process project-specific information.

Limitations

The selected model will run on the project's available hardware, which has approximately 32 GB RAM, an Intel Core i7-1360P processor, and Intel Iris Xe integrated graphics. Because the system does not have a dedicated high-performance GPU, response latency may be higher than cloud-hosted or GPU-accelerated deployments. Model performance and latency will therefore be evaluated throughout development.

Selection Rationale

Qwen3 8B provides the best balance for the project between software-engineering capability, local accessibility, privacy, resource requirements, and zero monetary cost. It is therefore selected as the baseline model before introducing RAG and additional agent capabilities.

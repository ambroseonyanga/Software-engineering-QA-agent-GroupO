Software Engineering QA Agent

Week 2 - Baseline Model Interaction

Model: Qwen3 8B

Deployment: Local via Ollama

Model interaction: The model was successfully prompted through Ollama using the following test prompt:

"You are a software engineering QA assistant. Explain what a software requirement is and

give three examples of good software requirements."

Observed result: Qwen3 successfully generated a structured response explaining software requirements and provided three examples covering functional, performance, and security requirements.

Result: PASS

Purpose: This interaction confirms that the selected model can be accessed locally and generate relevant software-engineering responses before implementing the specialized QA-agent prompt.

Baseline latency measurement

Test prompt: "Explain what a software requirement is in one sentence."

Measurement method: PowerShell Measure-Command was used around the Ollama CLI invocation.

Observed end-to-end execution time: 43.0155 seconds

Rounded value: 43.02 seconds

Note: This measurement represents the end-to-end time for the local Ollama command,

including model invocation and response generation.

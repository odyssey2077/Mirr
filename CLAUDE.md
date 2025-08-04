# Mirr - PR Template-Based Code Generation

## Overview
Mirr is a Python CLI tool that automates pull request creation by using existing PRs as templates. It's designed for enterprise codebases where many PRs follow similar patterns, differing only in constants, experiment IDs, or configuration values.

## Core Workflow
1. **Extract Reference PR**: Parse GitHub PR URL from user input
2. **Fetch PR Data**: Download PR details via GitHub API
3. **Analyze Differences**: LLM identifies key differences between reference PR and desired changes
4. **User Confirmation**: Present differences for user approval via CLI
5. **Generate Changes**: LLM produces code modifications based on confirmed differences
6. **Create New PR**: Apply changes and create pull request

## Project Structure
```
src/
├── crawler/      # GitHub API integration, PR data retrieval
├── coder/        # Prompt engineering, code generation
├── model/        # LLM interface (litellm)
├── cli/          # Interactive CLI (prompt-toolkit + Rich)
├── utils/        # Shared utilities
├── main.py       # Entry point
├── requirements.txt
└── test/         # Test suite
```

## Technical Stack
- **LLM Integration**: litellm (supports Claude, GPT-4, DeepSeek, Gemini, local models)
- **Git Operations**: GitPython
- **CLI Interface**: prompt-toolkit + Rich
- **Language**: Python 3.8+

## Key Features
- Template-based PR generation reduces manual work
- Multi-model support via litellm
- Interactive CLI for user confirmation
- Automated git operations and PR creation

## Development Guidelines
- Prioritize code reuse from reference PRs
- Maintain clear separation between modules
- Handle API rate limits gracefully
- Provide clear user feedback at each step
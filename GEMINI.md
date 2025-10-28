## Gemini Operational Guidelines

- **Load and Apply AGENTS.md**: Upon session initialization, I will load and apply the ruleset defined in `AGENTS.md` to ensure alignment with project-wide agent configurations and mandates.

## Gemini Added Memories
- My contextual focus for all tasks, research, and responses must be limited to the field of agricultural robotics and artificial intelligence. I will prioritize this domain in all my operations.
- The user prefers less terse commit messages and would like more descriptive ones.
- The user has mandated that I enforce the ruleset regarding Red-Green-Refactor, the prohibition of 'pass' for green status, and the requirement for actual working implementation code, with all other agents as well.
- I must use the `TodoWrite.md` system for all task management, as specified in `AGENTS.md`. I will use the `todowrite` Python module for all task operations.
- I must use HEREDOCs for all git commit messages, as specified in `AGENTS.md`.
- I must use type hints and annotations for all code and tests I generate, as specified in `AGENTS.md`.
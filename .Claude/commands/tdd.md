ARGUMENTS: PRD file path (required), tests path or test infotmation

1. validate PRD path exists; read PRD (UTF-8); extract requirements and acceptance criteria
2. build a traceability matrix: requirement → acceptance criteria → test IDs
3. locate tests (from ARGUMENT or under tests/). if missing, run generate-tests to create them
4. enable Claude Code plan-mode; draft an implementation plan (files, APIs, data models, risks)
5. summarize the plan in chat, then proceed to implement the smallest vertical slice first
6. implement only what is needed for the first failing test (RED → GREEN minimal change)
7. conda activate py-fin; run pytest non-interactively; capture and summarize failures
8. iterate: fix next failure with minimal code; keep cycle small; refactor only when green
9. keep docs and CHANGELOG updated where behavior or interfaces change; update mapping in tests header
10. when all tests pass, run full suite and static checks; ensure no linter/type errors
11. print list of edited/created files and final test summary
12. create a descriptive commit referencing the PRD and key tests
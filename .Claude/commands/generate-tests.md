
ARGUMENTS (optional): path to a PRD file; if omitted, use the latest user request in chat

1. read requirements and acceptance criteria (from PRD file if provided, otherwise from chat)
2. extract concrete test cases; if criteria are missing, infer them and list assumptions for validation
3. map each acceptance criterion to at least one test; include edge cases and error handling
4. generate pytest tests under tests/ as test-<short-title>.py using AAA pattern and parametrization where useful
5. avoid external network calls in tests; use fixtures, temp dirs, seeded randomness, and small, deterministic sample data
6. if the target code doesn't exist yet, create clear xfail tests or TODO-marked stubs so tests document intended behavior
7. run the test suite and report a concise summary; highlight failures that indicate missing implementations vs. behavioral regressions
8. output the mapping of acceptance criteria → tests at the top of the file as a comment block for traceability
9. if assumptions were made, include an "Assumptions for Validation" section in the test file header and list them explicitly
10. print out all the test you created (file names)
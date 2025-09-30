```markdown
---
name: tdd-workflow
description: 3-agent TDD workflow with human approval gates. Usage: /tdd-workflow <description> OR /tdd-workflow --doc <path>
---

# Parse Feature Request

If `--doc <path>` or `-d <path>`: Read the document
Else if arguments provided: Use as feature description  
Else: Ask human for feature description

# Phase 1: Planning

Invoke tdd-planner:

```markdown
Use tdd-planner to create a TDD plan for: [feature description]

Create docs/tdd-plan.md and STOP for human review.
```

After completion:

```markdown
✅ Phase 1 Complete - Plan created at docs/tdd-plan.md

Review and respond: "approved" to continue, "modify [changes]" to update, or "cancel"
```

WAIT for human approval before Phase 2.

# Phase 2: Test Writing

Invoke test-driver:
```markdown
Use test-driver to write tests from docs/tdd-plan.md

Write failing tests and STOP for human review.
```

After completion:
```markdown
✅ Phase 2 Complete - Tests created

Review tests and respond: "approved" to continue, "modify [changes]" to update, or "cancel"
```

WAIT for human approval before Phase 3.

# Phase 3: Implementation

Invoke production-driver:
```markdown
Use production-driver to implement features to pass tests

Work iteratively and report progress. NEVER modify tests.
```

After completion:
```markdown
✅ Phase 3 Complete - All tests passing

Ready to: "refactor", "review", or "commit"
```
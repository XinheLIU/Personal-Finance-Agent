1. read the user's informal request and relevant context from the current chat history
2. use the prd-translator agent to produce a professional PRD
3. include sections: Executive Summary, User Stories with acceptance criteria, Functional requirements, Non-functional requirements, Technical specifications and constraints, Success metrics and definition of done, Risk assessment and mitigations, Assumptions, Clarifying Questions, and MoSCoW prioritization
4. output the PRD in the chat and save a copy to docs/ as PRD-<short-title>.md (UTF-8)
5. if information is missing or ambiguous, add a "Clarifying Questions" section and clearly mark assumptions for validation
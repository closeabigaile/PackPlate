# AI Usage

AI-assisted work for PackPlate's Project 3 team.

## Project 3 M4 review, M0 verification, and documentation - November 2026

- **AI tool:** OpenAI Codex.
- **Files:** M4 chat documentation and tests reviewed; Project 3 M0 evaluator,
  scenarios, and results checked; installation/contribution guides,
  documentation generator/reference, CI workflows, and evidence reports updated.
- **Task:** Review and document group chat and account-access rules, verify
  Project 3 M0, and complete setup, contribution, and CI documentation.
- **AI assistance:** Assisted with reviewing edge cases and test coverage,
  drafting documentation, regenerating API/reference files, inspecting hosted
  CI results, correcting workflow configuration, and running local checks.
- **Conclusion and corrections:** Added the missing Project 3 evaluator to the
  reference generator. The hosted Tests failure came from missing badge
  publishing credentials; the workflow now checks configuration before that
  optional step and retains test/coverage reports. Routine M0 checks now use
  Project 3, with inherited evaluations kept manual. Local verification passed
  474/474 application tests and Project 3 M0's 6/6 authorized journeys, with
  zero unauthorized accesses in 21 attempts and both faulty controls detected.
  Hosted verification of the updated workflows remains pending.
- **Human reviewer:** Abigail Close.

### Project 3 reports and supporting outputs

| Date                 | Report / conclusion                                                                    | Supporting output                                                                                                                                                                               |
| -------------------- | -------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| November 19–21, 2026 | [Project 3 M0 evaluation and findings](../docs/m0-eval-project3.md)                    | [Recorded M0 outcomes](../eval_project3/results.json) and [fixed scenarios](../eval_project3/scenarios.json)                                                                                    |
| November 24, 2026    | [M4 completed work](../docs/m4-chat-room.md) and [CI evidence](../docs/ci-evidence.md) | [Local verification summary](../docs/ci-evidence/local-validation.json), [backend tests](../docs/ci-evidence/local/backend.xml), and [ingestion tests](../docs/ci-evidence/local/ingestion.xml) |

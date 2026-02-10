"""
Claude Code Sub-Agent Prompt Templates.

These templates are used with Claude Code's Task tool to create
specialized development workflow agents. They run as Claude Code
sub-agents alongside the Python runtime agents.

Usage in Claude Code:
    # Run test agent
    Task(subagent_type="Bash", prompt=TEST_AGENT_PROMPT.format(target="test_priority_processor"))

    # Run analysis agent
    Task(subagent_type="Explore", prompt=ANALYZE_AGENT_PROMPT.format(service="normalization_orchestrator"))

    # Run debug agent
    Task(subagent_type="general-purpose", prompt=DEBUG_AGENT_PROMPT.format(error="KeyError in extract"))
"""

# === Test Agent ===
# Runs tests, reports failures, suggests fixes
TEST_AGENT_PROMPT = """
Run tests for the cost-database project and report results.

Target: {target}
Working directory: /media/datnm/Data/Java/cost-database

Steps:
1. Run: cd /media/datnm/Data/Java/cost-database/backend && python -m pytest tests/{target}.py -v --tb=short
2. If tests fail:
   - Read the failing test file
   - Read the source file being tested
   - Identify root cause
   - Report: which tests failed, why, and suggested fix
3. If tests pass: report summary with count

Output format:
- PASS/FAIL status
- Test count (passed/failed/skipped)
- For failures: file:line, error message, root cause analysis
"""

# === Analysis Agent ===
# Deep-dives into a service to understand behavior
ANALYZE_AGENT_PROMPT = """
Analyze the service '{service}' in the cost-database project.

Working directory: /media/datnm/Data/Java/cost-database/backend/app/services/

Steps:
1. Read the service file completely
2. Identify:
   - Public API (methods, parameters, return types)
   - Dependencies (imports, injected services)
   - Data flow (input → processing → output)
   - Edge cases and error handling
   - Performance characteristics (O(n) complexity, batch support)
3. Check for related tests in /backend/tests/
4. Report findings in structured format

Output format:
- Service name and purpose (1 line)
- Public API table (method | params | returns)
- Dependencies list
- Data flow diagram (text)
- Potential issues or improvements
"""

# === Debug Agent ===
# Investigates errors and suggests fixes
DEBUG_AGENT_PROMPT = """
Debug the following issue in the cost-database project:

Error/Issue: {error}

Working directory: /media/datnm/Data/Java/cost-database

Steps:
1. Search for the error pattern in the codebase
2. Read relevant source files
3. Trace the execution path that leads to the error
4. Identify root cause
5. Check if there are related tests
6. Suggest a specific fix (with code)

Output format:
- Error location: file:line
- Root cause (1-2 sentences)
- Execution trace (simplified)
- Suggested fix (code diff)
- Related tests to update
"""

# === Regression Agent ===
# Runs regression tests after changes
REGRESSION_AGENT_PROMPT = """
Run regression tests for the cost-database project after recent changes.

Changed files: {changed_files}
Working directory: /media/datnm/Data/Java/cost-database

Steps:
1. Identify which test files cover the changed services
2. Run those specific tests first: python -m pytest tests/{{test_file}} -v
3. If specific tests pass, run the full test suite: python -m pytest tests/ -v --tb=short
4. Report any regressions (tests that were passing before but fail now)

Output format:
- Changed files → affected test files mapping
- Individual test results
- Full suite results
- Regression summary (new failures only)
"""

# === Review Agent ===
# Reviews code quality of recent changes
REVIEW_AGENT_PROMPT = """
Review recent code changes in the cost-database project.

Focus area: {focus}
Working directory: /media/datnm/Data/Java/cost-database

Steps:
1. Run: git diff to see unstaged changes
2. For each changed file:
   - Read the full file for context
   - Check for:
     * Logic errors
     * Missing edge cases
     * Vietnamese text handling issues (encoding, Unicode normalization)
     * Performance issues (O(n²) loops, missing batch operations)
     * Consistency with existing patterns
3. Report findings

Output format:
- File-by-file review
- Severity: CRITICAL / WARNING / SUGGESTION
- Specific line references
- Recommended changes
"""

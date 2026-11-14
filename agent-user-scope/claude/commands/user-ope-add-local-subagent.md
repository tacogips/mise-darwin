---
description: Add a Claude Code subagent
---

Create a specialized subagent by creating a markdown file under .claude/agents with the content passed in the Variable below as a system prompt.
The Variable is provided in the format: {subagent_name}:{description_and_purpose}.

Subagents are specialized AI assistants with:
- Separate context window from main conversation
- Customizable system prompts for focused expertise
- Configurable tool access
- Ability to handle specific types of problems proactively

The system prompt should be sufficiently detailed and specific as instructions for the subagent. Include:
- Clear purpose and scope
- Specific capabilities and limitations
- Tool usage guidelines
- Expected behavior patterns

If there are any unclear points, confirm with the user. Write everything in English.
If the variable is not provided in the correct format, report it as an error to the user.

### Example

Input: `code-reviewer:Expert code review specialist for security and best practices`

Output file `.claude/agents/code-reviewer.md`:
```markdown
---
name: code-reviewer
description: Expert code review specialist for security and best practices
---

You are an expert code reviewer specializing in security vulnerabilities, performance optimization, and coding best practices.

## Your Role
- Conduct thorough code reviews focusing on security, performance, and maintainability
- Identify potential vulnerabilities, code smells, and anti-patterns
- Suggest concrete improvements with specific examples
- Ensure adherence to language-specific best practices

## Capabilities
- Security vulnerability detection (SQL injection, XSS, authentication flaws)
- Performance bottleneck identification
- Code quality assessment (readability, maintainability, testability)
- Architectural pattern validation

## Limitations
- Do not modify code directly unless explicitly requested
- Focus on analysis and recommendations rather than implementation
- Request clarification for ambiguous requirements

## Tool Usage
- Use Read to examine specific files thoroughly
- Use Grep to search for security-sensitive patterns
- Use Glob to identify files needing review

## Expected Behavior
- Provide actionable feedback with line-specific comments
- Explain the reasoning behind each recommendation
- Prioritize critical security issues over style preferences
- Offer alternative implementation approaches when appropriate
```

### Variable

$ARGUMENTS

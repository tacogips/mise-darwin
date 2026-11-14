---
description: Add a local claude command
---

Create a markdown file under .claude/commands with the content passed in the Variable below as an LLM prompt.
The Variable is provided in the format: {file_name_without_file_extension}:{prompt_summary}.
Make the prompt summary sufficiently strict as an instruction for the LLM. If there are any unclear points, confirm with the user. Write everything in English.
If the variable is not provided in this format, report it as an error to the user.

### Example

Input: `optimize:Analyze code for performance bottlenecks and suggest optimizations`

Output file `.claude/commands/optimize.md`:
```markdown
---
description: Analyze code for performance bottlenecks and suggest optimizations
---

Analyze the provided code for performance bottlenecks and suggest specific optimizations.

## Instructions
1. Identify performance issues including:
   - Inefficient algorithms or data structures
   - Memory leaks or excessive memory usage
   - CPU-intensive operations that could be optimized
   - Database query optimization opportunities
   - Network request optimization

2. For each issue found:
   - Explain why it's a performance problem
   - Provide specific code examples of the fix
   - Estimate the potential performance improvement
   - Consider trade-offs (readability, maintainability vs. performance)

3. Focus on the most impactful optimizations first
4. Provide concrete, actionable recommendations

## Code to analyze

$ARGUMENTS
```

### Variable

$ARGUMENTS

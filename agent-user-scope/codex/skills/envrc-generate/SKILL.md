---
name: envrc-generate
description: Use this skill when the user asks to create or generate a direnv .envrc file for the current directory with Nix flake loading and kinko direnv secret export.
allowed-tools: Bash, Read, Write, Edit, LS
argument-hint: [optional target directory]
user-invocable: true
---

# Generate .envrc

Create a `.envrc` file in the current working directory, unless the user gives a specific target directory.

Use this exact file content:

```bash
if has nix; then
    use flake .
fi

# Load secrets from kinko vault.
# Use direnv-aware export from kinko.
if command -v kinko >/dev/null 2>&1; then
  eval "$(kinko direnv export)"
fi
```

## Workflow

1. Resolve the target directory. Default to the current working directory.
2. If `.envrc` already exists and the user did not explicitly ask to overwrite it, inspect it and ask before replacing unrelated content.
3. Write the exact content above to `.envrc`.
4. Verify the file content after writing.
5. Remind the user to run `direnv allow` if the directory has not already been allowed.

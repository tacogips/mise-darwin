# Fish autoloads this file the first time `mise` is completed, so shell startup
# pays nothing. mise's generated completions delegate to the `usage` CLI, which
# Homebrew installs as a dependency of mise.
if type -q mise; and type -q usage
    mise completion fish | source
end

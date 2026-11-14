function gh-token-refresh --description 'Replace the GitHub CLI token and save it in Kinko'
    set -l old_token (env GITHUB_TOKEN= gh auth token 2>/dev/null)

    echo "Revoking current GitHub token..."
    gh auth logout -h github.com 2>/dev/null
    or true

    echo "Please login to generate a new token..."
    gh auth login -h github.com -p https -w
    or begin
        echo "Error: GitHub login failed." >&2
        return 1
    end

    set -l new_token (env GITHUB_TOKEN= gh auth token 2>/dev/null)
    if test "$old_token" = "$new_token"
        echo "Warning: Token did not change. Revoke it in GitHub settings and retry."
    else
        echo "Token successfully regenerated."
    end

    gh-token-save-shared
end

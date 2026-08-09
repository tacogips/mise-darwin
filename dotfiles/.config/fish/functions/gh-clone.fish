function gh-clone --description 'Clone GitHub using GITHUB_TOKEN from the shell or Kinko'
    if test (count $argv) -lt 1
        echo "Usage: gh-clone <repository> [destination]" >&2
        return 1
    end

    set -l token $GITHUB_TOKEN
    if test -z "$token"; and type -q kinko
        set token (kinko get GITHUB_TOKEN --shared --reveal 2>/dev/null)
    end
    if test -z "$token"
        echo "Error: GITHUB_TOKEN is unavailable. Run 'gh-token-export' or 'gh-token-save-shared'." >&2
        return 1
    end

    set -l repo $argv[1]
    set -e argv[1]
    switch $repo
        case 'git@github.com:*'
            set repo (string replace -r '^git@github\.com:' 'https://github.com/' -- $repo)
        case 'ssh://git@github.com/*'
            set repo (string replace -r '^ssh://git@github\.com/' 'https://github.com/' -- $repo)
    end

    env GITHUB_TOKEN="$token" git \
        -c credential.helper= \
        -c 'credential.https://github.com.helper=!f() { test "$1" = get || exit 0; test -n "$GITHUB_TOKEN" || exit 0; echo username=x-access-token; echo "password=$GITHUB_TOKEN"; }; f' \
        clone $repo $argv
end

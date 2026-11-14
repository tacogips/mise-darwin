function __fish_git_prompt_line_counts --description 'Show Git added and deleted line counts'
    set -l counts (command git diff --numstat HEAD -- 2>/dev/null | awk '
        $1 ~ /^[0-9]+$/ { added += $1 }
        $2 ~ /^[0-9]+$/ { deleted += $2 }
        END { print added + 0, deleted + 0 }
    ' | string split ' ')

    if test "$counts[1]" -gt 0
        printf ' %s+%d%s' (set_color green) $counts[1] (set_color normal)
    end

    if test "$counts[2]" -gt 0
        printf ' %s-%d%s' (set_color red) $counts[2] (set_color normal)
    end
end

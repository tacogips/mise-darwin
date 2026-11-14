function fish_vcs_prompt --description 'Print VCS prompts with Git line counts'
    fish_jj_prompt $argv
    and return

    fish_git_prompt $argv
    if test $status -eq 0
        __fish_git_prompt_line_counts
        return 0
    end

    fish_hg_prompt $argv
    or fish_darcs_prompt $argv
end

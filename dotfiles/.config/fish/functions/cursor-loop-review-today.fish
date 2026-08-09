function cursor-loop-review-today
    __agent-loop-run cursor-loop-review-today cursor fixed review "Review the code changes made today and improve low-quality code. The review and fixes should cover code that is generally considered low quality, unused code, deprecated code that still remains, unnecessary hardcoding, places that can be made DRY, places that are not aligned with SOLID principles without a clear reason, inappropriate variable names, cases not covered by tests, overlooked considerations, and bugs." $argv
end

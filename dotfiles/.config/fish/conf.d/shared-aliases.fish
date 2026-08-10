alias fa='fd -H'
alias gac='git add .; git commit -am'
alias dc='docker compose'
alias lg='lazygit'
alias ldc='lazydocker'
alias m='mise'
alias gch='git checkout'
alias htop='btm'
alias cc='cargo check'
alias cb='cargo check'
alias kin='kinko unlock'
alias pyac='source ./venv/bin/activate.fish'
alias tm='herdr'
alias vim='nvim'
alias n='nvim'
alias cleanup="find . -type f -name '*.DS_Store' -ls -delete"

# Codex 0.147.0 distinguishes Ctrl-I from Tab with keyboard enhancement enabled,
# but completion handles only Tab. Re-test Ctrl-I after future Codex updates.
function co --description 'Codex SOL with medium reasoning'
    command codex --dangerously-bypass-approvals-and-sandbox --model gpt-5.6-sol -c 'model_reasoning_effort="medium"' $argv
end

function cot --description 'Codex Terra with medium reasoning'
    command codex --dangerously-bypass-approvals-and-sandbox --model gpt-5.6-terra -c 'model_reasoning_effort="medium"' $argv
end

function col --description 'Codex Luna with medium reasoning'
    command codex --dangerously-bypass-approvals-and-sandbox --model gpt-5.6-luna -c 'model_reasoning_effort="medium"' $argv
end

function cor --description 'Resume a Codex session'
    command codex --dangerously-bypass-approvals-and-sandbox --model gpt-5.6-sol resume $argv
end

function corl --description 'Resume the last Codex session'
    command codex --dangerously-bypass-approvals-and-sandbox --model gpt-5.6-sol resume --last $argv
end

function cr --description 'Cursor Agent with Composer'
    command cursor-agent --yolo --approve-mcps --model composer-2.5 $argv
end

function cro --description 'Cursor Agent with GPT-5.6 SOL'
    command cursor-agent --yolo --approve-mcps --model gpt-5.6-sol $argv
end

function crc --description 'Cursor Agent with Claude Opus'
    command cursor-agent --yolo --approve-mcps --model claude-opus-4-8-high $argv
end

function crr --description 'List Cursor Agent sessions'
    command cursor-agent --yolo --approve-mcps ls $argv
end

function crrl --description 'Resume the latest Cursor Agent session'
    command cursor-agent --yolo --approve-mcps resume $argv
end

function __codex_sakana_run
    set -l model $argv[1]
    set -e argv[1]
    set -q SAKANA_API_KEY; or set -lx SAKANA_API_KEY "$SAKANA_AI_API_KEY"
    command codex --dangerously-bypass-approvals-and-sandbox --model $model \
        -c 'model_provider="sakana"' \
        -c 'model_providers.sakana.name="Sakana API"' \
        -c 'model_providers.sakana.base_url="https://api.sakana.ai/v1"' \
        -c 'model_providers.sakana.env_key="SAKANA_API_KEY"' \
        -c 'model_providers.sakana.wire_api="responses"' \
        -c model_providers.sakana.stream_idle_timeout_ms=7200000 \
        -c model_providers.sakana.stream_max_retries=5 \
        -c model_providers.sakana.request_max_retries=4 \
        -c 'model_reasoning_effort="high"' \
        -c features.image_generation=false \
        -c features.apps=false \
        $argv
end

function cof --description 'Codex with Sakana Fugu'
    __codex_sakana_run fugu $argv
end

function cofu --description 'Codex with Sakana Fugu Ultra'
    __codex_sakana_run fugu-ultra $argv
end

function codex-fugu --description 'Codex with Sakana Fugu'
    __codex_sakana_run fugu $argv
end

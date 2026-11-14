vim.g.mapleader = " "
vim.g.maplocalleader = " "
vim.g.loaded_netrw = 1
vim.g.loaded_netrwPlugin = 1
vim.g.vim_markdown_folding_disabled = 1
vim.g.go_fmt_autosave = 0
vim.g.go_fmt_command = "goimports"
vim.g.go_fmt_fail_silently = 1
vim.g.go_list_type = "quickfix"
vim.g.go_gocode_propose_builtins = 1
vim.g.go_gocode_propose_source = 0
vim.g.go_gocode_socket_type = "unix"
vim.g.go_gocode_unimported_packages = 1
vim.g.go_highlight_build_constraints = 1
vim.g.go_highlight_functions = 1
vim.g.go_highlight_interfaces = 1
vim.g.go_highlight_methods = 1
vim.g.go_highlight_operators = 1
vim.g.go_highlight_structs = 1
vim.g.go_jump_to_error = 1
vim.g.hybrid_custom_term_colors = 1
vim.g.hybrid_reduced_contrast = 1
vim.g.rustfmt_autosave = 0
vim.g.taco_open_cmd = "open"
vim.g.taco_browser_open_cmd = "open"

local options = {
  autochdir = true,
  autoread = true,
  cursorline = true,
  expandtab = false,
  foldenable = false,
  history = 2000,
  ignorecase = true,
  magic = true,
  smartcase = true,
  number = true,
  relativenumber = false,
  shada = "'2000,f1,<50",
  shortmess = "atI",
  shiftwidth = 2,
  showmatch = true,
  softtabstop = 0,
  tabstop = 2,
  title = true,
  visualbell = true,
  wildmenu = true,
  wildmode = "list:full",
  wrapscan = true,
}

for name, value in pairs(options) do
  vim.opt[name] = value
end

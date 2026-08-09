vim.g.mapleader = " "
vim.g.maplocalleader = " "
vim.g.loaded_netrw = 1
vim.g.loaded_netrwPlugin = 1
vim.g.vim_markdown_folding_disabled = 1
vim.g.go_fmt_autosave = 0
vim.g.rustfmt_autosave = 0

local options = {
  autochdir = true,
  autoread = true,
  cursorline = true,
  expandtab = false,
  foldenable = false,
  history = 2000,
  ignorecase = true,
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

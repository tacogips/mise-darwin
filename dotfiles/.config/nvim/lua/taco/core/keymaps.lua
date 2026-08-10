local map = vim.keymap.set
local silent = { silent = true }

map("c", "<C-g>", "<C-c>")
map("c", "<C-a>", "<C-b>")
map("i", "<C-d>", "<Delete>")
map("i", "<C-h>", "<BS>")
map("i", "<C-f>", "<Right>")
map("i", "<C-b>", "<Left>")
map("i", "kj", "<Esc>", silent)
map("i", "<C-v>", "<C-r>+")
map("i", "<Esc>", "<Esc><Cmd>set iminsert=0<CR>")
map("i", "<C-j>", "<Nop>")
map("i", "<C-a>", function()
  _G.vimrc.cmp.lsp()
end, { desc = "LSP completion" })
map("n", "Q", "<Nop>")
map("n", "gQ", "<Nop>")
for _, lhs in ipairs({ "gq", "g%", "gx", "g0", "g8", "ga", "g^", "g_", "g~" }) do
  map("n", lhs, "<Nop>")
end
map("n", "<Esc><Esc>", "<Cmd>nohlsearch<CR>", silent)
map("n", "k", "gk")
map("n", "+", "g;")
map("n", "J", "gJ")
map("n", "zc", "zz", { desc = "Center current line" })
map("n", "zj", "<C-e>", { desc = "Scroll view down" })
map("n", "zk", "<C-y>", { desc = "Scroll view up" })
map("n", "zm", function()
  _G.vimrc.view.align_middle()
end, { desc = "Center cursor horizontally" })
for _, lhs in ipairs({
  "za",
  "zA",
  "zo",
  "zO",
  "zr",
  "zi",
  "zf",
  "zF",
  "z=",
  "z^",
  "z.",
  "z+",
  "zp",
  "zP",
  "zw",
  "zW",
  "zx",
  "zX",
}) do
  map("n", lhs, "<Nop>")
end
map("n", "mm", "%", { desc = "Jump to matching bracket" })
map("n", "ms", "ys", { desc = "Add surround", remap = true })
map("n", "mr", "cs", { desc = "Replace surround", remap = true })
map("n", "md", "ds", { desc = "Delete surround", remap = true })
map("n", "ma", "va", { desc = "Select around textobject", remap = true })
map("n", "mi", "vi", { desc = "Select inside textobject", remap = true })

map("n", "<leader>.", "<Cmd>edit!<CR>", { desc = "Reload file" })
map("n", "<leader>w", "<Cmd>write<CR>", { desc = "Write file" })
map("n", "<leader>q", "<Cmd>quit!<CR>", { desc = "Force quit" })
map("n", "<leader>c", function()
  vim.fn.setreg("+", vim.fn.expand("%:p"))
end, { desc = "Copy file path" })
map("n", "<leader>C", function()
  vim.fn.setreg("+", vim.fn.getcwd())
end, { desc = "Copy cwd" })
map({ "n", "x" }, "<leader>p", '"+p', { desc = "Paste clipboard after" })
map({ "n", "x" }, "<leader>P", '"+P', { desc = "Paste clipboard before" })
map({ "n", "x" }, "<leader>y", '"+y', { desc = "Yank to clipboard" })
map("n", "<leader>Y", '"+Y', { desc = "Yank line to clipboard" })
map("n", "<leader>v", function()
  local path = vim.api.nvim_buf_get_name(0)
  if path == "" then
    path = vim.fn.getcwd()
  else
    path = vim.fn.fnamemodify(path, ":p")
  end
  vim.fn.jobstart({ "chilla", path }, { detach = true })
end, { desc = "Open current file or directory in Chilla" })
map("n", "<leader>R", "<Cmd>QuickRun<CR>", { desc = "Run current file with QuickRun" })

map("n", "gn", vim.diagnostic.goto_next, { desc = "Next diagnostic" })
map("n", "gp", vim.diagnostic.goto_prev, { desc = "Previous diagnostic" })
map("n", "gd", vim.lsp.buf.definition, { desc = "Definition" })
map("n", "gy", vim.lsp.buf.type_definition, { desc = "Type definition" })
map("n", "gr", function()
  require("telescope.builtin").lsp_references()
end, { desc = "References", nowait = true })
map("n", "gi", function()
  require("telescope.builtin").lsp_implementations()
end, { desc = "Implementations" })
map("n", "<C-g>", vim.diagnostic.goto_next)
map("n", "<C-s>", vim.diagnostic.goto_prev)
map("n", "<leader>a", vim.lsp.buf.code_action, { desc = "Code action" })
map("n", "<leader>k", vim.lsp.buf.hover, { desc = "Hover" })
map("n", "<leader>r", vim.lsp.buf.rename, { desc = "Rename" })
map("n", "<leader>\\", "<Cmd>LspRestart<CR>", { desc = "Restart LSP" })
map("x", "kj", "<Esc>", silent)

for _, mode in ipairs({ "n", "x" }) do
  for _, lhs in ipairs({ "gra", "gri", "grn", "grr", "grt", "grx" }) do
    pcall(vim.keymap.del, mode, lhs)
  end
end

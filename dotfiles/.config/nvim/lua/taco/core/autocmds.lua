local group = vim.api.nvim_create_augroup("TacoConfig", { clear = true })

vim.api.nvim_create_autocmd("BufWritePre", {
  group = group,
  pattern = "*",
  callback = function()
    local view = vim.fn.winsaveview()
    vim.cmd([[silent! keeppatterns %s/\s\+$//e]])
    vim.fn.winrestview(view)
  end,
})

vim.api.nvim_create_autocmd("FileType", {
  group = group,
  pattern = "*",
  callback = function()
    vim.opt_local.foldenable = false
  end,
})

vim.api.nvim_create_autocmd("FileType", {
  group = group,
  pattern = "*",
  callback = function(args)
    pcall(vim.treesitter.start, args.buf)
  end,
})

vim.filetype.add({
  extension = { dig = "yaml", vtl = "velocity", zon = "zig", png = "png", jpg = "jpeg", jpeg = "jpeg" },
  filename = { ["nginx.conf"] = "nginx" },
  pattern = {
    ["Dockerfile.*"] = "dockerfile",
    [".*%.mdwn"] = "markdown",
    [".*%.mkd"] = "markdown",
    [".*%.mkdn"] = "markdown",
    [".*%.mark.*"] = "markdown",
  },
})

vim.api.nvim_create_autocmd("FileType", {
  group = group,
  pattern = "yaml",
  callback = function()
    vim.opt_local.indentkeys:remove("<:>")
    vim.opt_local.indentkeys:remove("0#")
  end,
})

vim.api.nvim_create_autocmd("FileType", {
  group = group,
  pattern = "go",
  callback = function()
    vim.fn.matchadd("goErr", [[\<err\>]])
    vim.api.nvim_set_hl(0, "goErr", { bold = true, ctermfg = 214 })
  end,
})

vim.api.nvim_create_autocmd("FileType", {
  group = group,
  pattern = "plantuml",
  callback = function()
    vim.keymap.set("n", ".r", "<Cmd>make<CR>", { buffer = true })
  end,
})

vim.api.nvim_create_autocmd("FileType", {
  group = group,
  pattern = "typescript",
  callback = function()
    vim.keymap.set("i", "<C-Space>", "<C-x><C-o>", { buffer = true })
  end,
})

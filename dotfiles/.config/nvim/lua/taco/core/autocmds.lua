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
  callback = function() vim.opt_local.foldenable = false end,
})

vim.filetype.add({
  extension = { dig = "yaml", vtl = "velocity", zon = "zig" },
  filename = { ["nginx.conf"] = "nginx" },
  pattern = { ["Dockerfile.*"] = "dockerfile" },
})

local path = vim.fn.stdpath("data") .. "/lazy/lazy.nvim"
if not vim.uv.fs_stat(path) then
  local result = vim.fn.system({
    "git", "clone", "--filter=blob:none", "--branch=stable",
    "https://github.com/folke/lazy.nvim.git", path,
  })
  if vim.v.shell_error ~= 0 then
    error("lazy.nvim bootstrap failed:\n" .. result)
  end
end
vim.opt.rtp:prepend(path)

require("lazy").setup({
  { import = "taco.plugins" },
  { import = "taco.plugins.lsp" },
}, {
  change_detection = { notify = false },
  checker = { enabled = true, notify = false },
})

return {
  { "ellisonleao/gruvbox.nvim", priority = 1000, config = function() vim.cmd.colorscheme("gruvbox") end },
  { "tpope/vim-surround" },
  { "tpope/vim-endwise" },
  { "editorconfig/editorconfig-vim" },
  { "vim-test/vim-test" },
  { "thinca/vim-quickrun" },
  { "fatih/vim-go", ft = "go" },
  { "rust-lang/rust.vim", ft = "rust" },
  { "cespare/vim-toml", ft = "toml" },
  { "hashivim/vim-terraform", ft = "terraform" },
  { "pangloss/vim-javascript", ft = { "javascript", "typescript" } },
  { "vim-ruby/vim-ruby", ft = "ruby" },
  { "plasticboy/vim-markdown", ft = "markdown" },
  { "mracos/mermaid.vim", ft = "mermaid" },
  { "lewis6991/gitsigns.nvim", opts = {} },
  { "f-person/git-blame.nvim", opts = { enabled = false } },
  {
    "akinsho/toggleterm.nvim",
    version = "*",
    opts = {},
  },
  {
    "smoka7/hop.nvim",
    version = "*",
    opts = { keys = "fdjhklsagqwertyuiopzxcvbnm" },
    keys = {
      { "gj", function() require("hop").hint_words() end, mode = { "n", "x" }, desc = "Hop anywhere" },
      { "gf", function() require("hop").hint_char1({ current_line_only = true }) end, mode = { "n", "x" }, desc = "Hop on line" },
    },
  },
  {
    "stevearc/conform.nvim",
    event = { "BufWritePre" },
    opts = {
      format_on_save = { timeout_ms = 3000, lsp_format = "never" },
      formatters_by_ft = {
        lua = { "stylua" }, python = { "black" }, go = { "goimports" },
        rust = { "rustfmt" }, zig = { "zigfmt" }, toml = { "taplo" },
        javascript = { "prettier" }, typescript = { "prettier" },
        javascriptreact = { "prettier" }, typescriptreact = { "prettier" },
        svelte = { "prettier" }, css = { "prettier" }, html = { "prettier" },
        json = { "prettier" }, yaml = { "prettier" }, sh = { "shfmt" },
      },
    },
  },
  {
    "folke/which-key.nvim",
    event = "VeryLazy",
    opts = { delay = 200 },
  },
  {
    "nvim-lualine/lualine.nvim",
    dependencies = { "nvim-tree/nvim-web-devicons" },
    opts = {
      options = { theme = "gruvbox", globalstatus = true },
      sections = {
        lualine_a = { "mode" },
        lualine_b = { function() return "cwd " .. vim.fn.fnamemodify(vim.fn.getcwd(), ":~") end },
        lualine_c = { { "filename", path = 0 } },
        lualine_x = { "branch", "diff", "diagnostics" },
        lualine_y = { "filetype", "encoding", "fileformat" },
        lualine_z = { "location" },
      },
    },
  },
  {
    "nvim-treesitter/nvim-treesitter",
    -- The main branch is an incompatible rewrite without nvim-treesitter.configs.
    branch = "master",
    build = ":TSUpdate",
    main = "nvim-treesitter.configs",
    opts = { highlight = { enable = true }, indent = { enable = true } },
  },
  {
    "nvim-telescope/telescope.nvim",
    dependencies = {
      "nvim-lua/plenary.nvim",
      { "nvim-telescope/telescope-fzf-native.nvim", build = "make" },
    },
    config = function()
      local telescope = require("telescope")
      local actions = require("telescope.actions")
      telescope.setup({ defaults = { mappings = { i = {
        ["<Esc>"] = actions.close,
        ["<C-j>"] = actions.move_selection_next,
        ["<C-k>"] = actions.move_selection_previous,
        ["<Tab>"] = actions.toggle_selection + actions.move_selection_next,
      } } } })
      pcall(telescope.load_extension, "fzf")
      local builtin = require("telescope.builtin")
      vim.keymap.set("n", "<leader>f", builtin.git_files, { desc = "Git files" })
      vim.keymap.set("n", "<leader>/", builtin.live_grep, { desc = "Live grep" })
      vim.keymap.set("n", "<leader>b", builtin.buffers, { desc = "Buffers" })
      vim.keymap.set("n", "<leader>h", builtin.oldfiles, { desc = "History" })
      vim.keymap.set("n", "<leader>j", builtin.jumplist, { desc = "Jumplist" })
      vim.keymap.set("n", "<leader>G", builtin.git_branches, { desc = "Git branches" })
    end,
  },
  {
    "kdheepak/lazygit.nvim",
    dependencies = { "nvim-lua/plenary.nvim" },
    cmd = { "LazyGit", "LazyGitCurrentFile" },
    keys = { { "<leader>g", "<Cmd>LazyGit<CR>", desc = "LazyGit" } },
  },
  {
    "mikavilpas/yazi.nvim",
    dependencies = { "nvim-lua/plenary.nvim" },
    opts = { open_for_directories = true, floating_window_scaling_factor = 0.9 },
    keys = { { "<leader>e", "<Cmd>Yazi cwd<CR>", desc = "Yazi" } },
  },
}

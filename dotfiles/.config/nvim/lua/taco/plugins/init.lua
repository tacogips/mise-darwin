local function cwd_statusline()
  local cwd = vim.fn.fnamemodify(vim.fn.getcwd(), ":~")
  if cwd == "" then
    cwd = "."
  end
  local label = "cwd "
  local available = math.max(math.floor(vim.o.columns * 0.28), 24) - vim.fn.strdisplaywidth(label)
  if vim.fn.strdisplaywidth(cwd) > available then
    cwd = vim.fn.pathshorten(cwd)
  end
  if vim.fn.strdisplaywidth(cwd) > available then
    local target = math.max(available - 3, 1)
    while vim.fn.strdisplaywidth(cwd) > target and vim.fn.strchars(cwd) > 1 do
      cwd = vim.fn.strcharpart(cwd, 1)
    end
    cwd = "..." .. cwd
  end
  return label .. cwd
end

return {
  {
    "ellisonleao/gruvbox.nvim",
    priority = 1000,
    config = function()
      vim.cmd.colorscheme("gruvbox")
    end,
  },
  { "tpope/vim-surround" },
  { "tpope/vim-endwise" },
  { "editorconfig/editorconfig-vim" },
  { "vim-test/vim-test" },
  { "thinca/vim-quickrun" },
  { "fatih/vim-go", ft = "go" },
  { "rust-lang/rust.vim", ft = "rust" },
  { "dart-lang/dart-vim-plugin", ft = "dart" },
  { "cespare/vim-toml", ft = "toml" },
  { "hashivim/vim-terraform", ft = "terraform" },
  { "pangloss/vim-javascript", ft = { "javascript", "typescript" } },
  { "vim-ruby/vim-ruby", ft = "ruby" },
  { "plasticboy/vim-markdown", ft = "markdown" },
  { "Glench/Vim-Jinja2-Syntax", ft = "jinja" },
  { "imsnif/kdl.vim", ft = "kdl" },
  { "chr4/nginx.vim", ft = "nginx" },
  { "zah/nim.vim", ft = "nim" },
  { "pest-parser/pest.vim", ft = "pest" },
  { "jparise/vim-graphql", ft = "graphql" },
  { "NoahTheDuke/vim-just", ft = "just" },
  { "tomlion/vim-solidity", ft = "solidity" },
  { "evanleck/vim-svelte", ft = "svelte" },
  { "jbyuki/venn.nvim" },
  { "cocopon/iceberg.vim" },
  { "folke/tokyonight.nvim" },
  { "octol/vim-cpp-enhanced-highlight", ft = { "c", "cpp" } },
  { "tpope/vim-dispatch" },
  { "thosakwe/vim-flutter", ft = "dart" },
  { "w0ng/vim-hybrid" },
  { "nvim-lua/lsp_extensions.nvim" },
  { "mracos/mermaid.vim", ft = "mermaid" },
  { "lewis6991/gitsigns.nvim", opts = {} },
  { "f-person/git-blame.nvim", opts = { enabled = false } },
  { "akinsho/toggleterm.nvim", version = "*", opts = {} },
  {
    "smoka7/hop.nvim",
    version = "*",
    opts = { keys = "fdjhklsagqwertyuiopzxcvbnm" },
    keys = {
      {
        "gj",
        function()
          require("hop").hint_char1()
        end,
        mode = { "n", "x" },
        desc = "Hop anywhere",
      },
      {
        "gf",
        function()
          require("hop").hint_char1({ current_line_only = true })
        end,
        mode = { "n", "x" },
        desc = "Hop on line",
      },
    },
  },
  {
    "stevearc/conform.nvim",
    event = { "BufWritePre" },
    opts = {
      format_on_save = { timeout_ms = 3000, lsp_format = "never" },
      formatters_by_ft = {
        lua = { "stylua" },
        fennel = { "fnlfmt" },
        python = { "black" },
        go = { "goimports" },
        rust = { "rustfmt" },
        zig = { "zigfmt" },
        toml = function(bufnr)
          if vim.fs.basename(vim.api.nvim_buf_get_name(bufnr)) == "Cargo.lock" then
            return {}
          end
          return { "taplo" }
        end,
        javascript = { "prettier" },
        typescript = { "prettier" },
        javascriptreact = { "prettier" },
        typescriptreact = { "prettier" },
        vue = { "prettier" },
        svelte = { "prettier" },
        css = { "prettier" },
        html = { "prettier" },
        graphql = { "prettier" },
        json = { "prettier" },
        yaml = { "prettier" },
        proto = { "buf" },
        c = { "clang_format" },
        solidity = { "forge_fmt" },
        sql = { "sqlfmt" },
        terraform = { "terraform_fmt" },
        nix = { "nixfmt" },
        sh = { "shfmt" },
      },
      formatters = {
        buf = { command = "buf", args = { "format" }, stdin = true },
        forge_fmt = { command = "forge", args = { "fmt", "--raw", "-" }, stdin = true },
        sqlfmt = { command = "sqlfmt", args = { "-" }, stdin = true },
        fnlfmt = { command = "fnlfmt", args = { "-" }, stdin = true },
        nixfmt = { command = "nixfmt", stdin = true },
        rustfmt = { prepend_args = { "--edition", "2021" } },
      },
    },
  },
  {
    "echasnovski/mini.clue",
    event = "VeryLazy",
    config = function()
      local miniclue = require("mini.clue")
      miniclue.setup({
        triggers = {
          { mode = { "n", "x" }, keys = "<Space>" },
          { mode = { "n", "x" }, keys = "g" },
          { mode = "n", keys = "m" },
          { mode = "n", keys = "z" },
        },
        window = { delay = 200, config = { border = "rounded", width = 48 } },
      })
    end,
  },
  {
    "nvim-lualine/lualine.nvim",
    dependencies = { "nvim-tree/nvim-web-devicons" },
    opts = {
      options = {
        theme = "gruvbox",
        globalstatus = true,
        component_separators = { left = "", right = "|" },
        section_separators = { left = "", right = "" },
        always_divide_middle = true,
      },
      sections = {
        lualine_a = { "mode" },
        lualine_b = { cwd_statusline },
        lualine_c = {
          { "filename", path = 0, symbols = { modified = " [+]", readonly = " [ro]", unnamed = "[No Name]" } },
        },
        lualine_x = { "branch", "diff", "diagnostics" },
        lualine_y = { "filetype", "encoding", "fileformat" },
        lualine_z = { "location" },
      },
      inactive_sections = {
        lualine_a = {},
        lualine_b = {},
        lualine_c = {
          cwd_statusline,
          { "filename", path = 0, symbols = { modified = " [+]", readonly = " [ro]", unnamed = "[No Name]" } },
        },
        lualine_x = { "location" },
        lualine_y = {},
        lualine_z = {},
      },
    },
  },
  {
    "nvim-treesitter/nvim-treesitter",
    branch = "main",
    lazy = false,
    build = ":TSUpdate",
  },
  {
    "nvim-telescope/telescope.nvim",
    dependencies = {
      "nvim-lua/plenary.nvim",
      { "nvim-telescope/telescope-fzf-native.nvim", build = "make" },
      "nvim-telescope/telescope-symbols.nvim",
      { "danielfalk/smart-open.nvim", dependencies = { "kkharji/sqlite.lua" } },
    },
    config = function()
      local telescope = require("telescope")
      local actions = require("telescope.actions")
      local builtin = require("telescope.builtin")
      local function system_lines(command, cwd)
        local result = vim.system(command, { cwd = cwd, text = true }):wait()
        return result.code, vim.split(result.stdout or "", "\n", { trimempty = true })
      end
      local function repo_grep_targets()
        local cwd = vim.fn.getcwd()
        local status, roots = system_lines({ "git", "rev-parse", "--show-toplevel" }, cwd)
        if status ~= 0 or #roots == 0 then
          return cwd, nil
        end
        local root = roots[1]
        local files_status, files = system_lines({ "git", "ls-files" }, root)
        if files_status ~= 0 or #files == 0 then
          return root, nil
        end
        return root, files
      end
      local type_symbols = {
        "File",
        "Module",
        "Namespace",
        "Package",
        "Class",
        "Field",
        "Constructor",
        "Enum",
        "Interface",
        "String",
        "Number",
        "Boolean",
        "Array",
        "Object",
        "Key",
        "Null",
        "EnumMember",
        "Struct",
        "Event",
        "Operator",
        "TypeParameter",
      }
      telescope.setup({
        defaults = {
          prompt_prefix = " ❯ ",
          sorting_strategy = "descending",
          layout_config = { prompt_position = "bottom" },
          mappings = {
            i = {
              ["<Esc>"] = actions.close,
              ["<C-j>"] = actions.move_selection_next,
              ["<C-k>"] = actions.move_selection_previous,
              ["<Tab>"] = actions.toggle_selection + actions.move_selection_next,
              ["<C-s>"] = actions.send_selected_to_qflist,
              ["<C-q>"] = actions.send_to_qflist,
            },
          },
        },
        extensions = {
          fzf = { fuzzy = true, override_generic_sorter = true, override_file_sorter = true, case_mode = "smart_case" },
          smart_open = { match_algorithm = "fzf" },
        },
      })
      pcall(telescope.load_extension, "fzf")
      pcall(telescope.load_extension, "smart_open")
      vim.keymap.set("n", "<leader>f", builtin.git_files, { desc = "Git files" })
      vim.keymap.set("n", "<leader>/", function()
        local cwd, search_dirs = repo_grep_targets()
        builtin.live_grep({ cwd = cwd, search_dirs = search_dirs })
      end, { desc = "Repo-aware grep" })
      vim.keymap.set("n", "<leader>b", builtin.buffers, { desc = "Buffers" })
      vim.keymap.set("n", "<leader>h", builtin.oldfiles, { desc = "History" })
      vim.keymap.set("n", "<leader>j", builtin.jumplist, { desc = "Jumplist" })
      vim.keymap.set("n", "<leader>G", builtin.git_branches, { desc = "Git branches" })
      vim.keymap.set("n", "<leader>,", function()
        telescope.extensions.smart_open.smart_open()
      end, { desc = "Smart files" })
      vim.keymap.set("n", "<leader>m", builtin.marks, { desc = "Marks" })
      vim.keymap.set("n", "<leader>H", builtin.command_history, { desc = "Command history" })
      vim.keymap.set("n", "<leader>?", builtin.keymaps, { desc = "Keymaps" })
      vim.keymap.set("n", "<leader>s", function()
        builtin.lsp_workspace_symbols({ query = "", symbols = type_symbols })
      end, { desc = "Workspace type symbols" })
      vim.keymap.set("n", "<leader>S", function()
        builtin.lsp_workspace_symbols({ query = "", ignore_symbols = type_symbols })
      end, { desc = "Workspace non-type symbols" })
      vim.keymap.set("n", "<leader>W", function()
        builtin.lsp_workspace_symbols({ query = "" })
      end, { desc = "Workspace symbols" })
      vim.keymap.set("n", "<leader>t", builtin.lsp_document_symbols, { desc = "Document symbols" })
      vim.keymap.set("n", "<leader>d", function()
        builtin.diagnostics({ bufnr = 0 })
      end, { desc = "Document diagnostics" })
      vim.keymap.set("n", "<leader>D", builtin.diagnostics, { desc = "Workspace diagnostics" })
    end,
  },
  {
    "kdheepak/lazygit.nvim",
    dependencies = { "nvim-lua/plenary.nvim" },
    cmd = { "LazyGit", "LazyGitConfig", "LazyGitCurrentFile", "LazyGitFilter", "LazyGitFilterCurrentFile" },
    keys = { { "<leader>g", "<Cmd>LazyGit<CR>", desc = "LazyGit" } },
  },
  {
    "mikavilpas/yazi.nvim",
    dependencies = { "nvim-lua/plenary.nvim" },
    opts = {
      open_for_directories = true,
      floating_window_scaling_factor = 0.9,
      yazi_floating_window_border = "rounded",
      yazi_floating_window_winblend = 0,
    },
    keys = { { "<leader>e", "<Cmd>Yazi cwd<CR>", desc = "Yazi" } },
  },
  {
    "nvimtools/none-ls.nvim",
    dependencies = { "nvim-lua/plenary.nvim" },
    opts = function()
      local null_ls = require("null-ls")
      return { sources = { null_ls.builtins.formatting.stylua, null_ls.builtins.completion.spell } }
    end,
  },
}

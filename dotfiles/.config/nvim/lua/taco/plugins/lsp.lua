return {
  {
    "neovim/nvim-lspconfig",
    dependencies = {
      "hrsh7th/cmp-nvim-lsp",
      { "j-hui/fidget.nvim", opts = {} },
    },
    config = function()
      local capabilities = require("cmp_nvim_lsp").default_capabilities()
      local on_attach = function(client)
        client.server_capabilities.documentFormattingProvider = false
        client.server_capabilities.documentRangeFormattingProvider = false
      end

      vim.lsp.config("*", {
        root_markers = { ".git" },
        capabilities = capabilities,
        on_attach = on_attach,
      })

      local servers = {
        ccls = {},
        gopls = {},
        jdtls = {},
        julials = {},
        nil_ls = {},
        move_analyzer = { cmd = { "move-analyzer" }, filetypes = { "move" }, root_markers = { ".git", "Move.toml" } },
        basedpyright = {},
        sourcekit = { root_markers = { "Package.swift", ".git" } },
        denols = { root_markers = { "deno.json" } },
        solidity_ls_nomicfoundation = {},
        svelte = {},
        ts_ls = { root_markers = { "package.json" } },
        zls = {
          cmd = { "zls", "--config-path", vim.fn.expand("~/.config/zls/zls.json") },
          filetypes = { "zig", "zon" },
          root_markers = { "build.zig", "zls.json", ".git" },
        },
        lua_ls = {
          settings = {
            Lua = {
              runtime = { version = "LuaJIT" },
              diagnostics = { globals = { "vim" } },
              workspace = { library = vim.api.nvim_get_runtime_file("", true) },
              telemetry = { enable = false },
            },
          },
        },
        rust_analyzer = {
          settings = {
            ["rust-analyzer"] = {
              procMacro = { enable = true },
              cargo = { targetDir = "target/rust-analyzer" },
              check = { command = "check", extraArgs = { "--target-dir", "target/ra" } },
              workspace = { symbol = { search = { kind = "all_symbols", limit = 4096 } } },
            },
          },
        },
      }

      for name, config in pairs(servers) do
        vim.lsp.config(name, config)
        vim.lsp.enable(name)
      end
    end,
  },
  {
    "hrsh7th/nvim-cmp",
    event = "InsertEnter",
    dependencies = {
      "hrsh7th/cmp-buffer",
      "hrsh7th/cmp-path",
      "hrsh7th/cmp-cmdline",
      "L3MON4D3/LuaSnip",
      "saadparwaiz1/cmp_luasnip",
    },
    config = function()
      local cmp = require("cmp")
      require("luasnip.loaders.from_snipmate").load()
      cmp.setup({
        snippet = {
          expand = function(args)
            require("luasnip").lsp_expand(args.body)
          end,
        },
        mapping = cmp.mapping.preset.insert({
          ["<CR>"] = cmp.mapping.confirm({ select = true }),
        }),
        sources = cmp.config.sources({ { name = "luasnip" }, { name = "path" } }, { { name = "buffer" } }),
      })
      cmp.setup.cmdline("/", { mapping = cmp.mapping.preset.cmdline(), sources = { { name = "buffer" } } })
      cmp.setup.cmdline(":", {
        mapping = cmp.mapping.preset.cmdline(),
        sources = cmp.config.sources({ { name = "path" }, { name = "cmdline" } }, { { name = "buffer" } }),
      })

      _G.vimrc = _G.vimrc or {}
      _G.vimrc.cmp = _G.vimrc.cmp or {}
      _G.vimrc.cmp.lsp = function()
        cmp.complete({
          config = {
            sources = {
              { name = "nvim_lsp" },
              { name = "luasnip" },
              { name = "buffer" },
              { name = "path" },
            },
          },
        })
      end
    end,
  },
}

return {
  {
    "neovim/nvim-lspconfig",
    dependencies = {
      "hrsh7th/cmp-nvim-lsp",
      { "j-hui/fidget.nvim", opts = {} },
    },
    config = function()
      local capabilities = require("cmp_nvim_lsp").default_capabilities()
      local on_attach = function(client, bufnr)
        client.server_capabilities.documentFormattingProvider = false
        client.server_capabilities.documentRangeFormattingProvider = false
        local function bmap(lhs, rhs, desc)
          vim.keymap.set("n", lhs, rhs, { buffer = bufnr, desc = desc })
        end
        bmap("gd", vim.lsp.buf.definition, "Definition")
        bmap("gy", vim.lsp.buf.type_definition, "Type definition")
        bmap("gr", require("telescope.builtin").lsp_references, "References")
        bmap("gi", require("telescope.builtin").lsp_implementations, "Implementations")
        bmap("<leader>a", vim.lsp.buf.code_action, "Code action")
        bmap("<leader>k", vim.lsp.buf.hover, "Hover")
        bmap("<leader>r", vim.lsp.buf.rename, "Rename")
        bmap("<leader>d", require("telescope.builtin").diagnostics, "Diagnostics")
      end

      local servers = {
        ccls = {}, gopls = {}, jdtls = {}, julials = {}, nil_ls = {},
        basedpyright = {}, sourcekit = {}, denols = {}, solidity_ls_nomicfoundation = {},
        svelte = {}, ts_ls = {}, zls = { cmd = { "zls", "--config-path", vim.fn.expand("~/.config/zls/zls.json") } },
        lua_ls = { settings = { Lua = {
          runtime = { version = "LuaJIT" },
          diagnostics = { globals = { "vim" } },
          workspace = { library = vim.api.nvim_get_runtime_file("", true) },
          telemetry = { enable = false },
        } } },
        rust_analyzer = { settings = { ["rust-analyzer"] = {
          procMacro = { enable = true },
          cargo = { targetDir = "target/rust-analyzer" },
          check = { command = "check", extraArgs = { "--target-dir", "target/ra" } },
        } } },
      }

      for name, config in pairs(servers) do
        config.capabilities = capabilities
        config.on_attach = on_attach
        vim.lsp.config(name, config)
        vim.lsp.enable(name)
      end
    end,
  },
  {
    "hrsh7th/nvim-cmp",
    event = "InsertEnter",
    dependencies = {
      "hrsh7th/cmp-buffer", "hrsh7th/cmp-path", "hrsh7th/cmp-cmdline",
      "L3MON4D3/LuaSnip", "saadparwaiz1/cmp_luasnip",
    },
    config = function()
      local cmp = require("cmp")
      cmp.setup({
        snippet = { expand = function(args) require("luasnip").lsp_expand(args.body) end },
        mapping = cmp.mapping.preset.insert({
          ["<CR>"] = cmp.mapping.confirm({ select = true }),
          ["<C-Space>"] = cmp.mapping.complete(),
        }),
        sources = cmp.config.sources({ { name = "nvim_lsp" }, { name = "luasnip" }, { name = "path" } }, { { name = "buffer" } }),
      })
      cmp.setup.cmdline("/", { mapping = cmp.mapping.preset.cmdline(), sources = { { name = "buffer" } } })
      cmp.setup.cmdline(":", { mapping = cmp.mapping.preset.cmdline(), sources = cmp.config.sources({ { name = "path" } }, { { name = "cmdline" } }) })
    end,
  },
}

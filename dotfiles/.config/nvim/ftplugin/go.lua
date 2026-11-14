local map = function(lhs, rhs, desc) vim.keymap.set("n", lhs, rhs, { buffer = true, desc = desc }) end
map(".r", "<Cmd>GoRun<CR>", "Go run")
map(".b", "<Cmd>GoBuild<CR>", "Go build")
map(".t", "<Cmd>GoTest<CR>", "Go test")
map(".l", "<Cmd>GoLint<CR>", "Go lint")
map(".v", "<Cmd>GoVet<CR>", "Go vet")

local map = function(lhs, rhs, desc) vim.keymap.set("n", lhs, rhs, { buffer = true, desc = desc }) end
map(".f", "<Cmd>!cargo fix<CR>", "Cargo fix")
map(".r", "<Cmd>!cargo run<CR>", "Cargo run")
map(".b", "<Cmd>!cargo check<CR>", "Cargo check")
map(".l", "<Cmd>!cargo clippy<CR>", "Cargo clippy")
map(".t", "<Cmd>!cargo nextest run<CR>", "Cargo test")

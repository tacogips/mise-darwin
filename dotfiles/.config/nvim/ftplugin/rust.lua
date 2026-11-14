local map = function(lhs, rhs, desc)
  vim.keymap.set("n", lhs, rhs, { buffer = true, desc = desc })
end
map(".f", "<Cmd>Cargo fix<CR>", "Cargo fix")
map(".r", "<Cmd>Cargo run<CR>", "Cargo run")
map(".b", "<Cmd>Cargo check<CR>", "Cargo check")
map(".l", "<Cmd>Cargo clippy<CR>", "Cargo clippy")
map(".t", "<Cmd>Cargo nextest run<CR>", "Cargo test")

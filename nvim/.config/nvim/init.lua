-- bootstrap lazy.nvim, LazyVim and your plugins
require("config.lazy")
vim.cmd("colorscheme OliveTangerine")

vim.api.nvim_create_autocmd({ "BufEnter" }, {
  pattern = { "*.md", "*.markdown" },
  callback = function()
    vim.opt.spell = true
    vim.opt.spelllang = "it_it,en_us"
  end,
})

-- Disabilita il controllo ortografico per altri tipi di file
vim.api.nvim_create_autocmd({ "BufLeave" }, {
  pattern = { "*.md", "*.markdown" },
  callback = function()
    vim.opt.spell = false
    vim.opt.spelllang = ""
  end,
})

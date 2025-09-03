-- OliveTangerine.lua
-- Main colorscheme file

-- Prevent unnecessary reloads
if vim.g.colors_name then
  vim.cmd("hi clear")
end

vim.g.colors_name = "OliveTangerine"

-- Load the highlight group definitions
local highlights = require("olive-tangerine.highlights")

-- Apply the highlights
for group, settings in pairs(highlights) do
  vim.api.nvim_set_hl(0, group, settings)
end

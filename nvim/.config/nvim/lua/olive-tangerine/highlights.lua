-- Load the palette we just defined
local p = require("olive-tangerine.palette")

-- Define the highlight groups with the corrected syntax
local highlights = {
  -- Base UI
  Normal = { fg = p.cream, bg = p.darker_olive },
  LineNr = { fg = p.slate_grey, bg = p.darker_olive },
  CursorLineNr = { fg = p.tangerine, bold = true }, -- CORRECTED
  SignColumn = { bg = p.darker_olive },
  Visual = { bg = "#556B2F" },

  -- Syntax
  Comment = { fg = p.slate_grey, italic = true }, -- CORRECTED
  Keyword = { fg = p.tangerine, bold = true }, -- CORRECTED
  Function = { fg = p.tangerine },
  String = { fg = p.muted_tangerine },
  Number = { fg = p.muted_tangerine },
  Constant = { fg = p.tangerine },
  Title = { fg = p.tangerine, bold = true }, -- CORRECTED

  -- Types and Identifiers
  Type = { fg = p.light_blue },
  Identifier = { fg = p.cream },

  -- Diagnostics (for LSP)
  DiagnosticError = { fg = p.alert_red },
  DiagnosticWarn = { fg = p.muted_tangerine },
  DiagnosticInfo = { fg = p.light_blue },
  DiagnosticHint = { fg = p.slate_grey },

  -- Git Diffs
  DiffAdd = { bg = "#394A22" },
  DiffChange = { bg = "#2E4C68" },
  DiffDelete = { bg = "#662B2B" },
}

return highlights

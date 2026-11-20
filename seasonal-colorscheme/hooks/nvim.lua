local root = vim.fn.expand("~/.config/colorscheme/current")
local function apply()
  local chunk, err = loadfile(root .. "/nvim.lua")
  if not chunk then
    vim.notify("Seasonal theme: " .. tostring(err), vim.log.levels.WARN)
    return
  end
  local ok, failure = pcall(chunk)
  if not ok then
    vim.notify("Seasonal theme: " .. tostring(failure), vim.log.levels.WARN)
  end
end
local group = vim.api.nvim_create_augroup("SeasonalColorscheme", {clear=true})
vim.api.nvim_create_autocmd({"VimEnter", "ColorScheme"}, {
  group=group, callback=function() vim.schedule(apply) end,
})
vim.api.nvim_create_autocmd("User", {
  group=group, pattern="SeasonalColorscheme", callback=apply,
})
local runtime = vim.env.XDG_RUNTIME_DIR
if runtime then
  local directory = runtime .. "/colorscheme"
  vim.fn.mkdir(directory, "p", 448)
  local socket = directory .. "/nvim-" .. vim.fn.getpid() .. ".sock"
  local ok = pcall(vim.fn.serverstart, socket)
  if ok then
    vim.api.nvim_create_autocmd("VimLeavePre", {
      group=group, callback=function()
        pcall(vim.fn.serverstop, socket)
        vim.fn.delete(socket)
      end,
    })
  end
end

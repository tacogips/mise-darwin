--- @sync entry
local function entry()
  local hovered = cx.active.current.hovered

  if hovered and hovered.cha.is_dir then
    ya.emit("cd", { hovered.url })
    ya.emit("quit", {})
    return
  end

  ya.emit("open", { hovered = true })
end

return { entry = entry }

--- @sync get_cwd
local get_cwd = ya.sync(function()
  return cx.active.current.cwd
end)

local function notify(level, content)
  ya.notify({ title = "Git Diff Tree", content = content, timeout = 5, level = level })
end

local function add_entry(entries, url)
  local cha = fs.cha(url, true)
  if cha then
    entries[tostring(url)] = File({ url = url, cha = cha })
  end
end

local function add_parent_dirs(entries, cwd, relative_path)
  local parts = {}
  for part in relative_path:gmatch("[^/]+") do
    parts[#parts + 1] = part
  end
  for i = 1, #parts - 1 do
    add_entry(entries, cwd:join(table.concat(parts, "/", 1, i)))
  end
end

local function sorted_entries(entries)
  local items = {}
  for _, file in pairs(entries) do
    items[#items + 1] = file
  end
  table.sort(items, function(a, b)
    local a_dir = a.cha.is_dir and 0 or 1
    local b_dir = b.cha.is_dir and 0 or 1
    if a_dir ~= b_dir then
      return a_dir < b_dir
    end
    return tostring(a.url) < tostring(b.url)
  end)
  return items
end

local function entry()
  local cwd = get_cwd()
  local output, err = Command("git")
    :cwd(tostring(cwd))
    :arg({ "diff", "--name-only", "HEAD" })
    :output()

  if err then
    return notify("error", "Failed to run `git diff`: " .. err)
  elseif not output.status.success then
    return notify("error", "Failed to run `git diff`: " .. output.stderr)
  end

  local entries = {}
  for line in output.stdout:gmatch("[^\r\n]+") do
    add_parent_dirs(entries, cwd, line)
    add_entry(entries, cwd:join(line))
  end

  local files = sorted_entries(entries)
  if #files == 0 then
    return notify("info", "No files or directories match `git diff`")
  end

  local id = ya.id("ft")
  local search_cwd = cwd:into_search("Git diff tree")
  ya.emit("cd", { Url(search_cwd) })
  ya.emit("update_files", { op = fs.op("part", { id = id, url = Url(search_cwd), files = {} }) })
  ya.emit("update_files", { op = fs.op("part", { id = id, url = Url(search_cwd), files = files }) })
  ya.emit("update_files", {
    op = fs.op("done", { id = id, url = search_cwd, cha = Cha({ mode = tonumber("100644", 8) }) }),
  })
end

return { entry = entry }

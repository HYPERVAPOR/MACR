-- Pandoc Lua filter to support Markdown includes.
-- Usage in paper.md:
--   as fenced code block:
--     ```
--     include: sections/introduction.md
--     ```
--   or as raw markdown block:
--     ```{=markdown}
--     include: sections/introduction.md
--     ```

local function process_include(text)
  if text:match("^include:%s*") then
    local path = text:gsub("^include:%s*", ""):gsub("%s*$", "")
    local file = io.open(path, "r")
    if not file then
      io.stderr:write("Warning: could not open include file: " .. path .. "\n")
      return {}
    end
    local content = file:read("*a")
    file:close()
    return pandoc.read(content, "markdown").blocks
  end
  return nil
end

function CodeBlock(el)
  return process_include(el.text)
end

function RawBlock(el)
  if el.format:match("^markdown") then
    return process_include(el.text)
  end
end

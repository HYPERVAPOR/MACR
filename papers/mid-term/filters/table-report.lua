-- Convert pandoc Table elements to a standard LaTeX table float
-- using tabular instead of longtable. This variant uses table (not table*)
-- for single-column documents such as the Chinese mid-term report.

local function escape_latex(s)
  local escapes = {
    ["\\"] = "\\textbackslash{}",
    ["{"] = "\\{",
    ["}"] = "\\}",
    ["$"] = "\\$",
    ["&"] = "\\&",
    ["#"] = "\\#",
    ["_"] = "\\_",
    ["%"] = "\\%",
    ["~"] = "\\textasciitilde{}",
    ["^"] = "\\textasciicircum{}",
  }
  -- Backslash must be escaped first; the rest can be done via gsub.
  return (s:gsub("(.)", function(c) return escapes[c] or c end))
end

local function stringify_cells(cells)
  local parts = {}
  for _, cell in ipairs(cells) do
    local text = pandoc.utils.stringify(cell.contents)
    table.insert(parts, escape_latex(text))
  end
  return parts
end

local function render_row(row)
  local cells = stringify_cells(row.cells)
  return table.concat(cells, " & ") .. " \\\\"
end

-- Extract an explicit identifier of the form {#some-id} from a caption string.
local function extract_label(caption)
  local label = ""
  local cleaned = caption:gsub("%s*\\?\r?\n%s*", " ")
  cleaned = cleaned:gsub("()%s*%{#([^%{%}]+)%}%s*$", function(pos, id)
    label = "\\label{" .. id .. "}"
    return ""
  end)
  return cleaned, label
end

function Table(el)
  local raw_caption = ""
  if el.caption and el.caption.long then
    raw_caption = pandoc.utils.stringify(el.caption.long)
  end
  local caption, label_from_attr = extract_label(raw_caption)
  -- Also honour any native pandoc identifier if present.
  local native_label = (el.identifier and el.identifier ~= "") and "\\label{" .. el.identifier .. "}" or ""
  local label = native_label ~= "" and native_label or label_from_attr

  -- Build column specification from alignments
  local aligns = { Left = "l", Right = "r", Center = "c", Default = "l" }
  local col_spec = {}
  for _, col in ipairs(el.colspecs) do
    local align = col[1] or "Default"
    table.insert(col_spec, aligns[align] or "l")
  end
  local cols = table.concat(col_spec)

  -- Build rows
  local rows = {}

  -- Header rows from el.head
  if el.head and el.head.rows then
    for _, row in ipairs(el.head.rows) do
      table.insert(rows, render_row(row))
    end
    if #el.head.rows > 0 then
      table.insert(rows, "\\hline")
    end
  end

  -- Body rows
  if el.bodies then
    for _, body in ipairs(el.bodies) do
      if body.body then
        for _, row in ipairs(body.body) do
          table.insert(rows, render_row(row))
        end
      end
    end
  end

  -- Wrap in table float (single-column friendly)
  local latex = "\\begin{table}[htbp]\n\\centering\n"
  if caption ~= "" then
    latex = latex .. "\\caption{" .. escape_latex(caption) .. "}" .. label .. "\n"
  end
  latex = latex .. "\\begin{tabular}{" .. cols .. "}\n"
  latex = latex .. "\\hline\n"
  latex = latex .. table.concat(rows, "\n") .. "\n"
  latex = latex .. "\\hline\n"
  latex = latex .. "\\end{tabular}\n"
  latex = latex .. "\\end{table}"

  return pandoc.RawBlock("latex", latex)
end

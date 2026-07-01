-- Convert pandoc Table elements to a standard LaTeX table/table* float
-- using tabular instead of longtable. This is required for two-column
-- conference templates such as IEEEtran where longtable is unsupported.

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

function Table(el)
  local raw_caption = ""
  if el.caption and el.caption.long then
    raw_caption = pandoc.utils.stringify(el.caption.long)
  end
  -- Strip any trailing markdown attribute such as {#tbl:main-results}
  local caption = raw_caption:gsub("%s*%{#.-}%s*$", "") or raw_caption
  local label = (el.identifier and el.identifier ~= "") and "\\label{" .. el.identifier .. "}" or ""

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

  -- Wrap in table* float (spans both columns in two-column mode)
  local latex = "\\begin{table*}[htbp]\n\\centering\n"
  if caption ~= "" then
    latex = latex .. "\\caption{" .. escape_latex(caption) .. "}" .. label .. "\n"
  end
  latex = latex .. "\\begin{tabular}{" .. cols .. "}\n"
  latex = latex .. "\\hline\n"
  latex = latex .. table.concat(rows, "\n") .. "\n"
  latex = latex .. "\\hline\n"
  latex = latex .. "\\end{tabular}\n"
  latex = latex .. "\\end{table*}"

  return pandoc.RawBlock("latex", latex)
end

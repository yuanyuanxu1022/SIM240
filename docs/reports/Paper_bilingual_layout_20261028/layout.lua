-- Presentation-only adaptations. Scientific Markdown remains unchanged.
local function quote(s) return '"' .. s:gsub('\\','\\\\'):gsub('"','\\"') .. '"' end
local function fragment(blocks)
  return pandoc.write(pandoc.Pandoc(blocks),'typst'):gsub('%s+$','')
end
function Math(el)
  local tag=el.text:match('\\tag{([^}]+)}')
  local s=el.text:gsub('\\tag{[^}]+}',''):gsub('\\rm%s+([%w]+)','\\mathrm{%1}')
  if el.mathtype=='DisplayMath' and s:find('\\qquad') then
    s='\\begin{gathered}'..s:gsub('\\qquad','\\\\')..'\\end{gathered}'
  end
  local content=fragment({pandoc.Para({pandoc.Math(el.mathtype,s)})})
  if el.mathtype=='DisplayMath' then
    local inner=content:match('^%$%s*([%s%S]-)%s*%$$')
    if not inner then error('Math conversion failed: '..s) end
    local numbering=tag and ('(..n) => '..quote('('..tag..')')) or 'none'
    return pandoc.RawInline('typst','#block(width: 100%)[#text(size: 9.6pt)[#math.equation(block: true, numbering: '..numbering..')[$ '..inner..' $]]]')
  end
  return pandoc.RawInline('typst',content)
end
function Blocks(blocks)
  local out=pandoc.List(); local i=1
  while i<=#blocks do
    local b=blocks[i]
    if b.t=='Para' and #b.content==1 and b.content[1].t=='Image' then
      local img=b.content[1]; local name=img.src:match('([^/]+)%.png$')
      if name then
        local path='/figures/paper/'..name..'.svg'
        local cap=blocks[i+1]
        local text=cap and fragment({cap}) or ''
        out:insert(pandoc.RawBlock('typst','#block(breakable: false, above: 12pt, below: 12pt)[\n#align(center)[#image('..quote(path)..', width: 100%)]\n#v(3pt)\n#text(size: 9pt)['..text..']\n]'))
        i=i+2
      else out:insert(b);i=i+1 end
    elseif b.t=='Para' and #b.content>0 and b.content[1].t=='Strong' and (pandoc.utils.stringify(b.content[1]):match('^表') or pandoc.utils.stringify(b.content[1]):match('^Table ')) then
      out:insert(pandoc.RawBlock('typst','#block(sticky: true, above: 5pt, below: 3pt)['..fragment({b})..']'));i=i+1
    else out:insert(b);i=i+1 end
  end
  return out
end

function Header(el)
  local title=pandoc.utils.stringify(el)
  if title:match("^附录 E") or title:match("^Appendix E") or title=="References" or title=="参考文献" then
    local style=(title=="References" or title=="参考文献") and "#set text(size: 10.5pt)\n#set par(leading: 0.6em, spacing: 0.75em)" or "#set text(size: 9.6pt)\n#set par(leading: 0.4em, spacing: 0.5em)"
    return {pandoc.RawBlock("typst","#pagebreak(weak: true)\n"..style),el}
  end
end

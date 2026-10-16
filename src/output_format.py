"""Render plain model text and pipe tables without allowing model-supplied HTML."""
import re
from markupsafe import Markup, escape


def render_output(value):
    lines = str(value).splitlines()
    output = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if '|' in line and i + 1 < len(lines) and re.fullmatch(r'[\s|:\-]+', lines[i+1]) and '-' in lines[i+1]:
            cells = lambda text: [str(escape(x.strip())) for x in text.strip().strip('|').split('|')]
            head = cells(line)
            output.append('<div class="table-scroll"><table><thead><tr>' + ''.join('<th scope="col">'+c+'</th>' for c in head) + '</tr></thead><tbody>')
            i += 2
            while i < len(lines) and '|' in lines[i]:
                row = cells(lines[i])
                output.append('<tr>'+''.join('<td>'+c+'</td>' for c in row)+'</tr>')
                i += 1
            output.append('</tbody></table></div>')
            continue
        if line:
            if line.startswith('#'):
                output.append('<h3>'+str(escape(line.lstrip('# ')))+'</h3>')
            else:
                output.append('<p>'+str(escape(line))+'</p>')
        i += 1
    return Markup(''.join(output))

from pathlib import Path
import re

path = Path('app.py')
text = path.read_text(encoding='utf-8')
text = re.sub(r'^tabs = st\.tabs\(\[.*?\]\)\n', '', text, flags=re.MULTILINE | re.DOTALL)
lines = text.splitlines()
out = []
skip_stack = []
for line in lines:
    m = re.match(r'^( *)(with tabs\[\d+\]:.*)$', line)
    if m:
        base_indent = len(m.group(1))
        skip_stack.append(base_indent)
        continue
    if skip_stack:
        if line.strip() == '' or (len(line) > skip_stack[-1] and line.startswith(' ' * (skip_stack[-1] + 4))):
            out.append(line[4:])
            continue
        else:
            skip_stack.pop()
    out.append(line)

text2 = '\n'.join(out)
path.write_text(text2, encoding='utf-8')
print('Updated app.py to remove tab wrappers and enable scroll layout')

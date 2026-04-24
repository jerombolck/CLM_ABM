#!/usr/bin/env python3
# Usage:
#   python replace_nlogox_code.py <model_name>.nlogox <code_file>.nls <output_model>.nlogox
# written with help from duck.ai, model: GPT-5 mini

import sys
import re
from pathlib import Path

if len(sys.argv) != 4:
    print("Usage: python replace_code_in_nlogox.py <input.nlogox> <code.nls> <output.nlogox>")
    sys.exit(2)

in_path = Path(sys.argv[1])
code_path = Path(sys.argv[2])
out_path = Path(sys.argv[3])

if not in_path.exists():
    print(f"Error: input file not found: {in_path}")
    sys.exit(1)
if not code_path.exists():
    print(f"Error: code file not found: {code_path}")
    sys.exit(1)

xml = in_path.read_text(encoding="utf-8")
code = code_path.read_text(encoding="utf-8")

# Normalize line endings in replacement code to Unix style (NetLogo tolerates this)
code = code.replace("\r\n", "\n").replace("\r", "\n")

# Pattern to find the first <code><![CDATA[ ... ]]></code> block (dotall to allow newlines)
pattern = re.compile(r"(<code>\s*<!\[CDATA\[)(.*?)(\]\]>\s*</code>)", re.DOTALL)

m = pattern.search(xml)
if not m:
    print("Error: <code><![CDATA[ ... ]]></code> block not found in input file.")
    sys.exit(3)

prefix, old_code, suffix = m.groups()

# Ensure the code does not contain the CDATA end sequence "]]>"
if "]]>" in code:
    # Safest approach: break the CDATA by replacing occurrences with "]]>]]<![CDATA["
    code = code.replace("]]>", "]]>]]<![CDATA[")

new_block = prefix + code + suffix
new_xml = xml[:m.start()] + new_block + xml[m.end():]

out_path.write_text(new_xml, encoding="utf-8")
print(f"Wrote {out_path} (replaced code block from {code_path})")

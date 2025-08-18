import re
import json

# Regex patterns
section_re = re.compile(r"\\section\{(.+?)\}")
subsection_re = re.compile(r"\\subsection\{(.+?)\}")
subsubsection_re = re.compile(r"\\subsubsection\{(.+?)\}")
label_re = re.compile(r"\\label\{(.+?)\}")
begin_enum = re.compile(r"\\begin\{enumerate\}")
end_enum = re.compile(r"\\end\{enumerate\}")
item_re = re.compile(r"\\item\s*(.*)")


def parse_latex(lines):
    root = []
    stack = []
    current = root
    i = 0

    tableofcontentsToggle = False
    newpageToggle = False
    
    while i < len(lines):
        line = lines[i].strip()

        if line == "\\tableofcontents":
            tableofcontentsToggle = True
            i += 1
            continue
        elif line == "\\newpage" and tableofcontentsToggle:
            newpageToggle = True
            i += 1
            continue
        if not tableofcontentsToggle and not newpageToggle:
            i += 1
            continue
        if not line:
            i += 1
            continue

        print(f"Processing line: {line}")

        # --- Sections ---
        m = section_re.match(line)
        if m:
            title = m.group(1)
            # Peek at next line for label
            label_line = lines[i + 1].strip() if i + 1 < len(lines) else ""
            label_match = label_re.match(label_line)
            label = label_match.group(1) if label_match else None
            node = {"type": "section", "title": title, "label": label, "children": []}
            root.append(node)
            stack = [node]
            current = node["children"]
            i += 2 if label else 1
            continue

        m = subsection_re.match(line)
        if m:
            title = m.group(1)
            label_line = lines[i + 1].strip() if i + 1 < len(lines) else ""
            label_match = label_re.match(label_line)
            label = label_match.group(1) if label_match else None
            node = {
                "type": "subsection",
                "title": title,
                "label": label,
                "children": [],
            }
            # pop stack to section level
            while stack and stack[-1]["type"] not in ["section"]:
                stack.pop()
            stack[-1]["children"].append(node)
            stack.append(node)
            current = node["children"]
            i += 2 if label else 1
            continue

        m = subsubsection_re.match(line)
        if m:
            title = m.group(1)
            label_line = lines[i + 1].strip() if i + 1 < len(lines) else ""
            label_match = label_re.match(label_line)
            label = label_match.group(1) if label_match else None
            node = {
                "type": "subsubsection",
                "title": title,
                "label": label,
                "children": [],
            }
            while stack and stack[-1]["type"] not in ["subsection", "section"]:
                stack.pop()
            stack[-1]["children"].append(node)
            stack.append(node)
            current = node["children"]
            i += 2 if label else 1
            continue

        # --- Enumerate ---
        if begin_enum.match(line):
            node = {"type": "enumerate", "items": []}
            current.append(node)
            stack.append(node)
            current = node["items"]
            i += 1
            continue

        if end_enum.match(line):
            stack.pop()
            if stack:
                parent = stack[-1]
                current = parent.get("children", parent.get("items", root))
            else:
                current = root
            i += 1
            continue

        # --- Items ---
        m = item_re.match(line)
        if m:
            text = m.group(1).strip()
            item_node = {"text": text, "children": []}
            # current.append(item_node)
            # current = item_node["children"]  # for potential nested lists
            i += 1
            continue

        # --- Other text ---
        # You can optionally append plain text nodes if needed
        if line:
            current.append({"type": "text", "text": line})
        i += 1

    return root


# --- Usage ---
with open("bylaws_flat.tex", "r", encoding="utf-8") as f:
    lines = f.readlines()

parsed = parse_latex(lines)

with open("bylaws.json", "w", encoding="utf-8") as f:
    json.dump(parsed, f, indent=2)

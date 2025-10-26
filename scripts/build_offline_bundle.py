#!/usr/bin/env python3
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
DIST = ROOT / "dist"

MODULE_ORDER = [
    "alerts.js",
    "analyst.js",
    "atmo.js",
    "basemap.js",
    "colorTables.js",
    "radar.js",
    "renderer.js",
    "ui.js",
    "main.js",
]

IMPORT_PATTERN = re.compile(r'^import\s+\{([^}]+)\}\s+from\s+["\'](.+?)["\'];?\s*$', re.MULTILINE)
EXPORT_CONST_PATTERN = re.compile(r'export\s+const\s+(\w+)(\s*=)')
EXPORT_FUNCTION_PATTERN = re.compile(r'export\s+function\s+(\w+)\s*\(')


def transform_module(path: pathlib.Path):
    source = path.read_text()
    exports = []

    def replace_import(match: re.Match):
        names = ",".join(name.strip() for name in match.group(1).split(","))
        module = match.group(2)
        return f"const {{{names}}} = require(\"{module}\");"

    source = IMPORT_PATTERN.sub(replace_import, source)

    def replace_export_const(match: re.Match):
        name = match.group(1)
        exports.append(name)
        return f"const {name}{match.group(2)}"

    source = EXPORT_CONST_PATTERN.sub(replace_export_const, source)

    def replace_export_function(match: re.Match):
        name = match.group(1)
        exports.append(name)
        return f"function {name}("

    source = EXPORT_FUNCTION_PATTERN.sub(replace_export_function, source)

    export_lines = [f"exports.{name} = {name};" for name in dict.fromkeys(exports)]
    if export_lines:
        source = source.rstrip() + "\n\n" + "\n".join(export_lines) + "\n"
    else:
        source = source.rstrip() + "\n"
    return source


def build():
    DIST.mkdir(parents=True, exist_ok=True)
    modules = {}
    for name in MODULE_ORDER:
        module_path = SRC / name
        modules[f"./{name}"] = transform_module(module_path)

    lines = ["(function (global) {", "  'use strict';", "  const modules = {"]
    for module_id, body in modules.items():
        lines.append(f"    '{module_id}': function (module, exports, require) {{")
        for line in body.splitlines():
            lines.append("      " + line)
        lines.append("    },")
    if lines[-1].endswith(','):
        lines[-1] = lines[-1][:-1]
    lines.append("  };\n")
    lines.append("  const cache = {};\n")
    lines.append("  function require(id) {")
    lines.append("    if (cache[id]) {")
    lines.append("      return cache[id].exports;")
    lines.append("    }")
    lines.append("    const factory = modules[id];")
    lines.append("    if (!factory) {")
    lines.append("      throw new Error('Cannot find module: ' + id);")
    lines.append("    }")
    lines.append("    const module = { exports: {} };")
    lines.append("    cache[id] = module;")
    lines.append("    factory(module, module.exports, require);")
    lines.append("    return module.exports;")
    lines.append("  }\n")
    lines.append("  global.SyntheticRadar = global.SyntheticRadar || {};\n")
    lines.append("  global.SyntheticRadar.require = require;\n")
    lines.append("  global.SyntheticRadar.modules = Object.keys(modules);\n")
    lines.append("  require('./main.js');\n")
    lines.append("})(typeof globalThis !== 'undefined' ? globalThis : window);\n")

    output = "\n".join(lines)
    (DIST / "offline-bundle.js").write_text(output)


if __name__ == '__main__':
    build()

"""
一次性脚本：解析 TOOL_CATALOG.md + pyscripts 函数签名，
为每个 pyscripts/*.py 注入 TOOL_DEF 常量。
"""
import ast
import inspect
import importlib
import re
import sys
import typing
from pathlib import Path

ROOT = Path(__file__).parent
CATALOG = ROOT / "TOOL_CATALOG.md"
PYSCRIPTS = ROOT / "pyscripts"

# 参数类型映射（基础类型）
TYPE_MAP = {
    "int": "integer", "float": "number", "bool": "boolean",
    "str": "string", "dict": "object", "list": "array"
}

SKIP_PARAMS = {"dry_run", "script_path"}

def parse_catalog() -> dict[str, str]:
    """返回 {tool_name: description}"""
    text = CATALOG.read_text(encoding="utf-8")
    result = {}
    for m in re.finditer(r"### (\w+)\n\*\*作用：\*\* (.+)", text):
        result[m.group(1)] = m.group(2).strip()
    return result

def resolve_type(ann) -> dict:
    """【核心更新】递归解析 Python 类型注解为标准 JSON Schema"""
    if ann is type(None):
        return {"type": "null"}
    if ann is typing.Any:
        return {} # 任何类型均可
        
    origin = typing.get_origin(ann)
    args = typing.get_args(ann)

    # 1. 处理 Literal 枚举
    if origin is typing.Literal:
        vals = list(args)
        inner_type = type(vals[0]).__name__ if vals else "str"
        return {"type": TYPE_MAP.get(inner_type, "string"), "enum": vals}

    # 2. 处理 Union / Optional (多类型支持)
    if origin is typing.Union:
        valid_types = [a for a in args if a is not type(None)]
        if len(valid_types) == 1:
            return resolve_type(valid_types[0])
        else:
            # 如果是真正的多类型 (如 Union[int, str])，使用 JSON Schema 的 anyOf
            return {"anyOf": [resolve_type(t) for t in valid_types]}

    # 3. 处理 List / Tuple / Set (数组支持)
    if origin in (list, tuple, set, typing.List, typing.Tuple, typing.Set):
        if args:
            # 递归解析 List 内部的类型
            return {"type": "array", "items": resolve_type(args[0])}
        return {"type": "array"}

    # 4. 处理 Dict / Mapping
    if origin in (dict, typing.Dict, typing.Mapping):
        return {"type": "object"}

    # 5. 处理普通基础类型 (int, str, bool 等)
    ann_name = getattr(ann, "__name__", str(ann))
    return {"type": TYPE_MAP.get(ann_name, "string")}

def get_param_schema(py_file: Path, tool_name: str) -> dict:
    """从函数签名提取 input_schema"""
    sys.path.insert(0, str(ROOT))
    try:
        mod = importlib.import_module(f"pyscripts.{tool_name}")
        fn = getattr(mod, tool_name)
        sig = inspect.signature(fn, eval_str=True)
    except Exception:
        return {"type": "object", "properties": {}, "required": []}

    properties = {}
    required = []

    for name, param in sig.parameters.items():
        if name in SKIP_PARAMS:
            continue
            
        # 直接调用递归解析函数，代码变得极其干净
        properties[name] = resolve_type(param.annotation)

        if param.default is inspect.Parameter.empty:
            required.append(name)

    return {"type": "object", "properties": properties, "required": required}

def build_tool_def(name: str, desc: str, schema: dict) -> str:
    import json
    d = {"name": name, "description": desc, "input_schema": schema}
    return f"TOOL_DEF = {json.dumps(d, ensure_ascii=False)}\n"

def inject(py_file: Path, tool_def_line: str):
    content = py_file.read_text(encoding="utf-8")
    if content.startswith("TOOL_DEF"):
        rest = content[content.index("\n") + 1:]
        py_file.write_text(tool_def_line + "\n" + rest, encoding="utf-8")
        print(f"  updated: {py_file.name}")
    else:
        py_file.write_text(tool_def_line + "\n" + content, encoding="utf-8")
        print(f"  injected: {py_file.name}")

def main():
    catalog = parse_catalog()
    for py_file in sorted(PYSCRIPTS.glob("*.py")):
        name = py_file.stem
        if name.startswith("_"):
            continue
        desc = catalog.get(name, name)
        schema = get_param_schema(py_file, name)
        tool_def_line = build_tool_def(name, desc, schema)
        inject(py_file, tool_def_line)
    print("Done.")

if __name__ == "__main__":
    main()
import importlib
import inspect
import json
from openai import OpenAI
from config import TOOL_CATEGORIES, DANGEROUS_TOOLS, CATEGORY_DESCRIPTIONS, MODEL, API_KEY, BASE_URL

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)


def _to_openai_tool(tool_def: dict) -> dict:
    """将 TOOL_DEF 格式转为 OpenAI function tool 格式"""
    return {
        "type": "function",
        "function": {
            "name": tool_def["name"],
            "description": tool_def["description"],
            "parameters": tool_def["input_schema"],
        },
    }


def detect_categories(user_input: str) -> list[str]:
    cats_desc = "\n".join(f"- {k}: {v}" for k, v in CATEGORY_DESCRIPTIONS.items())
    resp = client.chat.completions.create(
        model=MODEL,
        max_tokens=100,
        messages=[{
            "role": "user",
            "content": (
                f"用户问题：「{user_input}」\n\n"
                f"从以下类别中选出相关的（可多选），返回JSON数组，只返回数组不要其他内容：\n{cats_desc}"
            ),
        }],
    )
    text = resp.choices[0].message.content.strip()
    try:
        cats = json.loads(text)
        valid = [c for c in cats if c in TOOL_CATEGORIES]
        return valid if valid else ["system", "diag"]
    except Exception:
        return ["system", "diag"]


def load_tools(categories: list[str]) -> list[dict]:
    tools = []
    seen = set()
    for cat in categories:
        for name in TOOL_CATEGORIES.get(cat, []):
            if name in seen:
                continue
            seen.add(name)
            try:
                mod = importlib.import_module(f"pyscripts.{name}")
                tools.append(_to_openai_tool(mod.TOOL_DEF))
            except (ImportError, AttributeError):
                pass
    return tools


def is_dangerous(tool_name: str) -> bool:
    return tool_name in DANGEROUS_TOOLS


def extract_facts(conversation: list[dict], current_facts: dict) -> dict | None:
    """从本轮对话中提取值得记忆的系统信息，返回更新后的facts，无更新返回None"""
    summary = "\n".join(
        f"{m['role']}: {m['content'] if isinstance(m['content'], str) else str(m['content'])[:300]}"
        for m in conversation[-10:]  # 只看最近10条
    )
    resp = client.chat.completions.create(
        model=MODEL,
        max_tokens=300,
        messages=[{
            "role": "user",
            "content": (
                f"当前已知信息：{json.dumps(current_facts, ensure_ascii=False)}\n\n"
                f"本轮对话摘要：\n{summary}\n\n"
                "从对话中提取值得长期记忆的系统信息（如硬件配置、电源计划、用户偏好、已执行的操作等）。"
                "若有新信息，返回更新后的完整JSON对象（与当前已知信息格式相同）；若无新信息，返回null。"
                "只返回JSON，不要其他内容。"
            ),
        }],
    )
    text = resp.choices[0].message.content.strip()
    if text.lower() == "null":
        return None
    try:
        return json.loads(text)
    except Exception:
        return None
    

def execute_tool(tool_name: str, tool_input: dict) -> dict:
    mod = importlib.import_module(f"pyscripts.{tool_name}")
    fn = getattr(mod, tool_name)
    sig = inspect.signature(fn)
    valid_params = {k: v for k, v in tool_input.items() if k in sig.parameters}
    return fn(**valid_params)

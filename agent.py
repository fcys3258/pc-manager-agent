import json
import logging
import os
import sys
import threading
import itertools
from datetime import datetime
from openai import OpenAI
from tools import detect_categories, load_tools, is_dangerous, execute_tool, extract_facts
from memory import Memory
from config import MODEL, MAX_REACT_STEPS, API_KEY, BASE_URL

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename=f"logs/{datetime.now().strftime('%Y%m%d')}.log",
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(message)s",
    encoding="utf-8",
)
log = logging.getLogger(__name__)


# ── Spinner ──────────────────────────────────────────────────────────────────

class Spinner:
    def __init__(self):
        self._msg = ""
        self._stop = threading.Event()
        self._t = None

    def _run(self):
        for ch in itertools.cycle("⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"):
            if self._stop.is_set():
                break
            line = f"{ch} {self._msg}"
            sys.stdout.write(f"\r{line:<60}")
            sys.stdout.flush()
            self._stop.wait(0.1)
        sys.stdout.write(f"\r{'':<60}\r")
        sys.stdout.flush()

    def set(self, msg: str):
        self._msg = msg

    def start(self, msg: str = ""):
        self._msg = msg
        self._stop.clear()
        self._t = threading.Thread(target=self._run, daemon=True)
        self._t.start()

    def stop(self):
        self._stop.set()
        if self._t:
            self._t.join()


spinner = Spinner()


# ── Logging helpers ───────────────────────────────────────────────────────────

def _log_request(messages, tools):
    log.debug("=== LLM REQUEST ===\ntools: %s\nmessages: %s",
              json.dumps([t["function"]["name"] for t in tools], ensure_ascii=False),
              json.dumps(messages, ensure_ascii=False))


def _log_response(msg, finish_reason):
    log.debug("=== LLM RESPONSE === finish_reason=%s\ncontent: %s\ntool_calls: %s",
              finish_reason, msg.content,
              json.dumps([{"name": tc.function.name, "args": tc.function.arguments}
                          for tc in (msg.tool_calls or [])], ensure_ascii=False))


# ── Core ──────────────────────────────────────────────────────────────────────

def confirm_dangerous(tool_name: str, tool_input: dict) -> bool:
    spinner.stop()
    print(f"\n[警告] 即将执行高危操作: {tool_name}")
    print(f"参数: {json.dumps(tool_input, ensure_ascii=False)}")
    ans = input("确认执行? (y/n): ").strip().lower()
    return ans == "y"


def run_react_loop(user_input: str, memory: Memory, categories: list[str]):
    tools = load_tools(categories)
    if not tools:
        print("未找到相关工具")
        return

    log.info("用户输入: %s | 类别: %s", user_input, categories)
    system = memory.build_system_prompt(categories)
    memory.add("user", user_input)

    spinner.start("正在思考...")

    for step in range(MAX_REACT_STEPS):
        messages = [{"role": "system", "content": system}] + memory.get_messages()
        _log_request(messages, tools)

        spinner.set("正在等待模型回复...")
        response = client.chat.completions.create(
            model=MODEL, max_tokens=4096, tools=tools, messages=messages,
        )
        msg = response.choices[0].message
        finish_reason = response.choices[0].finish_reason
        _log_response(msg, finish_reason)

        assistant_msg = {"role": "assistant", "content": msg.content or ""}
        if msg.tool_calls:
            assistant_msg["tool_calls"] = [
                {"id": tc.id, "type": "function",
                 "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                for tc in msg.tool_calls
            ]
        memory.add("assistant", assistant_msg["content"])
        memory.session_messages[-1] = assistant_msg

        if finish_reason == "stop" or not msg.tool_calls:
            spinner.set("正在总结对话...")
            new_facts = extract_facts(memory.get_messages(), memory.facts)
            if new_facts:
                memory.facts = new_facts
                memory.save_facts()
                log.info("记忆已更新: %s", new_facts)
            spinner.stop()
            print(f"\nAssistant: {msg.content}\n")
            log.info("最终回复: %s", msg.content)
            break

        for tc in msg.tool_calls:
            tool_name = tc.function.name
            try:
                tool_input = json.loads(tc.function.arguments)
            except json.JSONDecodeError as e:
                log.error("工具参数解析失败: %s | error: %s", tc.function.arguments, str(e))
                memory.session_messages.append({
                    "role": "tool", "tool_call_id": tc.id,
                    "content": json.dumps({"ok": False, "error": "参数解析失败"}, ensure_ascii=False),
                })
                continue
            log.info("工具调用 [step=%d]: %s %s", step, tool_name, tool_input)

            if is_dangerous(tool_name):
                if not confirm_dangerous(tool_name, tool_input):
                    log.info("用户取消: %s", tool_name)
                    memory.session_messages.append({
                        "role": "tool", "tool_call_id": tc.id,
                        "content": json.dumps({"ok": False, "error": "用户取消操作"}, ensure_ascii=False),
                    })
                    continue

            spinner.set(f"正在执行 {tool_name}...")
            result = execute_tool(tool_name, tool_input)
            log.info("工具结果: ok=%s | %s", result.get("ok"), str(result.get("data", result))[:500])

            memory.session_messages.append({
                "role": "tool", "tool_call_id": tc.id,
                "content": json.dumps(result, ensure_ascii=False),
            })
    else:
        spinner.stop()
        log.warning("达到最大步骤数 (%d)", MAX_REACT_STEPS)
        print("[警告] 达到最大步骤数")


def _ensure_admin():
    import ctypes
    is_admin = ctypes.windll.shell32.IsUserAnAdmin()
    if is_admin:
        return
    print("当前以普通用户身份运行，部分工具需要管理员权限。")
    ans = input("是否以管理员身份重新启动? (y/n): ").strip().lower()
    if ans == "y":
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit(0)
    else:
        print("[提示] 已跳过提权，部分工具可能执行失败。\n")


def main():
    _ensure_admin()
    memory = Memory()
    print("PC管家助手已启动。输入 'quit' 退出，'clear' 清除会话。\n")

    while True:
        user_input = input("你: ").strip()
        if not user_input:
            continue
        if user_input.lower() == "quit":
            memory.save_trajectory()
            memory.save_facts()
            print("已保存记忆，再见。")
            break
        if user_input.lower() == "clear":
            memory.save_trajectory()
            memory.session_messages.clear()
            print("[会话已清除]")
            continue

        spinner.start("正在分析意图...")
        categories = detect_categories(user_input)
        log.info("意图类别: %s", categories)
        run_react_loop(user_input, memory, categories)
        memory.trim_if_needed()


if __name__ == "__main__":
    main()

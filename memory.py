import json
import os
from datetime import datetime
from config import MEMORY_FILE


class Memory:
    def __init__(self):
        self.system = ""
        self.session_messages: list[dict] = []
        self.facts: dict = self._load_facts()

    def _load_facts(self) -> dict:
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, encoding="utf-8") as f:
                return json.load(f)
        return {"system_profile": {}, "user_preferences": {}, "notes": ""}

    def save_facts(self):
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(self.facts, f, ensure_ascii=False, indent=2)

    def add(self, role: str, content):
        self.session_messages.append({"role": role, "content": content})

    def get_messages(self) -> list[dict]:
        return [{"role": "system", "content": self.system}] + self.session_messages

    def build_system_prompt(self, categories: list[str]) -> str:
        facts_str = json.dumps(self.facts, ensure_ascii=False, indent=2)
        return f"""你是一个PC管家助手，帮助用户诊断和修复Windows电脑问题。

已知用户系统信息：
{facts_str}

当前加载的工具类别：{categories}
今天日期：{datetime.now().strftime('%Y-%m-%d')}

工作原则：
- 用中文回复用户，简洁专业
- 如果发现重要的系统信息（如硬件配置、用户偏好），请在最终回复中告知用户，以便记录
- 如果工具调用失败，查看返回的错误信息，尝试修正后再次调用"""

    def save_evicted_trajectory(self, evicted_messages: list[dict]):
        """【冷数据归档】将超出窗口被截断的消息保存下来"""
        if not evicted_messages:
            return
            
        os.makedirs("trajectories", exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_path = f"trajectories/chunk_{timestamp}.json"
        
        export_data = {
            "timestamp": timestamp,
            "type": "eviction_chunk", # 标记这是被截断的片段
            "message_count": len(evicted_messages),
            "messages": evicted_messages
        }
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
            
        import logging
        logging.getLogger(__name__).info("已将超出的 %d 条历史消息截断并归档至 %s", len(evicted_messages), file_path)


    def trim_if_needed(self, max_turns: int = 20):
        """带有冷数据归档和安全切点校验的截断机制"""
        max_msgs = max_turns * 2
        if len(self.session_messages) <= max_msgs:
            return

        # 1. 寻找安全切点 (从倒数 max_msgs 的位置开始，向后寻找第一个 user 消息)
        cut_index = len(self.session_messages) - max_msgs
        for i in range(cut_index, len(self.session_messages)):
            if self.session_messages[i].get("role") == "user":
                cut_index = i
                break
                
        # 2. 分离“被淘汰的冷消息”和“要保留的热消息”
        evicted_messages = self.session_messages[:cut_index]
        retained_messages = self.session_messages[cut_index:]

        # 3. 归档冷消息
        self.save_evicted_trajectory(evicted_messages)

        # 4. 更新内存中的热消息
        self.session_messages = retained_messages


    def save_trajectory(self):
        """【开发者工具】将本次会话的所有原始消息落盘，用于后续复盘和优化"""
        # 如果根本没说话，就不保存了
        if not self.session_messages:
            return
            
        os.makedirs("trajectories", exist_ok=True)
        
        # 使用当前时间戳作为文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_path = f"trajectories/session_{timestamp}.json"
        
        # 将当前的 Facts 快照和完整的对话记录打包
        export_data = {
            "timestamp": timestamp,
            "message_count": len(self.session_messages),
            "messages": self.get_messages()
        }
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
            
        print(f"[Telemetry] 完整对话轨迹已归档至: {file_path}")

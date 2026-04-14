API_KEY = "sk-xxx"
BASE_URL = ""
MODEL = ""
MAX_REACT_STEPS = 10
MEMORY_FILE = "memory.json"

TOOL_CATEGORIES = {
    "network": [
        "clear_proxy_config", "flush_dns", "get_active_connections", "get_dns_config",
        "get_network_configuration_snapshot", "get_route_table", "get_vpn_status",
        "get_wifi_details", "release_renew_ipconfig", "reset_network_stack",
        "reset_winhttp_proxy", "test_connectivity", "test_secure_channel", "trace_network_route",
    ],
    "system": [
        "get_battery_status", "get_bitlocker_status", "get_device_status", "get_disk_info",
        "get_firewall_status", "get_pnp_device_list", "get_system_specs",
        "get_temperature", "get_tpm_status", "get_usb_info",
    ],
    "process": [
        "check_process_health", "get_process_cpu_time", "get_running_processes",
        "get_service_status", "kill_process", "restart_service", "start_service", "stop_service",
    ],
    "power": ["get_active_power_plan", "get_power_requests", "set_active_power_plan"],
    "printer": [
        "cancel_print_job", "control_print_job", "get_printer_config", "get_printer_queue",
        "install_printer", "list_printers", "remove_printer", "set_default_printer", "set_printer_config",
    ],
    "software": ["get_app_last_used_time", "get_browser_extensions", "get_installed_software", "uninstall_software"],
    "startup": ["disable_startup_item", "enable_startup_item", "get_startup_items"],
    "file": ["execute_cleanup_items", "get_directory_size", "list_large_files", "move_file_to_recycle_bin", "scan_cleanup_items"],
    "security": ["check_root_certificate", "force_gpupdate", "get_antivirus_status", "get_gpo_status", "get_os_update_status"],
    "hardware": ["enable_disable_device", "get_audio_service_status", "get_monitor_topology", "list_camera_devices", "reinstall_driver", "reset_audio_service"],
    "sysconfig": [
        "delete_hosts_entry", "get_hosts_content", "get_local_admin_members",
        "get_mic_privacy_settings", "get_pagefile_status", "get_password_expiry",
        "get_system_uptime", "get_user_context", "get_usb_storage_devices",
    ],
    "diag": ["check_time_synchronization", "get_bsod_history", "get_event_log", "get_system_health_snapshot", "get_top_window"],
}

# 类别描述，用于发给LLM做意图识别
CATEGORY_DESCRIPTIONS = {
    "network": "网络管理：DNS、IP、连接、代理、VPN、WiFi、路由、网络重置",
    "system": "系统信息：磁盘、内存、CPU、温度、电池、BitLocker、防火墙、USB设备",
    "process": "进程与服务：查看/终止进程、启动/停止/重启Windows服务",
    "power": "电源管理：查看/切换电源计划（节能/平衡/高性能）",
    "printer": "打印机管理：打印机列表、队列、安装、删除、配置",
    "software": "软件与应用：已安装软件、卸载、浏览器扩展",
    "startup": "启动项管理：查看/启用/禁用开机自启项",
    "file": "文件操作：磁盘清理、大文件扫描、回收站",
    "security": "安全与更新：杀毒软件、系统更新、组策略",
    "hardware": "硬件与设备：驱动、音频服务、摄像头、显示器、设备启用/禁用",
    "sysconfig": "系统配置：hosts文件、虚拟内存、用户账户、USB存储",
    "diag": "诊断工具：蓝屏历史、事件日志、系统健康快照、时间同步",
}

DANGEROUS_TOOLS = {
    "kill_process", "uninstall_software", "disable_startup_item", "enable_startup_item",
    "enable_disable_device", "reinstall_driver", "reset_network_stack", "execute_cleanup_items",
    "delete_hosts_entry", "restart_service", "stop_service", "force_gpupdate",
    "release_renew_ipconfig", "reset_audio_service", "set_active_power_plan",
    "move_file_to_recycle_bin", "cancel_print_job", "remove_printer", "install_printer",
    "reset_winhttp_proxy", "clear_proxy_config", "start_service", "set_printer_config",
    "control_print_job", "set_default_printer",
}

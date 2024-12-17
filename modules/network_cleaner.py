import os
import subprocess
import configparser
import yaml
from pathlib import Path

class NetworkCleaner:
    def __init__(self):
        """
        初始化网络配置文件的扫描路径
        """
        self.network_config_paths = [
            "/etc/NetworkManager/system-connections",  # NetworkManager 配置目录
            "/etc/netplan",  # netplan 配置
            "/etc/network/interfaces.d",  # legacy network 配置
            "/etc/network/interfaces"  # 主要网络接口文件
        ]

    def scan_network_configs(self):
        """
        扫描网络配置文件，解析内容
        返回: [{"name": 文件名, "path": 文件路径, "status": "used"/"unused", "details": 具体配置}]
        """
        results = []
        for path in self.network_config_paths:
            if os.path.exists(path):
                if os.path.isdir(path):
                    for file in os.listdir(path):
                        full_path = os.path.join(path, file)
                        if os.path.isfile(full_path):
                            result = self.parse_network_config(full_path)
                            if result:
                                results.append(result)
                elif os.path.isfile(path):
                    result = self.parse_network_config(path)
                    if result:
                        results.append(result)
        return results

    def parse_network_config(self, file_path):
        """
        解析单个网络配置文件并返回具体配置内容
        """
        details = []
        status = self.check_config_usage(file_path)
        try:
            if file_path.endswith(".nmconnection"):  # NetworkManager 配置
                details = self.parse_nmconnection(file_path)
            elif file_path.endswith(('.yaml', '.yml')):  # Netplan 配置
                details = self.parse_yaml(file_path)
            else:  # 其他纯文本配置文件
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    details = [line.strip() for line in f if line.strip()]  # 去除空行
        except Exception as e:
            details = [f"无法解析: {e}"]

        return {
            "name": os.path.basename(file_path),
            "path": file_path,
            "status": status,
            "details": details
        }

    def parse_nmconnection(self, file_path):
        """
        解析 NetworkManager 的 .nmconnection 配置文件
        """
        details = []
        parser = configparser.ConfigParser(allow_no_value=True, delimiters=('=',))
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                parser.read_string(content)

            for section in parser.sections():
                details.append(f"[{section}]")
                for key, value in parser.items(section):
                    details.append(f"  {key}={value}")
        except Exception as e:
            details = [f"无法解析 nmconnection 文件: {e}"]
        return [line for line in details if line.strip()]  # 去除多余空行

    def parse_yaml(self, file_path):
        """
        解析 YAML 配置文件 (如 netplan)
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                return self.format_yaml(data)
        except yaml.YAMLError as e:
            return [f"YAML 格式错误: {e}"]
        except Exception as e:
            return [f"无法解析 YAML 文件: {e}"]

    def format_yaml(self, data, prefix=""):
        """
        将 YAML 数据递归格式化为字符串列表
        """
        details = []
        if isinstance(data, dict):
            for key, value in data.items():
                new_prefix = f"{prefix}{key}."
                details.extend(self.format_yaml(value, new_prefix))
        elif isinstance(data, list):
            for i, item in enumerate(data):
                details.extend(self.format_yaml(item, f"{prefix}[{i}]."))
        else:
            details.append(f"{prefix.rstrip('.')}: {data}")
        return [line for line in details if line.strip()]  # 去除多余空行

    def check_config_usage(self, file_path):
        """
        检查指定网络配置文件是否正在使用
        """
        try:
            if file_path.endswith(".nmconnection"):
                config_name = os.path.basename(file_path).replace(' ', '_').strip().replace('.nmconnection', '')
                output = subprocess.check_output(["nmcli", "-t", "-f", "NAME", "con", "show"], text=True)
                if config_name in output:
                    return "used"
                return "unused"
            return "unknown"
        except Exception as e:
            print(f"检测配置文件使用状态时出错: {e}")
            return "unknown"

    def delete_network_configs(self, config_paths):
        """
        删除指定的网络配置文件
        """
        for path in config_paths:
            try:
                if os.path.exists(path):
                    os.remove(path)
                    print(f"已删除网络配置文件: {path}")
                else:
                    print(f"文件不存在: {path}")
            except Exception as e:
                print(f"删除失败: {path}, 错误: {e}")

# 调试代码
if __name__ == "__main__":
    cleaner = NetworkCleaner()
    results = cleaner.scan_network_configs()
    print("扫描到的网络配置文件:")
    for result in results:
        print(f"名称: {result['name']}, 路径: {result['path']}, 状态: {result['status']}")
        print("详细配置:")
        for line in result['details']:
            print(f"  {line}")
        print()

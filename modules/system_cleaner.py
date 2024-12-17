import os
from pathlib import Path

class SystemCleaner:
    def __init__(self):
        # 定义需要扫描的常见垃圾文件目录
        self.directories_to_scan = {
            "Temporary Files": "/tmp",
            "User Cache": str(Path.home() / ".cache"),
            "System Logs": "/var/log",
            "Package Cache": "/var/cache/apt/archives"
        }

    def scan_system(self):
        """扫描系统垃圾文件并返回结果"""
        results = []
        for category, directory in self.directories_to_scan.items():
            if os.path.exists(directory):
                category_result = {"category": category, "files": []}
                total_size = 0

                # 遍历目录中的文件
                for root, _, files in os.walk(directory):
                    for file in files:
                        file_path = os.path.join(root, file)
                        try:
                            file_size = os.path.getsize(file_path)
                            category_result["files"].append({
                                "path": file_path,
                                "size": file_size
                            })
                            total_size += file_size
                        except Exception as e:
                            print(f"无法读取文件 {file_path}: {e}")
                            continue

                category_result["total_size"] = total_size
                results.append(category_result)
            else:
                print(f"目录不存在: {directory}")
        return results

    def delete_files(self, file_paths):
        """删除指定的文件"""
        for file_path in file_paths:
            # try:
            os.remove(file_path)
            print(f"已删除: {file_path}")
            # except Exception as e:
            #     print(f"无法删除文件 {file_path}: {e}")

# 调试代码
if __name__ == "__main__":
    cleaner = SystemCleaner()
    scan_results = cleaner.scan_system()
    for result in scan_results:
        print(f"Category: {result['category']}")
        print(f"Total Size: {result['total_size'] / (1024 * 1024):.2f} MB")
        for file in result["files"]:
            print(f"  - {file['path']} ({file['size'] / 1024:.2f} KB)")

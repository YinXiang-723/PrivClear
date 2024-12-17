import os
from pathlib import Path
import subprocess
import sqlite3

class BrowserCleaner:
    def __init__(self):
        # 初始化支持的浏览器及其路径
        self.os_type = self.detect_os()
        self.browsers = self.detect_installed_browsers()

    def detect_os(self):
        """检测操作系统类型"""
        if os.name == 'nt':
            return "Windows"
        elif os.name == 'posix':
            return "Linux/macOS"
        else:
            return "Unknown"

    def detect_installed_browsers(self):
        """检测已安装的浏览器"""
        browsers = {}
        if self.is_chrome_installed():
            browsers["Google Chrome"] = self.get_chrome_paths()
        if self.is_firefox_installed():
            browsers["Mozilla Firefox"] = self.get_firefox_paths()
        if self.is_edge_installed():
            browsers["Microsoft Edge"] = self.get_edge_paths()
        return browsers

    def is_chrome_installed(self):
        """通过命令行检测 Chrome 是否已安装"""
        try:
            if self.os_type == "Windows":
                subprocess.run(["where", "chrome"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                subprocess.run(["which", "google-chrome"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except subprocess.CalledProcessError:
            return False

    def is_firefox_installed(self):
        """通过命令行检测 Firefox 是否已安装"""
        try:
            if self.os_type == "Windows":
                subprocess.run(["where", "firefox"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                subprocess.run(["which", "firefox"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except subprocess.CalledProcessError:
            return False

    def is_edge_installed(self):
        """通过命令行检测 Edge 是否已安装"""
        try:
            if self.os_type == "Windows":
                subprocess.run(["where", "msedge"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return True
            elif self.os_type == "Linux/macOS":
                subprocess.run(["which", "microsoft-edge"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return True
            return False
        except subprocess.CalledProcessError:
            return False

    def get_chrome_paths(self):
        """返回 Chrome 的数据路径"""
        if self.os_type == "Windows":
            return {
                "cookies": Path("C:/Users") / os.getlogin() / "AppData/Local/Google/Chrome/User Data/Default/Cookies",
                "history": Path("C:/Users") / os.getlogin() / "AppData/Local/Google/Chrome/User Data/Default/History"
            }
        elif self.os_type == "Linux/macOS":
            return {
                "cookies": Path.home() / ".config/google-chrome/Default/Cookies",
                "history": Path.home() / ".config/google-chrome/Default/History"
            }
        return {}

    def get_firefox_paths(self):
        """返回 Firefox 的数据路径"""
        # 优先检查 Snap 安装路径
        snap_firefox_path = Path.home() / "snap/firefox/common/.mozilla/firefox/"
        if snap_firefox_path.exists():
            base_profile_path = snap_firefox_path
        else:
            base_profile_path = Path.home() / ".mozilla/firefox/"

        profiles_ini = base_profile_path / "profiles.ini"
        if not profiles_ini.exists():
            return {}

        # 解析 profiles.ini 文件，找到默认配置的路径
        profile_path = None
        with profiles_ini.open() as f:
            for line in f:
                if line.startswith("Path="):
                    profile_path = line.strip().split("=")[-1]
                    break

        if profile_path:
            full_profile_path = base_profile_path / profile_path
            return {
                "cookies": full_profile_path / "cookies.sqlite",
                "history": full_profile_path / "places.sqlite",
            }
        return {}

    def get_edge_paths(self):
        """返回 Edge 的数据路径"""
        if self.os_type == "Windows":
            return {
                "cookies": Path("C:/Users") / os.getlogin() / "AppData/Local/Microsoft/Edge/User Data/Default/Cookies",
                "history": Path("C:/Users") / os.getlogin() / "AppData/Local/Microsoft/Edge/User Data/Default/History"
            }
        elif self.os_type == "Linux/macOS":
            return {
                "cookies": Path.home() / ".config/microsoft-edge/Default/Cookies",
                "history": Path.home() / ".config/microsoft-edge/Default/History"
            }
        return {}

    def scan_browsers(self):
        """扫描各浏览器目录并返回结果"""
        results = []

        # 定义浏览器与其对应方法的映射
        extract_methods = {
            "Mozilla Firefox": {
                "cookies": self.extract_firefox_cookies,
                "history": self.extract_firefox_history,
            },
            "Google Chrome": {
                "cookies": self.extract_cookies,
                "history": self.extract_history,
            },
            "Microsoft Edge": {
                "cookies": self.extract_cookies,
                "history": self.extract_history,
            },
        }

        for browser, paths in self.browsers.items():
            browser_result = {"browser": browser, "details": []}

            for data_type, path in paths.items():
                if not path.exists():
                    browser_result["details"].append(f"{data_type.capitalize()} not found. Checked path: {path}")
                    continue

                # 获取当前浏览器对应的方法
                extract_method = extract_methods.get(browser, {}).get(data_type)
                if extract_method:
                    try:
                        data = extract_method(path)
                        if data:
                            browser_result["details"].append(f"{data_type.capitalize()}: {path}")
                        else:
                            browser_result["details"].append(f"{data_type.capitalize()}: {path} (不可读取)")
                    except Exception as e:
                        browser_result["details"].append(f"{data_type.capitalize()}: {path} (读取失败: {e})")
                else:
                    browser_result["details"].append(f"{data_type.capitalize()}: {path} (无提取方法)")

            results.append(browser_result)

        return results

    def extract_firefox_cookies(self, path):
        """专门处理 Firefox cookies.sqlite 的提取逻辑"""
        try:
            conn = sqlite3.connect(path)
            cursor = conn.cursor()
            cursor.execute("SELECT host, name, value FROM moz_cookies")
            cookies = cursor.fetchall()
            conn.close()
            return [f"{host}={name}" for host, name, value in cookies]
        except sqlite3.OperationalError as e:
            print(f"Error reading Firefox cookies: {e}")
            return []
        except Exception as e:
            print(f"Unexpected error: {e}")
            return []

    def extract_firefox_history(self, path):
        """专门处理 Firefox places.sqlite 的提取逻辑"""
        try:
            conn = sqlite3.connect(path)
            cursor = conn.cursor()
            # 从 moz_places 表提取 URL 和标题，并与 moz_historyvisits 表关联
            cursor.execute("""
                SELECT moz_places.url, moz_places.title, moz_places.last_visit_date
                FROM moz_places
                JOIN moz_historyvisits ON moz_places.id = moz_historyvisits.place_id
                WHERE moz_places.hidden = 0
                ORDER BY moz_places.last_visit_date DESC
            """)
            history = cursor.fetchall()
            conn.close()
            # 格式化结果为 "title (url)"
            return [
                f"{title if title else 'No Title'} ({url})"
                for url, title, last_visit_date in history if url
            ]
        except sqlite3.OperationalError as e:
            print(f"Error reading Firefox history: {e}")
            return []
        except Exception as e:
            print(f"Unexpected error: {e}")
            return []

    def extract_cookies(self, path):
        """提取并返回 Cookies 信息"""
        try:
            conn = sqlite3.connect(path)
            cursor = conn.cursor()
            cursor.execute("SELECT host_key, name, value FROM cookies")
            cookies = cursor.fetchall()
            conn.close()
            return [f"{host}={name}" for host, name, value in cookies]
        except Exception as e:
            return [f"Error reading cookies: {e}"]

    def extract_history(self, path):
        """提取并返回历史记录信息"""
        try:
            conn = sqlite3.connect(path)
            cursor = conn.cursor()
            cursor.execute("SELECT url, title FROM urls")
            history = cursor.fetchall()
            conn.close()
            return [f"{title} ({url})" for url, title in history]
        except Exception as e:
            return [f"Error reading history: {e}"]

    def clean_selected_items(self, items):
        """清理选中的记录"""
        for item in items:
            try:
                if "Cookies:" in item or "History:" in item:
                    # 从条目中提取数据库路径和具体清理信息
                    db_path, browser, table, condition = self.parse_item_for_cleaning(item)
                    if db_path and table and condition:
                        if browser == "Mozilla Firefox":
                            self.clean_firefox_item(db_path, table, condition)
                        else:
                            self.clean_chrome_edge_item(db_path, table, condition)
                    else:
                        print(f"无法解析条目: {item}")
                else:
                    print(f"无法处理的条目: {item}")
            except Exception as e:
                print(f"清理失败: {item}, 错误: {e}")

    def parse_item_for_cleaning(self, item):
        """解析需要清理的条目，返回数据库路径、浏览器、表名和条件"""
        try:
            parts = item.split(" ", 2)  # 提取条目信息
            db_path = parts[1]  # 提取数据库路径
            if "Cookies:" in item:
                browser = self.get_browser_by_path(db_path)
                host, name = parts[2].split("=")  # 提取 host 和 name
                table = "moz_cookies" if browser == "Mozilla Firefox" else "cookies"
                if browser == "Mozilla Firefox":
                    condition = f"host='{host}' OR host='.{host}' AND name='{name}'"
                else:
                    condition = f"host_key='{host}' AND name='{name}'"
                return db_path, browser, table, condition
            elif "History:" in item:
                browser = self.get_browser_by_path(db_path)
                url_part = parts[2].split("(")[-1].rstrip(")")  # 提取括号内的 URL
                table = "moz_places" if browser == "Mozilla Firefox" else "urls"
                condition = f"url='{url_part}'"
                return db_path, browser, table, condition
        except (IndexError, ValueError):
            return None, None, None, None
        return None, None, None, None

    def get_browser_by_path(self, db_path):
        """根据路径返回浏览器类型"""
        if "firefox" in db_path.lower():
            return "Mozilla Firefox"
        elif "chrome" in db_path.lower():
            return "Google Chrome"
        elif "edge" in db_path.lower():
            return "Microsoft Edge"
        return "Unknown"

    def clean_firefox_item(self, db_path, table, condition):
        """清理 Firefox 数据库中的记录"""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            # 添加 originAttributes 条件过滤
            sql = f"DELETE FROM {table} WHERE ({condition}) AND originAttributes=''"
            print(f"Firefox: 执行 SQL: {sql}")
            cursor.execute(sql)
            conn.commit()
            if cursor.rowcount == 0:
                print(f"Firefox: 未找到匹配的记录: {condition}")
            else:
                print(f"Firefox: 清理完成: {db_path}, 表: {table}, 条件: {condition}")
            conn.close()
        except Exception as e:
            print(f"Firefox: 清理失败: {db_path}, 错误: {e}")

    def clean_chrome_edge_item(self, db_path, table, condition):
        """清理 Chrome 和 Edge 数据库中的记录"""
        # try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        sql = f"DELETE FROM {table} WHERE {condition}"
        print(f"Chrome/Edge: 执行 SQL: {sql}")
        cursor.execute(sql)
        conn.commit()
        if cursor.rowcount == 0:
            print(f"Chrome/Edge: 未找到匹配的记录: {condition}")
        else:
            print(f"Chrome/Edge: 清理完成: {db_path}, 表: {table}, 条件: {condition}")
        conn.close()
        # except Exception as e:
        #     print(f"Chrome/Edge: 清理失败: {db_path}, 错误: {e}")


if __name__ == "__main__":
    cleaner = BrowserCleaner()
    print(f"Detected OS: {cleaner.os_type}")
    results = cleaner.scan_browsers()
    for result in results:
        print(f"Browser: {result['browser']}")
        for detail in result['details']:
            print(f"  - {detail}")
        print()

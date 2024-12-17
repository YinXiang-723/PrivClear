import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTreeWidgetItem, QMessageBox
from PyQt5.uic import loadUi
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor


# 导入功能模块
from modules.browser_cleaner import BrowserCleaner
from modules.system_cleaner import SystemCleaner
from modules.network_cleaner import NetworkCleaner

class PrivClearApp(QMainWindow):
    def __init__(self):
        super(PrivClearApp, self).__init__()
        loadUi('assets/privclear_ui.ui', self)

        # 初始化功能模块
        self.browser_cleaner = BrowserCleaner()
        self.system_cleaner = SystemCleaner()
        self.network_cleaner = NetworkCleaner()

        # 连接按钮到对应的方法
        self.setup_connections()

    def setup_connections(self):
        """
        初始化界面控件与方法之间的连接。
        """
        # 浏览器清理页面的按钮
        self.button_clean_browser.clicked.connect(self.handle_browser_clean)
        self.button_scan_browser.clicked.connect(self.handle_scan_browser)

        # 系统清理页面的按钮
        self.button_clean_system.clicked.connect(self.handle_clean_system)
        self.button_scan_system.clicked.connect(self.handle_scan_system)

        # 网络清理页面的按钮
        self.button_scan_network.clicked.connect(self.handle_scan_network)
        self.button_clean_network.clicked.connect(self.handle_clear_network)
        self.checkBox_unuse.stateChanged.connect(self.handle_checkbox_unuse)

        # 复选框事件
        self.checkBox_cookies.stateChanged.connect(self.handle_checkbox_cookies)
        self.checkBox_history.stateChanged.connect(self.handle_checkbox_history)

        self.checkBox_temp.stateChanged.connect(lambda state: self.handle_checkBox_state("Temporary Files", state))
        self.checkBox_logs.stateChanged.connect(lambda state: self.handle_checkBox_state("System Logs", state))

    def handle_scan_browser(self):
        """扫描浏览器并在界面中显示结果"""
        self.statusBar().showMessage("正在扫描浏览器...")  # 显示状态
        self.treeWidget_browser_info.clear()
        results = self.browser_cleaner.scan_browsers()

        for result in results:
            # 顶层：浏览器名称
            browser_item = QTreeWidgetItem(self.treeWidget_browser_info)
            browser_item.setText(0, result['browser'])
            browser_item.setCheckState(0, Qt.Unchecked)  # 保留复选框

            # 遍历扫描结果
            for detail in result['details']:
                if "Cookies:" in detail:
                    self.add_data_item(browser_item, detail, result['browser'], "cookies")
                elif "History:" in detail:
                    self.add_data_item(browser_item, detail, result['browser'], "history")

            self.treeWidget_browser_info.expandItem(browser_item)

        self.statusBar().showMessage("扫描完成")  # 更新状态

    def add_data_item(self, parent_item, detail, browser, data_type):
        """添加数据条目"""
        data_item = QTreeWidgetItem(parent_item)
        data_item.setText(0, detail)

        if "(不可读取)" in detail:
            data_item.setFlags(data_item.flags() & ~Qt.ItemIsUserCheckable)  # 不可选
        else:
            data_item.setCheckState(0, Qt.Unchecked)
            path = detail.split(": ")[1]

            # 根据浏览器调用不同的函数
            if browser == "Mozilla Firefox" and data_type == "cookies":
                data_entries = self.browser_cleaner.extract_firefox_cookies(path)
            elif browser == "Mozilla Firefox" and data_type == "history":
                data_entries = self.browser_cleaner.extract_firefox_history(path)
            elif data_type == "cookies":
                data_entries = self.browser_cleaner.extract_cookies(path)
            elif data_type == "history":
                data_entries = self.browser_cleaner.extract_history(path)
            else:
                data_entries = []

            for entry in data_entries:
                entry_item = QTreeWidgetItem(data_item)
                entry_item.setText(0, f"{data_type.capitalize()}: {path} {entry}")
                entry_item.setCheckState(0, Qt.Unchecked)

        self.treeWidget_browser_info.itemChanged.connect(self.handle_item_changed)

    def handle_item_changed(self, item, column):
        """处理复选框状态改变，支持半选状态"""
        parent = item.parent()
        if item.checkState(column) == Qt.Checked:
            # 勾选父项时，勾选所有子项
            self.set_children_check_state(item, Qt.Checked)
            # 如果所有子项被选中，勾选父级
            if parent is not None:
                all_checked = all(parent.child(i).checkState(0) == Qt.Checked for i in range(parent.childCount()))
                if all_checked:
                    parent.setCheckState(0, Qt.Checked)
                else:
                    parent.setCheckState(0, Qt.PartiallyChecked)
        elif item.checkState(column) == Qt.Unchecked:
            # 取消勾选父项时，取消所有子项
            self.set_children_check_state(item, Qt.Unchecked)
            # 如果有子项未被选中，更新父级状态
            if parent is not None:
                any_checked = any(parent.child(i).checkState(0) != Qt.Unchecked for i in range(parent.childCount()))
                if any_checked:
                    parent.setCheckState(0, Qt.PartiallyChecked)
                else:
                    parent.setCheckState(0, Qt.Unchecked)

    def set_children_check_state(self, parent_item, state):
        """设置所有子项的复选框状态"""
        for i in range(parent_item.childCount()):
            child_item = parent_item.child(i)
            child_item.setCheckState(0, state)

    def handle_checkbox_cookies(self, state):
        """当 Cookies 复选框状态改变时处理所有 Cookies 条目"""
        root = self.treeWidget_browser_info.invisibleRootItem()
        for i in range(root.childCount()):
            browser_item = root.child(i)
            for j in range(browser_item.childCount()):
                data_item = browser_item.child(j)
                if "Cookies:" in data_item.text(0):
                    self.set_children_check_state(data_item, Qt.Checked if state == Qt.Checked else Qt.Unchecked)
                    data_item.setCheckState(0, Qt.Checked if state == Qt.Checked else Qt.Unchecked)  # 更新父级条目的状态

    def handle_checkbox_history(self, state):
        """当 History 复选框状态改变时处理所有 History 条目"""
        root = self.treeWidget_browser_info.invisibleRootItem()
        for i in range(root.childCount()):
            browser_item = root.child(i)
            for j in range(browser_item.childCount()):
                data_item = browser_item.child(j)
                if "History:" in data_item.text(0):
                    self.set_children_check_state(data_item, Qt.Checked if state == Qt.Checked else Qt.Unchecked)
                    data_item.setCheckState(0, Qt.Checked if state == Qt.Checked else Qt.Unchecked)  # 更新父级条目的状态

    def get_selected_items(self):
        """获取用户选择的条目"""
        selected_items = []
        root = self.treeWidget_browser_info.invisibleRootItem()
        for i in range(root.childCount()):
            browser_item = root.child(i)
            for j in range(browser_item.childCount()):
                data_item = browser_item.child(j)
                for k in range(data_item.childCount()):
                    sub_item = data_item.child(k)
                    if sub_item.checkState(0):
                        selected_items.append(sub_item.text(0))
        return selected_items

    def handle_browser_clean(self):
        """清理选中的浏览器记录并更新视图"""
        selected_items = self.get_selected_items()
        if not selected_items:
            QMessageBox.information(self, "提示", "未选择任何记录清理")
            return

        try:
            self.browser_cleaner.clean_selected_items(selected_items)
            QMessageBox.information(self, "清理完成", "选中记录已清理")
            self.remove_cleaned_items_from_tree(selected_items)  # 更新视图
            self.statusBar().showMessage("清理完成")
        except Exception as e:
            QMessageBox.critical(self, "清理失败", f"清理过程中发生错误: {e}")

    def remove_cleaned_items_from_tree(self, cleaned_items):
        """从 TreeWidget 中移除已清理的条目，并更新父条目的状态"""
        root = self.treeWidget_browser_info.invisibleRootItem()
        for i in range(root.childCount()):
            browser_item = root.child(i)
            for j in range(browser_item.childCount() - 1, -1, -1):  # 倒序遍历子节点
                data_item = browser_item.child(j)
                for k in range(data_item.childCount() - 1, -1, -1):  # 倒序遍历子子节点
                    sub_item = data_item.child(k)
                    if sub_item.text(0) in cleaned_items:
                        data_item.removeChild(sub_item)

                # 如果父节点（如 Cookies 或 History）没有子节点
                if data_item.childCount() == 0:
                    data_item.setFlags(Qt.NoItemFlags)  # 删除复选框
                    data_item.setText(0, f"{data_item.text(0)} (已清空)")  # 标记为已清空
                    data_item.setForeground(0, QColor("gray"))  # 设置文本颜色为灰色

    def handle_scan_system(self):
        """扫描系统垃圾文件并显示在界面中"""
        self.statusBar().showMessage("正在扫描系统垃圾文件...")
        self.treeWidget_system_info.clear()
        results = self.system_cleaner.scan_system()

        for result in results:
            # 顶层：垃圾分类名称
            category_item = QTreeWidgetItem(self.treeWidget_system_info)
            category_item.setText(0, result['category'])
            category_item.setCheckState(0, Qt.Unchecked)

            # 遍历垃圾文件
            for file in result['files']:
                file_item = QTreeWidgetItem(category_item)
                file_item.setText(0, f"{file['path']} ({file['size'] / 1024:.2f} KB)")
                file_item.setCheckState(0, Qt.Unchecked)

            # 如果分类没有子项，移除复选框
            if not result['files']:
                category_item.setFlags(Qt.NoItemFlags)

        self.statusBar().showMessage("扫描完成")


    def handle_scan_system(self):
        """扫描系统垃圾文件并显示在界面中"""
        self.statusBar().showMessage("正在扫描系统垃圾文件...")
        self.treeWidget_system_info.clear()
        results = self.system_cleaner.scan_system()

        for result in results:
            # 顶层：垃圾分类名称
            category_item = QTreeWidgetItem(self.treeWidget_system_info)
            category_item.setText(0, result['category'])
            category_item.setCheckState(0, Qt.Unchecked)
            category_item.setFlags(category_item.flags() | Qt.ItemIsTristate | Qt.ItemIsUserCheckable)

            # 遍历垃圾文件
            for file in result['files']:
                file_item = QTreeWidgetItem(category_item)
                file_item.setText(0, f"{file['path']} ({file['size'] / 1024:.2f} KB)")
                file_item.setCheckState(0, Qt.Unchecked)

            # 如果分类没有子项，移除复选框
            if not result['files']:
                category_item.setFlags(Qt.NoItemFlags)

        self.statusBar().showMessage("扫描完成")

    def handle_clean_system(self):
        """清理选中的系统垃圾文件并更新界面"""
        selected_files = self.get_selected_system_files()
        if not selected_files:
            QMessageBox.information(self, "提示", "未选择任何记录清理")
            return

        try:
            self.system_cleaner.delete_files(selected_files)
            QMessageBox.information(self, "清理完成", "选中记录已清理")
            self.remove_cleaned_system_items(selected_files)  # 更新界面
            self.statusBar().showMessage("清理完成")
        except Exception as e:
            QMessageBox.critical(self, "清理失败", f"清理过程中发生错误: {e}")

    def get_selected_system_files(self):
        """获取用户在 TreeWidget 中选择的系统垃圾文件"""
        selected_files = []
        root = self.treeWidget_system_info.invisibleRootItem()
        for i in range(root.childCount()):
            category_item = root.child(i)
            for j in range(category_item.childCount()):
                file_item = category_item.child(j)
                if file_item.checkState(0) == Qt.Checked:
                    selected_files.append(file_item.text(0).split(" (")[0])  # 提取文件路径
        return selected_files

    def remove_cleaned_system_items(self, cleaned_files):
        """从 TreeWidget 中移除已清理的条目"""
        root = self.treeWidget_system_info.invisibleRootItem()
        for i in range(root.childCount()):
            category_item = root.child(i)
            for j in range(category_item.childCount() - 1, -1, -1):  # 倒序遍历子节点
                file_item = category_item.child(j)
                if file_item.text(0).split(" (")[0] in cleaned_files:
                    category_item.removeChild(file_item)

            # 如果分类没有子节点，移除复选框
            if category_item.childCount() == 0:
                category_item.setFlags(Qt.NoItemFlags)
                category_item.setText(0, f"{category_item.text(0)} (已清空)")

    def handle_checkBox_state(self, category_name, state):
        """处理复选框状态与对应分类同步"""
        root = self.treeWidget_system_info.invisibleRootItem()
        for i in range(root.childCount()):
            category_item = root.child(i)
            if category_item.text(0) == category_name:
                self.set_category_check_state(category_item, state)
                break

    def set_category_check_state(self, category_item, state):
        """设置分类及其子项的复选框状态"""
        for i in range(category_item.childCount()):
            category_item.child(i).setCheckState(0, Qt.Checked if state == Qt.Checked else Qt.Unchecked)

    def handle_item_changed(self, item, column):
        """当子项或父项复选框状态改变时，自动同步状态"""
        if item is None:
            return

        parent = item.parent()
        if parent is None:  # 如果是顶层项，更新所有子项
            for i in range(item.childCount()):
                child = item.child(i)
                child.setCheckState(0, item.checkState(0))
        else:  # 如果是子项，更新父项的三态
            self.update_parent_check_state(parent)

    def update_parent_check_state(self, parent_item):
        """根据子项的状态更新父项复选框的三态"""
        checked_count = 0
        unchecked_count = 0
        for i in range(parent_item.childCount()):
            state = parent_item.child(i).checkState(0)
            if state == Qt.Checked:
                checked_count += 1
            elif state == Qt.Unchecked:
                unchecked_count += 1

        if checked_count == parent_item.childCount():
            parent_item.setCheckState(0, Qt.Checked)
        elif unchecked_count == parent_item.childCount():
            parent_item.setCheckState(0, Qt.Unchecked)
        else:
            parent_item.setCheckState(0, Qt.PartiallyChecked)

        # 同步顶部复选框
        if parent_item.text(0) == "Temporary Files":
            self.checkBox_temp.blockSignals(True)
            self.checkBox_temp.setCheckState(parent_item.checkState(0))
            self.checkBox_temp.blockSignals(False)
        elif parent_item.text(0) == "System Logs":
            self.checkBox_logs.blockSignals(True)
            self.checkBox_logs.setCheckState(parent_item.checkState(0))
            self.checkBox_logs.blockSignals(False)

    def handle_scan_network(self):
        """扫描网络配置并显示到 UI"""
        self.statusBar().showMessage("正在扫描网络配置...")
        self.treeWidget_network_info.clear()

        results = self.network_cleaner.scan_network_configs()
        for result in results:
            # 顶层：配置文件名称
            config_item = QTreeWidgetItem(self.treeWidget_network_info)
            config_item.setText(0, f"{result['name']} ({result['path']})")
            config_item.setCheckState(0, Qt.Unchecked)
            config_item.setData(0, Qt.UserRole, result['path'])

            # 添加详细配置信息
            for line in result['details']:
                detail_item = QTreeWidgetItem(config_item)
                detail_item.setText(0, line)
                detail_item.setFlags(Qt.ItemIsEnabled)  # 配置详情不可选

            # 如果是未使用的配置，标记为可选择
            if result['status'] == "unused":
                config_item.setCheckState(0, Qt.Unchecked)

        self.statusBar().showMessage("网络配置扫描完成")

    def handle_clear_network(self):
        """清理所选网络配置"""
        selected_configs = self.get_selected_network_configs()
        if not selected_configs:
            QMessageBox.information(self, "提示", "未选择任何网络配置文件清理")
            return

        try:
            self.network_cleaner.delete_network_configs(selected_configs)
            QMessageBox.information(self, "清理完成", "选中的网络配置已清理")
            self.remove_cleared_network_items(selected_configs)  # 更新 UI
            self.statusBar().showMessage("网络配置清理完成")
        except Exception as e:
            QMessageBox.critical(self, "清理失败", f"清理过程中发生错误: {e}")

    def handle_checkbox_unuse(self, state):
        """当勾选未使用配置复选框时，自动选择所有未使用的配置"""
        root = self.treeWidget_network_info.invisibleRootItem()
        for i in range(root.childCount()):
            config_item = root.child(i)
            if "unused" in config_item.text(0).lower():
                config_item.setCheckState(0, Qt.Checked if state == Qt.Checked else Qt.Unchecked)

    def get_selected_network_configs(self):
        """获取用户在 TreeWidget 中选择的网络配置文件"""
        selected_configs = []
        root = self.treeWidget_network_info.invisibleRootItem()
        for i in range(root.childCount()):
            config_item = root.child(i)
            if config_item.checkState(0) == Qt.Checked:
                selected_configs.append(config_item.data(0, Qt.UserRole))  # 获取文件路径
        return selected_configs

    def remove_cleared_network_items(self, cleared_configs):
        """从 TreeWidget 中移除已清理的网络配置"""
        root = self.treeWidget_network_info.invisibleRootItem()
        for i in range(root.childCount() - 1, -1, -1):  # 倒序遍历顶层节点
            config_item = root.child(i)
            if config_item.data(0, Qt.UserRole) in cleared_configs:
                root.removeChild(config_item)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = PrivClearApp()
    main_window.show()
    sys.exit(app.exec_())

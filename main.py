import json
import os
import re
from datetime import datetime, timedelta, date
import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import Calendar  # 日历控件
import uuid  # 生成唯一ID
import pytz  # 时区支持（当前代码中未使用）


# 任务类，存储单个任务的所有属性和行为
class Task:
    def __init__(self, description, start_date=None, due_date=None, completed=False, task_id=None, created_at=None,
                 is_multi=False, multi_index=None, multi_total=None, group_id=None, importance=1, details=""):
        # 任务唯一标识符，如果未提供则生成新的UUID
        self.id = task_id or str(uuid.uuid4())
        # 任务描述文本
        self.description = description
        # 任务详情文本
        self.details = details
        # 对于多任务，存储所属组的ID；单任务则为None
        self.group_id = group_id or (str(uuid.uuid4()) if is_multi else None)
        # 确保日期类型为date（而非datetime）
        self.start_date = start_date.date() if isinstance(start_date, datetime) else start_date
        self.due_date = due_date.date() if isinstance(due_date, datetime) else due_date
        # 任务完成状态
        self.completed = completed
        # 任务创建时间
        self.created_at = created_at or datetime.now()
        # 多任务相关属性
        self.is_multi = is_multi  # 是否为多任务组的一部分
        self.multi_index = multi_index  # 在多任务组中的序号
        self.multi_total = multi_total  # 多任务组的总任务数
        # 任务重要性等级（1-5）
        self.importance = importance

    # 将任务对象转换为字典格式（用于JSON序列化）
    def to_dict(self):
        return {
            "id": self.id,
            "description": self.description,
            "details": self.details,
            "start_date": self.start_date.strftime("%Y-%m-%d") if self.start_date else None,
            "due_date": self.due_date.strftime("%Y-%m-%d") if self.due_date else None,
            "completed": self.completed,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "is_multi": self.is_multi,
            "multi_index": self.multi_index,
            "multi_total": self.multi_total,
            "group_id": self.group_id,
            "importance": self.importance
        }

    # 类方法：从字典创建任务对象（用于JSON反序列化）
    @classmethod
    def from_dict(cls, data):
        # 解析日期字符串为date对象
        start_date = datetime.strptime(data["start_date"], "%Y-%m-%d").date() if data["start_date"] else None
        due_date = datetime.strptime(data["due_date"], "%Y-%m-%d").date() if data["due_date"] else None
        created_at = datetime.strptime(data["created_at"], "%Y-%m-%d %H:%M:%S") if data["created_at"] else None

        # 获取多任务相关属性（带默认值）
        is_multi = data.get("is_multi", False)
        multi_index = data.get("multi_index")
        multi_total = data.get("multi_total")
        group_id = data.get("group_id")
        importance = data.get("importance", 1)  # 默认为1（最低重要性）
        details = data.get("details", "")  # 获取任务详情，默认为空

        # 创建并返回任务实例
        return cls(
            data["description"],
            start_date,
            due_date,
            data["completed"],
            data["id"],
            created_at,
            is_multi,
            multi_index,
            multi_total,
            group_id=group_id,
            importance=importance,
            details=details
        )


# 任务管理类，处理任务的增删改查和持久化存储
class TaskManager:
    def __init__(self, filename='tasks.json'):
        self.filename = filename  # 任务存储文件
        self.tasks = []  # 内存中的任务列表
        self.load_tasks()  # 初始化时加载任务



    # 从文件加载任务数据
    def load_tasks(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r') as f:
                    data = json.load(f)
                    # 将字典数据转换为Task对象
                    self.tasks = [Task.from_dict(task) for task in data]
            except:
                # 文件读取失败时使用空列表
                self.tasks = []
        else:
            self.tasks = []

    # 保存任务到文件
    def save_tasks(self):
        with open(self.filename, 'w') as f:
            # 将Task对象列表转换为字典列表
            json.dump([task.to_dict() for task in self.tasks], f, indent=2)

    # 添加单个任务
    def add_task(self, description, start_date, due_date, is_multi=False, multi_index=None, multi_total=None,
                 importance=1, details=""):
        # 创建新任务对象
        task = Task(description=description, start_date=start_date, due_date=due_date,
                    is_multi=is_multi, multi_index=multi_index, multi_total=multi_total,
                    importance=importance, details=details)
        # 添加到列表并保存
        self.tasks.append(task)
        self.save_tasks()
        return task

    # 添加多任务组（在起止日期范围内每天创建一个任务）
    # 添加多任务组（在起止日期范围内每天创建一个任务）
    def add_multiple_tasks(self, description, start_date, due_date, importance=1, details=""):
        # 生成唯一组ID（组内所有任务共享）
        group_id = str(uuid.uuid4())
        # 计算任务数量（天数）
        date_range = (due_date - start_date).days + 1

        tasks_added = []
        for i in range(date_range):
            # 计算当前任务日期
            current_date = start_date + timedelta(days=i)
            # 格式化任务描述（包含序号）
            task_desc = f"{description} ({i + 1}/{date_range})"
            # 创建任务对象
            task = Task(
                description=task_desc,
                start_date=current_date,
                due_date=current_date,
                is_multi=True,
                multi_index=i + 1,
                multi_total=date_range,
                group_id=group_id,
                importance=importance,  # 所有子任务使用相同重要性
                details=details  # 所有子任务共享相同的详情
            )
            self.tasks.append(task)
            tasks_added.append(task)

        self.save_tasks()
        return tasks_added

    # 编辑现有任务
    def edit_task(self, task_id, description, start_date, due_date, is_multi, multi_index=None, multi_total=None,
                  importance=1, details=""):
        for task in self.tasks:
            if task.id == task_id:
                # 更新任务属性
                task.description = description
                task.start_date = start_date.date() if isinstance(start_date, datetime) else start_date
                task.due_date = due_date.date() if isinstance(due_date, datetime) else due_date
                task.is_multi = is_multi
                task.multi_index = multi_index
                task.multi_total = multi_total
                task.importance = importance
                task.details = details  # 更新任务详情
                self.save_tasks()
                return True
        return False  # 未找到任务

    # 删除任务
    def delete_task(self, task_id):
        # 过滤掉指定ID的任务
        self.tasks = [task for task in self.tasks if task.id != task_id]
        self.save_tasks()

    # 切换任务完成状态
    def toggle_completion(self, task_id):
        for task in self.tasks:
            if task.id == task_id:
                task.completed = not task.completed
                self.save_tasks()
                return True
        return False

    # 获取特定日期的任务
    def get_tasks_by_date(self, target_date):
        # 无日期参数时返回所有任务
        if target_date is None:
            return list(self.tasks)

        # 统一为date类型
        target_date = target_date.date() if isinstance(target_date, datetime) else target_date

        results = []
        for task in self.tasks:
            # 跳过无起始日期的任务
            if task.start_date is None:
                continue

            if task.due_date is None:
                # 无截止日期：从起始日期开始的所有任务
                if target_date >= task.start_date:
                    results.append(task)
            else:
                # 有起止日期：检查目标日期是否在范围内
                if task.start_date <= target_date <= task.due_date:
                    results.append(task)

        return results

    # 获取今天的任务（便捷方法）
    def get_today_tasks(self):
        today = datetime.now().date()
        return self.get_tasks_by_date(today)

    # 获取分组后的任务（多任务组显示为单个代表任务）
    def get_all_tasks_grouped(self):
        grouped_tasks = []  # 结果列表
        seen_groups = set()  # 已处理的多任务组

        for task in self.tasks:
            # 单任务直接添加
            if not task.is_multi:
                grouped_tasks.append(task)
                continue

            # 检查多任务组是否已处理
            if task.group_id not in seen_groups:
                # 获取组内所有任务
                group_tasks = [t for t in self.tasks if t.group_id == task.group_id]

                # 计算组的起始和截止日期
                start_dates = [t.start_date for t in group_tasks if t.start_date]
                due_dates = [t.due_date for t in group_tasks if t.due_date]
                overall_start = min(start_dates) if start_dates else None
                overall_due = max(due_dates) if due_dates else None

                # 使用第一个任务的重要性
                group_importance = group_tasks[0].importance if group_tasks else 1

                # 移除描述中的序号
                base_description = re.sub(r' \(\d+/\d+\)$', '', group_tasks[0].description)

                # 检查所有子任务是否完成
                all_completed = all(t.completed for t in group_tasks)

                # 创建代表整个组的任务
                group_task = Task(
                    description=f"{base_description} (共{len(group_tasks)}个子任务)",
                    start_date=overall_start,
                    due_date=overall_due,
                    completed=all_completed,
                    group_id=task.group_id,
                    is_multi=True,
                    importance=group_importance
                )
                group_task.id = task.group_id  # 使用组ID作为标识
                group_task.is_group_task = True  # 标记为组任务

                grouped_tasks.append(group_task)
                seen_groups.add(task.group_id)  # 标记为已处理

        return grouped_tasks


# 主应用程序类，实现GUI界面
class TaskManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title('JIANNAN Schedule')
        self.root.geometry('900x600')
        self.root.resizable(True, True)

        # 窗口居中
        self.center_window(self.root)
        self.root.update_idletasks()  # 确保窗口位置已更新

        # 初始化任务管理器
        self.manager = TaskManager()
        self.current_date = datetime.now()  # 当前显示日期

        # 排序设置
        self.sort_column = 'importance'  # 默认按重要性排序
        self.sort_reverse = True  # 从高到低排序
        self.displayed_tasks = []  # 当前显示的任务

        # 在 __init__ 中初始化 progress_var
        self.progress_var = tk.DoubleVar(value=0.0)

        # 计时器属性初始化
        self.timer_running = False
        self.elapsed_time = 0
        self.study_records = []
        self.current_event_name = None  # 新增：当前学习事件名称
        self.load_study_records()  # 加载学习记录

        # 创建界面组件
        self.create_widgets()

        # 设置自动保存（每30秒）
        self.root.after(30000, self.auto_save)

        # 初始显示今天的任务
        self.show_today_tasks()

    # 窗口居中方法
    def center_window(self, window, parent=None):
        """将窗口居中显示，相对于父窗口或屏幕"""
        window.update_idletasks()
        width = window.winfo_width()
        height = window.winfo_height()

        if parent:
            # 相对于父窗口居中
            parent_x = parent.winfo_rootx()
            parent_y = parent.winfo_rooty()
            parent_width = parent.winfo_width()
            parent_height = parent.winfo_height()

            x = parent_x + (parent_width - width) // 2
            y = parent_y + (parent_height - height) // 2
        else:
            # 相对于屏幕居中
            screen_width = window.winfo_screenwidth()
            screen_height = window.winfo_screenheight()
            x = (screen_width // 2) - (width // 2)
            y = (screen_height // 2) - (height // 2)

        window.geometry(f'+{x}+{y}')

    # 自动保存方法
    def auto_save(self):
        self.manager.save_tasks()
        self.root.after(30000, self.auto_save)  # 递归调用实现定时器

    # 创建GUI组件
    def create_widgets(self):
        # 主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 左侧任务列表区域
        task_frame = ttk.LabelFrame(main_frame, text="任务列表")
        task_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5, side=tk.LEFT)

        # 任务树状视图（表格）
        self.task_tree = ttk.Treeview(task_frame,
                                      columns=('importance', 'task_name', 'start_date', 'due_date', 'status'),
                                      show='headings')

        # 设置列标题（带排序功能）
        self.task_tree.heading("importance", text="重要性", command=lambda: self.sort_tasks('importance'))
        self.task_tree.heading("task_name", text="任务名称", command=lambda: self.sort_tasks('task_name'))
        self.task_tree.heading("start_date", text="起始日期", command=lambda: self.sort_tasks('start_date'))
        self.task_tree.heading("due_date", text="截止日期", command=lambda: self.sort_tasks('due_date'))
        self.task_tree.heading("status", text="状态")

        # 设置列宽
        self.task_tree.column("importance", width=60, anchor=tk.CENTER)
        self.task_tree.column("task_name", width=220, stretch=tk.YES)
        self.task_tree.column("start_date", width=100, anchor=tk.CENTER)
        self.task_tree.column("due_date", width=100, anchor=tk.CENTER)
        self.task_tree.column("status", width=80, anchor=tk.CENTER)

        # 滚动条
        scrollbar = ttk.Scrollbar(task_frame, orient=tk.VERTICAL, command=self.task_tree.yview)
        self.task_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.task_tree.pack(fill=tk.BOTH, expand=True)

        # 事件绑定
        self.task_tree.bind("<<TreeviewSelect>>", self.on_task_select)
        self.task_tree.bind("<Double-1>", self.on_double_click)  # 双击编辑

        # 右键菜单
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="添加任务", command=self.add_task)
        self.context_menu.add_command(label="编辑任务", command=self.edit_task)
        self.context_menu.add_command(label="标记完成/未完成", command=self.toggle_completion)
        self.context_menu.add_command(label="删除任务", command=self.delete_task)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="显示全部任务", command=self.show_all_tasks)

        # 绑定右键菜单到任务树
        self.task_tree.bind("<Button-3>", self.show_context_menu)

        # 右侧控制面板
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)

        # 日期导航
        date_frame = ttk.LabelFrame(control_frame, text="日期导航")
        date_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(date_frame, text="今天", command=self.show_today_tasks).pack(side=tk.LEFT, padx=2)
        ttk.Button(date_frame, text="前一天", command=self.show_previous_day).pack(side=tk.LEFT, padx=2)
        ttk.Button(date_frame, text="后一天", command=self.show_next_day).pack(side=tk.LEFT, padx=2)

        # 日历控件
        self.cal = Calendar(control_frame, selectmode="day", date_pattern="y-mm-dd")
        self.cal.pack(padx=5, pady=5, fill=tk.X)
        self.cal.bind("<<CalendarSelected>>", self.on_cal_select)

        # 当前日期标签
        self.date_label = ttk.Label(control_frame, text="", font=("Arial", 10, "bold"))
        self.date_label.pack(pady=5)

        # 任务操作按钮
        btn_frame = ttk.LabelFrame(control_frame, text="任务操作")
        btn_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(btn_frame, text="添加任务", command=self.add_task).pack(fill=tk.X, padx=5, pady=2)
        ttk.Button(btn_frame, text="编辑任务", command=self.edit_task).pack(fill=tk.X, padx=5, pady=2)
        ttk.Button(btn_frame, text="标记完成/未完成", command=self.toggle_completion).pack(fill=tk.X, padx=5, pady=2)
        ttk.Button(btn_frame, text="删除任务", command=self.delete_task).pack(fill=tk.X, padx=5, pady=2)
        ttk.Button(btn_frame, text="显示全部任务", command=self.show_all_tasks).pack(fill=tk.X, padx=5, pady=2)

        # 搜索功能
        search_frame = ttk.Frame(control_frame)
        search_frame.pack(fill=tk.X, padx=5, pady=5)

        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        search_entry.bind("<KeyRelease>", self.search_tasks)  # 实时搜索

        ttk.Button(search_frame, text="搜索", command=self.search_tasks).pack(side=tk.RIGHT, padx=2)

        # 在底部添加计时学习功能
        timer_frame = ttk.Frame(self.root)
        timer_frame.pack(fill=tk.X, padx=10, pady=10, side=tk.BOTTOM)
        self.create_timer_widgets(timer_frame)

    def create_timer_widgets(self, parent):
        # 首先初始化进度条变量（如果尚未初始化）
        if not hasattr(self, 'progress_var'):
            self.progress_var = tk.DoubleVar(value=0.0)

        # 计时器显示
        self.timer_label = ttk.Label(parent, text="00:00:00", font=("Arial", 14, "bold"))
        self.timer_label.grid(row=0, column=0, padx=5, pady=5)

        # 控制按钮
        self.timer_button = ttk.Button(parent, text="开始学习", command=self.toggle_timer)
        self.timer_button.grid(row=0, column=1, padx=5, pady=5)

        ttk.Button(parent, text="重置", command=self.reset_timer).grid(row=0, column=2, padx=5, pady=5)

        # 学习记录
        ttk.Label(parent, text="学习记录:").grid(row=0, column=3, padx=(10, 0))
        self.record_label = ttk.Label(parent, text="0 次")
        self.record_label.grid(row=0, column=4, padx=(0, 10))

        # 学习目标
        self.goal_var = tk.StringVar(value="25")
        ttk.Label(parent, text="目标(分):").grid(row=0, column=5)
        goal_entry = ttk.Spinbox(parent, textvariable=self.goal_var, width=3, from_=5, to=120)
        goal_entry.grid(row=0, column=6, padx=5)

        # 在第7列添加显示详细记录的按钮
        ttk.Button(parent, text="详细记录", command=self.show_detailed_records).grid(row=0, column=7, padx=5)

        # 进度条（使用已初始化的 progress_var）
        progress_bar = ttk.Progressbar(parent, variable=self.progress_var, length=150)
        progress_bar.grid(row=0, column=8, padx=5)  # 放在第8列


        # 初始化学习记录
        self.study_records = []
        self.load_study_records()
        self.update_record_label()

    def toggle_timer(self):
        if not self.timer_running:
            # 弹出对话框让用户输入学习事件名称
            event_name = self.get_study_event_name()
            if event_name is None:  # 用户取消了输入
                return

            # 开始计时
            self.timer_running = True
            self.current_event_name = event_name  # 保存当前学习事件名称
            self.timer_button.config(text="停止学习")
            self.start_time = datetime.now()
            self.update_timer()
        else:
            # 停止计时
            self.timer_running = False
            self.timer_button.config(text="开始学习")
            end_time = datetime.now()
            duration = (end_time - self.start_time).total_seconds()
            self.record_study_session(duration, self.current_event_name)
            self.current_event_name = None  # 清空当前事件名称

    def get_study_event_name(self):
        # 创建对话框获取学习事件名称
        dialog = tk.Toplevel(self.root)
        dialog.title("学习事件名称")
        dialog.transient(self.root)
        dialog.grab_set()

        # 居中显示
        self.center_window(dialog, self.root)

        ttk.Label(dialog, text="请输入本次学习的事件名称:").pack(padx=10, pady=10)

        event_var = tk.StringVar()
        event_entry = ttk.Entry(dialog, textvariable=event_var, width=30)
        event_entry.pack(padx=10, pady=5)
        event_entry.focus()

        result = [None]  # 使用列表来存储结果，以便在内部函数中修改

        def on_ok():
            result[0] = event_var.get().strip()
            dialog.destroy()

        def on_cancel():
            dialog.destroy()

        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="确定", command=on_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="取消", command=on_cancel).pack(side=tk.LEFT, padx=5)

        self.root.wait_window(dialog)
        return result[0]

    def record_study_session(self, duration_seconds, event_name):
        # 记录学习会话
        record = {
            "id": str(uuid.uuid4()),  # 添加唯一ID
            "date": datetime.now().strftime("%Y-%m-%d"),
            "duration": duration_seconds,
            "event_name": event_name  # 保存事件名称
        }
        self.study_records.append(record)
        self.save_study_records()
        self.update_record_label()

    def update_timer(self):
        if self.timer_running:
            elapsed = (datetime.now() - self.start_time).total_seconds() + self.elapsed_time
            hours, remainder = divmod(int(elapsed), 3600)
            minutes, seconds = divmod(remainder, 60)
            self.timer_label.config(text=f"{hours:02d}:{minutes:02d}:{seconds:02d}")

            # 更新进度条
            goal_minutes = int(self.goal_var.get() or 25)
            progress = min(100.0, (elapsed / (goal_minutes * 60)) * 100)
            self.progress_var.set(progress)

            self.root.after(1000, self.update_timer)



    def reset_timer(self):
        self.timer_running = False
        self.elapsed_time = 0
        self.timer_label.config(text="00:00:00")
        self.progress_var.set(0.0)
        self.timer_button.config(text="开始学习")

    def load_study_records(self):
        if os.path.exists('study_records.json'):
            try:
                with open('study_records.json', 'r') as f:
                    records = json.load(f)
                    # 确保每条记录都有唯一ID
                    for record in records:
                        if 'id' not in record:
                            record['id'] = str(uuid.uuid4())
                    self.study_records = records
                    # 保存更新后的记录（确保ID被保存）
                    self.save_study_records()
            except:
                self.study_records = []
        else:
            self.study_records = []

    def save_study_records(self):
        with open('study_records.json', 'w') as f:
            json.dump(self.study_records, f, indent=2)


    def update_record_label(self):
        # 计算今日学习次数
        today = datetime.now().strftime("%Y-%m-%d")
        today_sessions = sum(1 for r in self.study_records if r["date"] == today)

        # 计算总学习时间（分钟）
        total_minutes = sum(r["duration"] for r in self.study_records) // 60

        self.record_label.config(text=f"今日: {today_sessions} 次 | 总计: {total_minutes} 分钟")

    # 添加显示详细学习记录的方法
    def show_detailed_records(self):
        # 创建新窗口
        detail_window = tk.Toplevel(self.root)
        detail_window.title("学习记录详情")
        detail_window.geometry("900x500")
        detail_window.transient(self.root)
        detail_window.grab_set()

        # 居中窗口
        self.center_window(detail_window, self.root)

        # 创建框架
        frame = ttk.Frame(detail_window)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 创建滚动条
        scrollbar = ttk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 创建树状视图显示记录
        tree = ttk.Treeview(frame, columns=("id", "date", "event_name", "duration", "minutes"),
                            show="headings", yscrollcommand=scrollbar.set)
        tree.pack(fill=tk.BOTH, expand=True)

        # 配置列
        tree.heading("id", text="ID")
        tree.heading("date", text="日期")
        tree.heading("event_name", text="事件名称")
        tree.heading("duration", text="持续时间(秒)")
        tree.heading("minutes", text="持续时间(分钟)")

        tree.column("id", width=120, stretch=False)
        tree.column("date", width=120)
        tree.column("event_name", width=200)
        tree.column("duration", width=120, anchor=tk.CENTER)
        tree.column("minutes", width=120, anchor=tk.CENTER)

        # 配置滚动条
        scrollbar.config(command=tree.yview)

        # 添加数据
        for record in self.study_records:
            minutes = round(record["duration"] / 60, 1)
            tree.insert("", "end", values=(
                record["id"],
                record["date"],
                record.get("event_name", "未命名"),
                int(record["duration"]),
                minutes
            ))

        # 添加编辑和删除按钮
        button_frame = ttk.Frame(detail_window)
        button_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Button(button_frame, text="编辑选中记录",
                   command=lambda: self.edit_study_record(tree, detail_window)).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="删除选中记录",
                   command=lambda: self.delete_study_record(tree, detail_window)).pack(side=tk.LEFT, padx=5)

        # 添加统计信息
        stats_frame = ttk.Frame(detail_window)
        stats_frame.pack(fill=tk.X, padx=10, pady=10)

        # 计算统计数据
        total_duration = sum(r["duration"] for r in self.study_records)
        total_minutes = total_duration / 60
        total_hours = total_minutes / 60

        # 今日数据
        today = datetime.now().strftime("%Y-%m-%d")
        today_records = [r for r in self.study_records if r["date"] == today]
        today_duration = sum(r["duration"] for r in today_records)
        today_minutes = today_duration / 60

        # 创建统计变量
        self.today_count_var = tk.StringVar(value=f"今日学习: {len(today_records)}次, {round(today_minutes, 1)}分钟")
        self.total_count_var = tk.StringVar(value=f"总学习次数: {len(self.study_records)}")
        self.total_time_var = tk.StringVar(
            value=f"总学习时间: {round(total_hours, 1)}小时 ({round(total_minutes, 1)}分钟)")

        # 添加统计标签
        ttk.Label(stats_frame, textvariable=self.today_count_var).grid(row=0, column=0, padx=10, sticky=tk.W)
        ttk.Label(stats_frame, textvariable=self.total_count_var).grid(row=0, column=1, padx=10, sticky=tk.W)
        ttk.Label(stats_frame, textvariable=self.total_time_var).grid(row=0, column=2, padx=10, sticky=tk.W)

        # 添加关闭按钮
        ttk.Button(detail_window, text="关闭", command=detail_window.destroy).pack(pady=10)

        # 绑定双击事件编辑记录
        tree.bind("<Double-1>", lambda e: self.edit_study_record(tree, detail_window))
    def edit_study_record(self, tree, parent_window):
        """编辑选中的学习记录"""
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请先选择一条记录")
            return

        # 获取选中的记录
        item = selected[0]
        values = tree.item(item, "values")
        record_id = values[0]  # 第一列现在是ID

        # 创建编辑对话框
        edit_dialog = tk.Toplevel(parent_window)
        edit_dialog.title("编辑学习记录")
        edit_dialog.transient(parent_window)
        edit_dialog.grab_set()

        # 居中显示
        self.center_window(edit_dialog, parent_window)

        # 查找要编辑的记录
        record_to_edit = None
        for record in self.study_records:
            if record['id'] == record_id:
                record_to_edit = record
                break

        if not record_to_edit:
            messagebox.showerror("错误", "未找到记录")
            edit_dialog.destroy()
            return

        # 创建表单
        ttk.Label(edit_dialog, text="日期 (YYYY-MM-DD):").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        date_var = tk.StringVar(value=record_to_edit["date"])
        date_entry = ttk.Entry(edit_dialog, textvariable=date_var, width=15)
        date_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(edit_dialog, text="事件名称:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        event_var = tk.StringVar(value=record_to_edit.get("event_name", "未命名"))
        event_entry = ttk.Entry(edit_dialog, textvariable=event_var, width=30)
        event_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(edit_dialog, text="持续时间(分钟):").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        minutes_var = tk.StringVar(value=str(round(record_to_edit["duration"] / 60, 1)))
        minutes_entry = ttk.Entry(edit_dialog, textvariable=minutes_var, width=10)
        minutes_entry.grid(row=2, column=1, padx=5, pady=5)

        # 保存按钮
        def save_changes():
            try:
                # 验证输入
                new_date = date_var.get().strip()
                new_event = event_var.get().strip()
                new_minutes = float(minutes_var.get().strip())

                if not new_date or not new_event:
                    messagebox.showwarning("警告", "日期和事件名称不能为空")
                    return

                # 验证日期格式
                datetime.strptime(new_date, "%Y-%m-%d")

                # 更新记录
                record_to_edit["date"] = new_date
                record_to_edit["event_name"] = new_event
                record_to_edit["duration"] = int(new_minutes * 60)  # 转换为秒

                # 保存到文件
                self.save_study_records()

                # 更新树状视图
                tree.item(item, values=(
                    record_to_edit["id"],
                    new_date,
                    new_event,
                    int(new_minutes * 60),
                    new_minutes
                ))

                # 更新统计信息
                self.update_statistics(parent_window)

                # 更新主窗口的统计标签
                self.update_record_label()

                edit_dialog.destroy()
                return

            except ValueError:
                messagebox.showerror("错误", "请输入有效的数字和日期格式(YYYY-MM-DD)")

        ttk.Button(edit_dialog, text="保存", command=save_changes).grid(row=3, column=0, padx=5, pady=10)
        ttk.Button(edit_dialog, text="取消", command=edit_dialog.destroy).grid(row=3, column=1, padx=5, pady=10)

    def delete_study_record(self, tree, parent_window):
        """删除选中的学习记录"""
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请先选择一条记录")
            return

        # 确认删除
        if not messagebox.askyesno("确认", "确定要删除这条记录吗？"):
            return

        # 获取选中的记录
        item = selected[0]
        values = tree.item(item, "values")
        record_id = values[0]  # 第一列现在是ID

        # 找到并删除记录
        for i, record in enumerate(self.study_records):
            if record["id"] == record_id:
                # 删除记录
                del self.study_records[i]

                # 保存到文件
                self.save_study_records()

                # 从树状视图中删除
                tree.delete(item)

                # 更新统计信息
                self.update_statistics(parent_window)

                # 更新主窗口的统计标签
                self.update_record_label()

                return

        messagebox.showerror("错误", "未找到记录")

    def update_statistics(self, parent_window):
        """更新统计信息"""
        # 计算统计数据
        total_duration = sum(r["duration"] for r in self.study_records)
        total_minutes = total_duration / 60
        total_hours = total_minutes / 60

        # 今日数据
        today = datetime.now().strftime("%Y-%m-%d")
        today_records = [r for r in self.study_records if r["date"] == today]
        today_duration = sum(r["duration"] for r in today_records)
        today_minutes = today_duration / 60

        # 更新统计变量
        self.today_count_var.set(f"今日学习: {len(today_records)}次, {round(today_minutes, 1)}分钟")
        self.total_count_var.set(f"总学习次数: {len(self.study_records)}")
        self.total_time_var.set(f"总学习时间: {round(total_hours, 1)}小时 ({round(total_minutes, 1)}分钟)")

    # 任务排序方法
    def sort_tasks(self, column):
        if not self.displayed_tasks:
            return

        # 切换排序方向
        if self.sort_column == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_reverse = False
        self.sort_column = column

        # 定义排序键
        key_map = {
            'importance': lambda t: t.importance,
            'task_name': lambda t: t.description.lower(),
            'start_date': lambda t: t.start_date or date.min,
            'due_date': lambda t: t.due_date or date.min
        }
        key = key_map[column]
        sorted_list = sorted(self.displayed_tasks, key=key, reverse=self.sort_reverse)
        self.display_tasks(sorted_list)  # 显示排序后任务

    # 更新日期标签
    def update_date_label(self):
        if self.current_date is None:
            text = "全部任务列表"
        else:
            text = self.current_date.strftime("%Y年%m月%d日 任务列表")
        self.date_label.config(text=text)

    # 显示右键菜单
    def show_context_menu(self, event):
        selected = self.task_tree.identify_row(event.y)

        # 根据是否有选中项设置菜单项状态
        state = tk.NORMAL if selected else tk.DISABLED
        self.context_menu.entryconfig(1, state=state)  # 编辑任务
        self.context_menu.entryconfig(2, state=state)  # 标记完成
        self.context_menu.entryconfig(3, state=state)  # 删除任务

        # 显示菜单
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    # 显示今天任务
    def show_today_tasks(self):
        self.current_date = datetime.now()
        self.update_date_label()
        self.display_tasks(self.manager.get_today_tasks())
        self.cal.selection_set(self.current_date.date())  # 高亮日历中的今天

    # 显示前一天任务
    def show_previous_day(self):
        self.current_date -= timedelta(days=1)
        self.update_date_label()
        self.display_tasks(self.manager.get_tasks_by_date(self.current_date))
        self.cal.selection_set(self.current_date.date())

    # 显示后一天任务
    def show_next_day(self):
        self.current_date += timedelta(days=1)
        self.update_date_label()
        self.display_tasks(self.manager.get_tasks_by_date(self.current_date))
        self.cal.selection_set(self.current_date.date())

    # 日历选择事件处理
    def on_cal_select(self, event):
        selected_date = self.cal.selection_get()
        self.current_date = datetime.combine(selected_date, datetime.min.time())
        self.update_date_label()
        self.display_tasks(self.manager.get_tasks_by_date(self.current_date))

    # 在界面中显示任务列表
    def display_tasks(self, tasks):
        # 清空当前显示
        self.task_tree.delete(*self.task_tree.get_children())

        # 任务去重（防止重复显示）
        unique = {t.id: t for t in tasks}
        deduped_tasks = list(unique.values())
        self.displayed_tasks = deduped_tasks

        # 应用当前排序
        if self.sort_column:
            key_map = {
                'importance': lambda t: t.importance,
                'task_name': lambda t: t.description.lower(),
                'start_date': lambda t: t.start_date or date.min,
                'due_date': lambda t: t.due_date or date.min
            }
            key = key_map[self.sort_column]
            deduped_tasks = sorted(deduped_tasks, key=key, reverse=self.sort_reverse)

        # 添加任务到树状视图
        for task in deduped_tasks:
            # 确定任务描述显示方式
            if hasattr(task, 'is_group_task'):
                display_desc = task.description  # 组任务
            elif task.is_multi:
                display_desc = task.description  # 多任务组中的单个任务
            else:
                display_desc = task.description  # 普通任务

            # 格式化日期
            start = task.start_date.strftime("%Y-%m-%d") if task.start_date else "无起始日期"
            due = task.due_date.strftime("%Y-%m-%d") if task.due_date else "无截止日期"
            status = "已完成" if task.completed else "未完成"

            # 用星号表示重要性（★ = 已选，☆ = 未选）
            importance_stars = "★" * task.importance + "☆" * (5 - task.importance)

            # 插入到树状视图
            self.task_tree.insert(
                "", "end", iid=task.id,
                values=(importance_stars, display_desc, start, due, status),
                tags=("completed" if task.completed else "pending",)
            )

        # 设置标签样式（已完成灰色，未完成黑色）
        self.task_tree.tag_configure("completed", foreground="gray")
        self.task_tree.tag_configure("pending", foreground="black")

    # 显示所有任务（分组显示）
    def show_all_tasks(self):
        self.current_date = None
        grouped_tasks = self.manager.get_all_tasks_grouped()
        self.display_tasks(grouped_tasks)
        self.update_date_label()

    # 任务搜索功能
    def search_tasks(self, event=None):
        query = self.search_var.get().lower()
        if not query:
            self.show_today_tasks()  # 空搜索显示今天任务
            return

        # 过滤匹配任务
        results = [task for task in self.manager.tasks
                   if query in task.description.lower()]
        self.display_tasks(results)
        self.date_label.config(text=f"搜索: '{query}' (找到{len(results)}个任务)")

    # 获取当前选中的任务
    def get_selected_task(self):
        selected = self.task_tree.selection()
        if not selected:
            return None
        task_id = selected[0]

        # 首先检查当前显示的任务列表（包含组代表任务）
        for task in self.displayed_tasks:
            if task.id == task_id:
                return task

        # 如果未找到，再检查原始任务列表
        for task in self.manager.tasks:
            if task.id == task_id:
                # 多任务子任务返回组代表
                if task.is_multi:
                    return self.get_group_representative(task.group_id)
                return task

        return None

    # 获取多任务组的代表任务
    def get_group_representative(self, group_id):
        group_tasks = [t for t in self.manager.tasks if t.group_id == group_id]
        if not group_tasks:
            return None

        # 提取基础描述（移除序号）
        base_description = re.sub(r' \(\d+/\d+\)$', '', group_tasks[0].description)

        # 创建代表任务
        group_task = Task(
            description=f"{base_description} (共{len(group_tasks)}个子任务)",
            start_date=min(t.start_date for t in group_tasks),
            due_date=max(t.due_date for t in group_tasks),
            completed=all(t.completed for t in group_tasks),
            group_id=group_id,
            is_multi=True,
            importance=group_tasks[0].importance
        )
        group_task.id = group_id  # 使用组ID作为标识
        group_task.is_group_task = True  # 标记为组任务
        group_task.created_at = min(t.created_at for t in group_tasks)  # 添加创建时间

        return group_task

    # 任务选择事件（当前无操作）
    def on_task_select(self, event):
        pass

    # 双击任务编辑
    def on_double_click(self, event):
        self.edit_task()

    # 添加任务入口
    def add_task(self):
        self.open_task_dialog()

    # 编辑任务入口
    def edit_task(self):
        task = self.get_selected_task()
        if task:
            self.open_task_dialog(task)
        else:
            messagebox.showwarning("警告", "请先选择一个任务")

    # 打开任务编辑对话框
    # 打开任务编辑对话框
    def open_task_dialog(self, task=None):
        dialog = tk.Toplevel(self.root)
        dialog.title("编辑任务" if task else "添加任务")
        dialog.transient(self.root)
        dialog.grab_set()  # 模态对话框

        # 居中显示
        self.center_window(dialog, self.root)

        # 任务描述输入
        ttk.Label(dialog, text="任务描述:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)

        # 如果是多任务组代表任务，去除后缀
        if task and hasattr(task, 'is_group_task'):
            base_description = task.description.split(' (共')[0]  # 去除后缀
            description_var = tk.StringVar(value=base_description)
        else:
            description_var = tk.StringVar(value=task.description if task else "")

        description_entry = ttk.Entry(dialog, textvariable=description_var, width=40)
        description_entry.grid(row=0, column=1, columnspan=3, padx=5, pady=5, sticky=tk.W)
        description_entry.focus()

        # 任务详情输入 - 新增部分
        ttk.Label(dialog, text="任务详情:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.NW)
        details_text = tk.Text(dialog, width=40, height=5)
        details_text.grid(row=1, column=1, columnspan=3, padx=5, pady=5, sticky=tk.W)

        # 如果有任务详情，填充到文本框中
        if task and task.details:
            details_text.insert("1.0", task.details)

        # 起始日期输入
        ttk.Label(dialog, text="起始日期:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        start_date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        start_date_entry = ttk.Entry(dialog, textvariable=start_date_var, width=15)
        start_date_entry.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)

        # 截止日期输入
        ttk.Label(dialog, text="截止日期:").grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)
        due_date_var = tk.StringVar()
        due_date_entry = ttk.Entry(dialog, textvariable=due_date_var, width=15)
        due_date_entry.grid(row=3, column=1, padx=5, pady=5, sticky=tk.W)

        # 日期选择器辅助函数
        def open_calendar(entry_var, row, parent):
            cal_dialog = tk.Toplevel(dialog)
            cal_dialog.title("选择日期")
            cal = Calendar(cal_dialog, selectmode="day", date_pattern="y-mm-dd")
            cal.pack(padx=10, pady=10)

            def set_date():
                entry_var.set(cal.get_date())
                cal_dialog.destroy()

            ttk.Button(cal_dialog, text="确定", command=set_date).pack(pady=5)
            self.center_window(cal_dialog, parent)

        # 起始日期选择按钮
        ttk.Button(dialog, text="选择",
                   command=lambda: open_calendar(start_date_var, 2, dialog)).grid(
            row=2, column=2, padx=5, pady=5, sticky=tk.W)

        # 截止日期选择按钮
        ttk.Button(dialog, text="选择",
                   command=lambda: open_calendar(due_date_var, 3, dialog)).grid(
            row=3, column=2, padx=5, pady=5, sticky=tk.W)

        # 设置编辑时的日期值
        if task:
            if task.start_date:
                start_date_var.set(task.start_date.strftime("%Y-%m-%d"))
            if task.due_date:
                due_date_var.set(task.due_date.strftime("%Y-%m-%d"))

        # 任务模式选择（单任务/多任务）
        task_mode = tk.IntVar(value=1)  # 1=单任务, 2=多任务
        if task:
            task_mode.set(2 if task.is_multi else 1)
        else:
            task_mode.set(1)

        # 模式选择框架
        mode_frame = ttk.Frame(dialog)
        mode_frame.grid(row=4, column=0, columnspan=4, padx=5, pady=5, sticky=tk.W)

        ttk.Label(mode_frame, text="任务模式:").pack(side=tk.LEFT)
        ttk.Radiobutton(mode_frame, text="单个任务（起止日期）", variable=task_mode, value=1).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(mode_frame, text="多个任务（每天一个）", variable=task_mode, value=2).pack(side=tk.LEFT, padx=5)

        # 重要性选择
        ttk.Label(dialog, text="重要性:").grid(row=5, column=0, padx=5, pady=5, sticky=tk.W)
        importance_var = tk.IntVar(value=task.importance if task else 1)
        importance_combo = ttk.Combobox(dialog, textvariable=importance_var, width=8)
        importance_combo['values'] = [1, 2, 3, 4, 5]
        importance_combo.state(['readonly'])  # 防止输入
        importance_combo.grid(row=5, column=1, padx=5, pady=5, sticky=tk.W)
        ttk.Label(dialog, text="(1-5星, 5星为最高)").grid(row=5, column=2, padx=5, pady=5, sticky=tk.W)

        # 按钮框架
        btn_frame = ttk.Frame(dialog)
        btn_frame.grid(row=6, column=0, columnspan=4, pady=10)

        # 保存任务逻辑
        def save_task():
            # 验证输入
            description = description_var.get().strip()
            if not description:
                messagebox.showwarning("警告", "任务描述不能为空")
                return

            # 获取任务详情
            details = details_text.get("1.0", tk.END).strip()

            # 解析日期
            start_date = datetime.strptime(start_date_var.get(), "%Y-%m-%d") if start_date_var.get().strip() else None
            due_date = datetime.strptime(due_date_var.get(), "%Y-%m-%d") if due_date_var.get().strip() else None

            importance = importance_var.get()
            if not 1 <= importance <= 5:
                messagebox.showwarning("警告", "重要性必须是1-5之间的整数")
                return

            # 验证日期逻辑
            if start_date and due_date and start_date > due_date:
                messagebox.showwarning("警告", "起始日期不能晚于截止日期")
                return

            # 处理多任务模式
            if task_mode.get() == 2:  # 多任务
                if not start_date or not due_date:
                    messagebox.showwarning("警告", "在多个任务模式下，起始日期和截止日期都不能为空")
                    return

                if (due_date - start_date).days < 0:
                    messagebox.showwarning("警告", "截止日期不能早于起始日期")
                    return

                # 编辑时删除原组任务
                if task:
                    # 获取组ID（组任务或子任务）
                    delete_group_id = task.group_id if task.group_id else task.id
                    # 删除组内所有任务
                    for t in [t for t in self.manager.tasks if t.group_id == delete_group_id]:
                        self.manager.delete_task(t.id)

                # 添加新多任务组
                self.manager.add_multiple_tasks(
                    description,
                    start_date.date(),
                    due_date.date(),
                    importance,
                    details
                )
            else:  # 单任务模式
                if task:
                    # 更新现有任务
                    task.description = description
                    task.details = details
                    task.start_date = start_date.date() if start_date else None
                    task.due_date = due_date.date() if due_date else None
                    task.is_multi = False
                    task.multi_index = None
                    task.multi_total = None
                    task.importance = importance
                    self.manager.save_tasks()
                else:
                    # 添加新任务
                    self.manager.add_task(
                        description,
                        start_date.date() if start_date else None,
                        due_date.date() if due_date else None,
                        importance=importance,
                        details=details
                    )

            # 刷新显示并关闭对话框
            self.display_tasks(self.manager.get_tasks_by_date(self.current_date))
            dialog.destroy()

        # 对话框按钮
        ttk.Button(btn_frame, text="保存", command=save_task).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="取消", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    # 切换任务完成状态
    def toggle_completion(self):
        selected = self.task_tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请先选择一个任务")
            return

        task_id = selected[0]
        task = self.get_selected_task()

        # 处理组任务
        if task and hasattr(task, 'is_group_task'):
            # 获取组内所有任务
            group_tasks = [t for t in self.manager.tasks if t.group_id == task.group_id]

            # 确定新的完成状态（取反）
            new_completed_state = not all(t.completed for t in group_tasks)

            # 更新所有子任务
            for t in group_tasks:
                t.completed = new_completed_state
            self.manager.save_tasks()
            success = True
        else:
            # 处理单个任务
            success = self.manager.toggle_completion(task_id)

        if success:
            # 刷新显示
            tasks = self.manager.get_tasks_by_date(
                self.current_date) if self.current_date else self.manager.get_all_tasks_grouped()
            self.display_tasks(tasks)
        else:
            messagebox.showwarning("警告", "任务状态切换失败")

    # 删除任务
    def delete_task(self):
        task = self.get_selected_task()
        if not task:
            messagebox.showwarning("警告", "请先选择一个任务")
            return

        # 多任务组处理
        if task.is_multi:
            # 获取组内所有任务
            group_tasks = [t for t in self.manager.tasks if t.group_id == task.group_id]

            confirm = messagebox.askyesno(
                "确认删除",
                f"这是一个包含{len(group_tasks)}个子任务的任务组\n"
                f"确定要删除整个'{task.description.split(' (')[0]}'任务组吗?"
            )
            if confirm:
                for t in group_tasks:
                    self.manager.delete_task(t.id)
        else:  # 单任务处理
            confirm = messagebox.askyesno(
                "确认",
                f"确定要删除任务 '{task.description}' 吗?"
            )
            if confirm:
                self.manager.delete_task(task.id)

        # 刷新显示
        tasks = self.manager.get_tasks_by_date(self.current_date) if self.current_date else self.manager.tasks
        self.display_tasks(tasks)


# 程序入口
if __name__ == '__main__':
    root = tk.Tk()
    app = TaskManagerApp(root)
    root.mainloop()
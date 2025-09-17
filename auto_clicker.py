#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动点击程序
支持Windows和Mac系统的自动鼠标点击工具
"""

import tkinter as tk
from tkinter import ttk, messagebox
import pyautogui
import threading
import time
import random
import platform
import sys
from PIL import Image, ImageTk, ImageDraw
import numpy as np

class AreaSelector:
    """屏幕区域选择器"""
    
    def __init__(self, callback):
        self.callback = callback
        self.start_x = None
        self.start_y = None
        self.end_x = None
        self.end_y = None
        self.selecting = False
        
    def select_area(self):
        """开始选择屏幕区域"""
        # 先截取当前屏幕
        screenshot = pyautogui.screenshot()
        
        # 创建全屏窗口
        self.root = tk.Toplevel()
        self.root.attributes('-fullscreen', True)
        self.root.attributes('-topmost', True)
        
        # 获取屏幕尺寸
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # 调整截图大小以匹配屏幕
        screenshot = screenshot.resize((screen_width, screen_height), Image.Resampling.LANCZOS)
        
        # 创建半透明遮罩
        overlay = Image.new('RGBA', (screen_width, screen_height), (0, 0, 0, 100))
        
        # 合成图像：截图 + 半透明遮罩
        combined = Image.alpha_composite(screenshot.convert('RGBA'), overlay)
        
        # 转换为tkinter可用的图像
        self.bg_image = ImageTk.PhotoImage(combined)
        
        # 创建画布
        self.canvas = tk.Canvas(
            self.root, 
            width=screen_width, 
            height=screen_height,
            highlightthickness=0
        )
        self.canvas.pack()
        
        # 设置背景图像
        self.canvas.create_image(0, 0, anchor="nw", image=self.bg_image)
        
        # 添加提示文字（带背景框）
        text_x = screen_width // 2
        text_y = 50
        
        # 创建文字背景
        self.canvas.create_rectangle(
            text_x - 200, text_y - 20,
            text_x + 200, text_y + 20,
            fill="black", outline="red", width=2,
            stipple="gray50"
        )
        
        # 添加提示文字
        self.canvas.create_text(
            text_x, text_y,
            text="拖拽鼠标选择点击区域，按ESC键取消",
            fill="white",
            font=("Arial", 16, "bold")
        )
        
        # 绑定鼠标事件
        self.canvas.bind("<Button-1>", self.start_selection)
        self.canvas.bind("<B1-Motion>", self.update_selection)
        self.canvas.bind("<ButtonRelease-1>", self.end_selection)
        
        # 绑定键盘事件
        self.root.bind("<Escape>", self.cancel_selection)
        self.root.focus_set()
        
        self.selecting = True
        
    def start_selection(self, event):
        """开始选择"""
        self.start_x = event.x
        self.start_y = event.y
        
    def update_selection(self, event):
        """更新选择区域"""
        if self.start_x is not None and self.start_y is not None:
            # 清除之前的选择框
            self.canvas.delete("selection")
            
            # 绘制选择框边框（双层边框，更醒目）
            self.canvas.create_rectangle(
                self.start_x, self.start_y, event.x, event.y,
                outline="red", width=4, tags="selection"
            )
            self.canvas.create_rectangle(
                self.start_x, self.start_y, event.x, event.y,
                outline="white", width=2, tags="selection"
            )
            
            # 显示选择区域的尺寸信息
            width = abs(event.x - self.start_x)
            height = abs(event.y - self.start_y)
            info_text = f"区域大小: {width} × {height} 像素"
            
            # 计算信息文字位置
            info_x = (self.start_x + event.x) // 2
            info_y = min(self.start_y, event.y) - 10
            if info_y < 20:
                info_y = max(self.start_y, event.y) + 20
                
            # 创建信息文字背景
            self.canvas.create_rectangle(
                info_x - 80, info_y - 10,
                info_x + 80, info_y + 10,
                fill="black", outline="yellow", width=1,
                tags="selection"
            )
            
            # 显示信息文字
            self.canvas.create_text(
                info_x, info_y,
                text=info_text,
                fill="yellow",
                font=("Arial", 10, "bold"),
                tags="selection"
            )
            
    def end_selection(self, event):
        """结束选择"""
        if self.start_x is not None and self.start_y is not None:
            self.end_x = event.x
            self.end_y = event.y
            
            # 确保坐标正确（左上角和右下角）
            x1 = min(self.start_x, self.end_x)
            y1 = min(self.start_y, self.end_y)
            x2 = max(self.start_x, self.end_x)
            y2 = max(self.start_y, self.end_y)
            
            # 检查区域大小
            if abs(x2 - x1) > 10 and abs(y2 - y1) > 10:
                self.callback((x1, y1, x2, y2))
                self.close_selector()
            else:
                messagebox.showwarning("警告", "选择的区域太小，请重新选择")
                self.close_selector()
                
    def cancel_selection(self, event):
        """取消选择"""
        self.close_selector()
        
    def close_selector(self):
        """关闭选择器"""
        if hasattr(self, 'root'):
            self.root.destroy()
        self.selecting = False


class AutoClicker:
    """自动点击器主类"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("自动点击器 - 支持Windows/Mac")
        self.root.geometry("520x750")
        self.root.resizable(True, True)
        self.root.minsize(480, 650)
        
        # 设置程序图标和样式
        self.setup_style()
        
        # 初始化变量
        self.click_area = None  # (x1, y1, x2, y2)
        self.is_running = False
        self.click_thread = None
        
        # 创建GUI界面
        self.create_widgets()
        
        # 禁用pyautogui的安全机制（小心使用）
        pyautogui.FAILSAFE = False
        
    def setup_style(self):
        """设置界面样式"""
        style = ttk.Style()
        
        # 检测系统主题
        if platform.system() == "Darwin":  # macOS
            style.theme_use('aqua')
        elif platform.system() == "Windows":
            style.theme_use('winnative')
        else:
            style.theme_use('clam')
            
    def create_widgets(self):
        """创建GUI组件"""
        # 主标题
        title_label = tk.Label(
            self.root, 
            text="🖱️ 自动点击器",
            font=("Arial", 18, "bold"),
            fg="#2c3e50"
        )
        title_label.pack(pady=10)
        
        # 系统信息
        system_info = f"当前系统: {platform.system()} {platform.release()}"
        info_label = tk.Label(self.root, text=system_info, fg="#7f8c8d")
        info_label.pack()
        
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 1. 区域选择部分
        self.create_area_section(main_frame)
        
        # 2. 时间设置部分
        self.create_time_section(main_frame)
        
        # 3. 点击次数设置部分
        self.create_click_section(main_frame)
        
        # 4. 位置偏差设置部分
        self.create_offset_section(main_frame)
        
        # 5. 控制按钮部分
        self.create_control_section(main_frame)
        
        # 6. 状态显示部分
        self.create_status_section(main_frame)
        
    def create_area_section(self, parent):
        """创建区域选择部分"""
        area_frame = ttk.LabelFrame(parent, text="📍 点击区域设置", padding="10")
        area_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.area_button = ttk.Button(
            area_frame,
            text="选择屏幕区域",
            command=self.select_click_area,
            width=20
        )
        self.area_button.pack(side=tk.LEFT)
        
        self.area_label = tk.Label(
            area_frame,
            text="未选择区域",
            fg="#e74c3c"
        )
        self.area_label.pack(side=tk.LEFT, padx=(10, 0))
        
    def create_time_section(self, parent):
        """创建时间设置部分"""
        time_frame = ttk.LabelFrame(parent, text="⏰ 点击时间间隔设置", padding="10")
        time_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 最小时间间隔
        min_time_frame = ttk.Frame(time_frame)
        min_time_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(min_time_frame, text="最小间隔(秒):").pack(side=tk.LEFT)
        self.min_time_var = tk.StringVar(value="1.0")
        min_time_entry = ttk.Entry(min_time_frame, textvariable=self.min_time_var, width=10)
        min_time_entry.pack(side=tk.LEFT, padx=(10, 0))
        
        # 最大时间间隔
        max_time_frame = ttk.Frame(time_frame)
        max_time_frame.pack(fill=tk.X)
        
        ttk.Label(max_time_frame, text="最大间隔(秒):").pack(side=tk.LEFT)
        self.max_time_var = tk.StringVar(value="3.0")
        max_time_entry = ttk.Entry(max_time_frame, textvariable=self.max_time_var, width=10)
        max_time_entry.pack(side=tk.LEFT, padx=(10, 0))
        
    def create_click_section(self, parent):
        """创建点击次数设置部分"""
        click_frame = ttk.LabelFrame(parent, text="🖱️ 连续点击次数设置", padding="10")
        click_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 最小点击次数
        min_click_frame = ttk.Frame(click_frame)
        min_click_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(min_click_frame, text="最小次数:").pack(side=tk.LEFT)
        self.min_clicks_var = tk.StringVar(value="1")
        min_clicks_entry = ttk.Entry(min_click_frame, textvariable=self.min_clicks_var, width=10)
        min_clicks_entry.pack(side=tk.LEFT, padx=(10, 0))
        
        # 最大点击次数
        max_click_frame = ttk.Frame(click_frame)
        max_click_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(max_click_frame, text="最大次数:").pack(side=tk.LEFT)
        self.max_clicks_var = tk.StringVar(value="3")
        max_clicks_entry = ttk.Entry(max_click_frame, textvariable=self.max_clicks_var, width=10)
        max_clicks_entry.pack(side=tk.LEFT, padx=(10, 0))
        
        # 连续点击间隔 - 最小间隔
        min_interval_frame = ttk.Frame(click_frame)
        min_interval_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(min_interval_frame, text="连续点击最小间隔(秒):").pack(side=tk.LEFT)
        self.min_click_interval_var = tk.StringVar(value="0.05")
        min_interval_entry = ttk.Entry(min_interval_frame, textvariable=self.min_click_interval_var, width=10)
        min_interval_entry.pack(side=tk.LEFT, padx=(10, 0))
        
        # 连续点击间隔 - 最大间隔
        max_interval_frame = ttk.Frame(click_frame)
        max_interval_frame.pack(fill=tk.X)
        
        ttk.Label(max_interval_frame, text="连续点击最大间隔(秒):").pack(side=tk.LEFT)
        self.max_click_interval_var = tk.StringVar(value="0.2")
        max_interval_entry = ttk.Entry(max_interval_frame, textvariable=self.max_click_interval_var, width=10)
        max_interval_entry.pack(side=tk.LEFT, padx=(10, 0))
        
    def create_offset_section(self, parent):
        """创建位置偏差设置部分"""
        offset_frame = ttk.LabelFrame(parent, text="📐 点击位置偏差设置", padding="10")
        offset_frame.pack(fill=tk.X, pady=(0, 10))
        
        # X轴偏差
        x_offset_frame = ttk.Frame(offset_frame)
        x_offset_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(x_offset_frame, text="X轴最大偏差(像素):").pack(side=tk.LEFT)
        self.x_offset_var = tk.StringVar(value="10")
        x_offset_entry = ttk.Entry(x_offset_frame, textvariable=self.x_offset_var, width=10)
        x_offset_entry.pack(side=tk.LEFT, padx=(10, 0))
        
        # Y轴偏差
        y_offset_frame = ttk.Frame(offset_frame)
        y_offset_frame.pack(fill=tk.X)
        
        ttk.Label(y_offset_frame, text="Y轴最大偏差(像素):").pack(side=tk.LEFT)
        self.y_offset_var = tk.StringVar(value="10")
        y_offset_entry = ttk.Entry(y_offset_frame, textvariable=self.y_offset_var, width=10)
        y_offset_entry.pack(side=tk.LEFT, padx=(10, 0))
        
    def create_control_section(self, parent):
        """创建控制按钮部分"""
        control_frame = ttk.Frame(parent)
        control_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.start_button = ttk.Button(
            control_frame,
            text="▶️ 开始自动点击",
            command=self.start_clicking,
            style="Accent.TButton"
        )
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_button = ttk.Button(
            control_frame,
            text="⏹️ 停止点击",
            command=self.stop_clicking,
            state=tk.DISABLED
        )
        self.stop_button.pack(side=tk.LEFT)
        
        # 紧急停止提示
        emergency_label = tk.Label(
            control_frame,
            text="紧急停止: 移动鼠标到屏幕左上角",
            fg="#e74c3c",
            font=("Arial", 9)
        )
        emergency_label.pack(side=tk.RIGHT)
        
    def create_status_section(self, parent):
        """创建状态显示部分"""
        status_frame = ttk.LabelFrame(parent, text="📊 运行状态", padding="10")
        status_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.status_label = tk.Label(
            status_frame,
            text="就绪",
            fg="#27ae60",
            font=("Arial", 12, "bold")
        )
        self.status_label.pack()
        
        self.click_count_label = tk.Label(
            status_frame,
            text="总点击次数: 0",
            fg="#3498db"
        )
        self.click_count_label.pack()
        
        self.click_count = 0
        
    def select_click_area(self):
        """选择点击区域"""
        if self.is_running:
            messagebox.showwarning("警告", "请先停止自动点击")
            return
            
        def area_callback(area):
            self.click_area = area
            self.area_label.config(
                text=f"区域: ({area[0]}, {area[1]}) - ({area[2]}, {area[3]})",
                fg="#27ae60"
            )
            
        selector = AreaSelector(area_callback)
        selector.select_area()
        
    def validate_settings(self):
        """验证设置参数"""
        try:
            # 验证时间间隔
            min_time = float(self.min_time_var.get())
            max_time = float(self.max_time_var.get())
            if min_time <= 0 or max_time <= 0 or min_time > max_time:
                raise ValueError("时间间隔设置无效")
                
            # 验证点击次数
            min_clicks = int(self.min_clicks_var.get())
            max_clicks = int(self.max_clicks_var.get())
            if min_clicks <= 0 or max_clicks <= 0 or min_clicks > max_clicks:
                raise ValueError("点击次数设置无效")
                
            # 验证连续点击间隔
            min_click_interval = float(self.min_click_interval_var.get())
            max_click_interval = float(self.max_click_interval_var.get())
            if min_click_interval < 0.05:
                raise ValueError("连续点击最小间隔不能小于0.05秒(50ms)")
            if max_click_interval > 0.5:
                raise ValueError("连续点击最大间隔不能大于0.5秒(500ms)")
            if min_click_interval > max_click_interval:
                raise ValueError("连续点击最小间隔不能大于最大间隔")
                
            # 验证位置偏差
            x_offset = int(self.x_offset_var.get())
            y_offset = int(self.y_offset_var.get())
            if x_offset < 0 or y_offset < 0:
                raise ValueError("位置偏差不能为负数")
                
            # 验证点击区域
            if not self.click_area:
                raise ValueError("请先选择点击区域")
                
            return True
            
        except ValueError as e:
            messagebox.showerror("设置错误", f"参数设置有误: {str(e)}")
            return False
            
    def start_clicking(self):
        """开始自动点击"""
        if not self.validate_settings():
            return
            
        self.is_running = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.area_button.config(state=tk.DISABLED)
        
        # 启动点击线程
        self.click_thread = threading.Thread(target=self.clicking_loop, daemon=True)
        self.click_thread.start()
        
        self.status_label.config(text="运行中...", fg="#f39c12")
        
    def stop_clicking(self):
        """停止自动点击"""
        self.is_running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.area_button.config(state=tk.NORMAL)
        
        self.status_label.config(text="已停止", fg="#e74c3c")
        
    def clicking_loop(self):
        """点击循环"""
        while self.is_running:
            try:
                # 获取随机时间间隔
                min_time = float(self.min_time_var.get())
                max_time = float(self.max_time_var.get())
                wait_time = random.uniform(min_time, max_time)
                
                # 等待指定时间
                time.sleep(wait_time)
                
                if not self.is_running:
                    break
                    
                # 获取随机点击次数
                min_clicks = int(self.min_clicks_var.get())
                max_clicks = int(self.max_clicks_var.get())
                click_count = random.randint(min_clicks, max_clicks)
                
                # 获取连续点击间隔范围
                min_click_interval = float(self.min_click_interval_var.get())
                max_click_interval = float(self.max_click_interval_var.get())
                
                # 获取位置偏差设置
                x_offset = int(self.x_offset_var.get())
                y_offset = int(self.y_offset_var.get())
                
                # 在区域内随机选择第一个点击位置
                x1, y1, x2, y2 = self.click_area
                base_x = random.randint(x1, x2)
                base_y = random.randint(y1, y2)
                
                # 执行连续点击
                for i in range(click_count):
                    if not self.is_running:
                        break
                        
                    # 计算当前点击位置（带偏差）
                    if i == 0:
                        click_x, click_y = base_x, base_y
                    else:
                        # 在上一次点击位置基础上添加随机偏差
                        offset_x = random.randint(-x_offset, x_offset)
                        offset_y = random.randint(-y_offset, y_offset)
                        click_x = max(x1, min(x2, base_x + offset_x))
                        click_y = max(y1, min(y2, base_y + offset_y))
                    
                    # 执行点击
                    pyautogui.click(click_x, click_y)
                    self.click_count += 1
                    
                    # 更新UI（在主线程中）
                    self.root.after(0, self.update_click_count)
                    
                    # 连续点击间隔（随机）
                    if i < click_count - 1:
                        random_interval = random.uniform(min_click_interval, max_click_interval)
                        time.sleep(random_interval)
                        
            except Exception as e:
                print(f"点击过程中发生错误: {e}")
                self.root.after(0, self.stop_clicking)
                break
                
    def update_click_count(self):
        """更新点击计数显示"""
        self.click_count_label.config(text=f"总点击次数: {self.click_count}")
        
    def run(self):
        """运行程序"""
        # 设置窗口居中
        self.center_window()
        
        # 启动主循环
        self.root.mainloop()
        
    def center_window(self):
        """窗口居中显示"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")


def main():
    """主函数"""
    try:
        app = AutoClicker()
        app.run()
    except KeyboardInterrupt:
        print("程序被用户中断")
    except Exception as e:
        print(f"程序运行出错: {e}")
        messagebox.showerror("错误", f"程序运行出错: {e}")


if __name__ == "__main__":
    main()

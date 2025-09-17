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
import json
import os
from datetime import datetime

class AreaSelector:
    """屏幕区域选择器"""
    
    def __init__(self, callback, area_count=1):
        self.callback = callback
        self.area_count = area_count
        self.current_area = 0
        self.selected_areas = []
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
            stipple="gray50", tags="tip_text"
        )
        
        # 添加提示文字
        if self.area_count > 1:
            tip_text = f"选择第 {self.current_area + 1}/{self.area_count} 个区域，拖拽鼠标选择，按ESC键取消"
        else:
            tip_text = "拖拽鼠标选择点击区域，按ESC键取消"
            
        self.canvas.create_text(
            text_x, text_y,
            text=tip_text,
            fill="white",
            font=("Arial", 16, "bold"),
            tags="tip_text"
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
                # 添加当前区域到列表
                self.selected_areas.append((x1, y1, x2, y2))
                self.current_area += 1
                
                # 检查是否还需要选择更多区域
                if self.current_area < self.area_count:
                    # 重置选择状态，准备选择下一个区域
                    self.start_x = None
                    self.start_y = None
                    self.end_x = None
                    self.end_y = None
                    
                    # 清除当前选择框
                    self.canvas.delete("selection")
                    
                    # 更新提示文字
                    self.update_tip_text()
                else:
                    # 所有区域选择完成
                    self.callback(self.selected_areas)
                    self.close_selector()
            else:
                messagebox.showwarning("警告", "选择的区域太小，请重新选择")
                # 不关闭选择器，让用户重新选择当前区域
                
    def update_tip_text(self):
        """更新提示文字"""
        # 删除旧的提示文字
        self.canvas.delete("tip_text")
        
        # 获取屏幕尺寸
        screen_width = self.root.winfo_screenwidth()
        text_x = screen_width // 2
        text_y = 50
        
        # 创建新的提示文字
        if self.area_count > 1:
            tip_text = f"选择第 {self.current_area + 1}/{self.area_count} 个区域，拖拽鼠标选择，按ESC键取消"
        else:
            tip_text = "拖拽鼠标选择点击区域，按ESC键取消"
            
        # 创建文字背景
        self.canvas.create_rectangle(
            text_x - 200, text_y - 20,
            text_x + 200, text_y + 20,
            fill="black", outline="red", width=2,
            stipple="gray50", tags="tip_text"
        )
        
        # 添加提示文字
        self.canvas.create_text(
            text_x, text_y,
            text=tip_text,
            fill="white",
            font=("Arial", 16, "bold"),
            tags="tip_text"
        )
        
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
        self.root.geometry("700x700")
        self.root.resizable(True, True)
        self.root.minsize(560, 500)
        
        # 设置程序图标和样式
        self.setup_style()
        
        # 初始化变量
        self.click_areas = []  # 多个区域列表 [(x1, y1, x2, y2), ...]
        self.current_area_index = 0  # 当前点击区域索引
        self.is_running = False
        self.click_thread = None
        self.start_time = None  # 开始时间
        self.total_click_count = 0  # 总点击次数
        
        # 创建GUI界面
        self.create_widgets()
        
        # 配置文件目录（在绑定快捷键之前初始化）
        self.config_dir = "configs"
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
        
        # 最后使用的配置文件
        self.last_config_file = os.path.join(self.config_dir, "last_used.txt")
        
        # 绑定快捷键
        self.bind_hotkeys()
        
        # 禁用pyautogui的安全机制（小心使用）
        pyautogui.FAILSAFE = False
        
        # 延迟自动加载最后使用的配置
        self.root.after(200, self.load_last_used_config_on_startup)
        
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
    
    def create_scrollable_frame(self):
        """创建可滚动的主框架"""
        # 创建主容器框架
        container_frame = ttk.Frame(self.root)
        container_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建画布和滚动条
        self.canvas = tk.Canvas(container_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas, padding="20")
        
        # 配置滚动区域
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        # 创建画布窗口
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        # 配置画布滚动
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        # 布局画布和滚动条
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 绑定鼠标滚轮事件
        self.bind_mousewheel()
        
        # 绑定画布大小变化事件
        self.canvas.bind('<Configure>', self.on_canvas_configure)
        
    def bind_mousewheel(self):
        """绑定鼠标滚轮事件"""
        def _on_mousewheel(event):
            # Windows 和 Linux
            if platform.system() in ["Windows", "Linux"]:
                self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            # macOS
            elif platform.system() == "Darwin":
                self.canvas.yview_scroll(int(-1*event.delta), "units")
                
        def _on_mousewheel_mac(event):
            # macOS 的触控板滚动事件
            self.canvas.yview_scroll(int(-1*event.delta), "units")
            
        def _bind_to_mousewheel(event):
            if platform.system() == "Darwin":
                # macOS 需要绑定不同的事件
                self.canvas.bind_all("<MouseWheel>", _on_mousewheel_mac)
                self.canvas.bind_all("<Button-4>", lambda e: self.canvas.yview_scroll(-1, "units"))
                self.canvas.bind_all("<Button-5>", lambda e: self.canvas.yview_scroll(1, "units"))
            else:
                self.canvas.bind_all("<MouseWheel>", _on_mousewheel)
            
        def _unbind_from_mousewheel(event):
            self.canvas.unbind_all("<MouseWheel>")
            if platform.system() == "Darwin":
                self.canvas.unbind_all("<Button-4>")
                self.canvas.unbind_all("<Button-5>")
            
        # 当鼠标进入画布时绑定滚轮事件
        self.canvas.bind('<Enter>', _bind_to_mousewheel)
        # 当鼠标离开画布时解绑滚轮事件
        self.canvas.bind('<Leave>', _unbind_from_mousewheel)
        
    def on_canvas_configure(self, event):
        """画布大小变化时调整内容宽度"""
        canvas_width = event.width
        self.canvas.itemconfig(self.canvas_window, width=canvas_width)
            
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
        
        # 创建可滚动的主框架
        self.create_scrollable_frame()
        
        # 1. 区域选择部分
        self.create_area_section(self.scrollable_frame)
        
        # 2. 时间设置部分
        self.create_time_section(self.scrollable_frame)
        
        # 3. 点击次数设置部分
        self.create_click_section(self.scrollable_frame)
        
        # 4. 位置偏差设置部分
        self.create_offset_section(self.scrollable_frame)
        
        # 5. 时长和次数限制设置部分
        self.create_limit_section(self.scrollable_frame)
        
        # 6. 配置管理部分
        self.create_config_section(self.scrollable_frame)
        
        # 7. 控制按钮部分
        self.create_control_section(self.scrollable_frame)
        
        # 8. 状态显示部分
        self.create_status_section(self.scrollable_frame)
        
    def create_area_section(self, parent):
        """创建区域选择部分"""
        area_frame = ttk.LabelFrame(parent, text="📍 多区域点击设置", padding="10")
        area_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 区域数量设置
        area_count_frame = ttk.Frame(area_frame)
        area_count_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(area_count_frame, text="区域数量:").pack(side=tk.LEFT)
        self.area_count_var = tk.StringVar(value="1")
        area_count_entry = ttk.Entry(area_count_frame, textvariable=self.area_count_var, width=5)
        area_count_entry.pack(side=tk.LEFT, padx=(5, 10))
        
        ttk.Label(area_count_frame, text="区域间隔范围(秒):").pack(side=tk.LEFT)
        self.min_area_interval_var = tk.StringVar(value="0.3")
        min_area_interval_entry = ttk.Entry(area_count_frame, textvariable=self.min_area_interval_var, width=6)
        min_area_interval_entry.pack(side=tk.LEFT, padx=(5, 2))
        
        ttk.Label(area_count_frame, text="-").pack(side=tk.LEFT)
        self.max_area_interval_var = tk.StringVar(value="0.7")
        max_area_interval_entry = ttk.Entry(area_count_frame, textvariable=self.max_area_interval_var, width=6)
        max_area_interval_entry.pack(side=tk.LEFT, padx=(2, 0))
        
        # 区域间隔说明
        area_desc_label = tk.Label(
            area_frame,
            text="区域间隔：一次循环中从一个区域切换到下一个区域的随机等待时间",
            fg="#7f8c8d",
            font=("Arial", 9)
        )
        area_desc_label.pack(anchor="w", pady=(5, 0))
        
        # 选择按钮和状态
        button_frame = ttk.Frame(area_frame)
        button_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.area_button = ttk.Button(
            button_frame,
            text="开始选择区域 (Ctrl+S)",
            command=self.select_click_areas,
            width=22
        )
        self.area_button.pack(side=tk.LEFT)
        
        self.area_label = tk.Label(
            button_frame,
            text="未选择区域",
            fg="#e74c3c"
        )
        self.area_label.pack(side=tk.LEFT, padx=(10, 0))
        
    def create_time_section(self, parent):
        """创建时间设置部分"""
        time_frame = ttk.LabelFrame(parent, text="⏰ 循环时间间隔设置", padding="10")
        time_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 说明文字
        desc_label = tk.Label(
            time_frame,
            text="循环间隔：完成所有区域一轮点击后，开始下一轮循环前的等待时间",
            fg="#7f8c8d",
            font=("Arial", 9)
        )
        desc_label.pack(anchor="w", pady=(0, 5))
        
        # 最小循环间隔
        min_time_frame = ttk.Frame(time_frame)
        min_time_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(min_time_frame, text="最小循环间隔(秒):").pack(side=tk.LEFT)
        self.min_time_var = tk.StringVar(value="1.0")
        min_time_entry = ttk.Entry(min_time_frame, textvariable=self.min_time_var, width=10)
        min_time_entry.pack(side=tk.LEFT, padx=(10, 0))
        
        # 最大循环间隔
        max_time_frame = ttk.Frame(time_frame)
        max_time_frame.pack(fill=tk.X)
        
        ttk.Label(max_time_frame, text="最大循环间隔(秒):").pack(side=tk.LEFT)
        self.max_time_var = tk.StringVar(value="3.0")
        max_time_entry = ttk.Entry(max_time_frame, textvariable=self.max_time_var, width=10)
        max_time_entry.pack(side=tk.LEFT, padx=(10, 0))
        
    def create_click_section(self, parent):
        """创建点击次数设置部分"""
        click_frame = ttk.LabelFrame(parent, text="🖱️ 连续点击次数设置", padding="10")
        click_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 说明文字
        desc_label = tk.Label(
            click_frame,
            text="连续点击：单个区域内一次点击事件中的快速连续点击",
            fg="#7f8c8d",
            font=("Arial", 9)
        )
        desc_label.pack(anchor="w", pady=(0, 5))
        
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
        
        # 说明文字
        desc_label = tk.Label(
            offset_frame,
            text="连续点击偏差概率设置：无偏差概率(0-1)，剩余概率为有偏差",
            fg="#7f8c8d",
            font=("Arial", 9)
        )
        desc_label.pack(anchor="w", pady=(0, 5))
        
        # 无偏差概率设置
        no_offset_prob_frame = ttk.Frame(offset_frame)
        no_offset_prob_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(no_offset_prob_frame, text="无偏差概率:").pack(side=tk.LEFT)
        self.no_offset_probability_var = tk.StringVar(value="0.67")
        no_offset_prob_entry = ttk.Entry(no_offset_prob_frame, textvariable=self.no_offset_probability_var, width=8)
        no_offset_prob_entry.pack(side=tk.LEFT, padx=(10, 10))
        
        ttk.Label(no_offset_prob_frame, text="(0.0-1.0，如0.67表示67%无偏差)").pack(side=tk.LEFT)
        
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
        
    def create_limit_section(self, parent):
        """创建时长和次数限制设置部分"""
        limit_frame = ttk.LabelFrame(parent, text="⏱️ 运行限制设置", padding="10")
        limit_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 时长限制设置
        duration_frame = ttk.Frame(limit_frame)
        duration_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 时长限制复选框和输入框
        duration_control_frame = ttk.Frame(duration_frame)
        duration_control_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.duration_limit_var = tk.BooleanVar(value=False)
        duration_checkbox = ttk.Checkbutton(
            duration_control_frame,
            text="限制运行时长:",
            variable=self.duration_limit_var,
            command=self.toggle_duration_limit
        )
        duration_checkbox.pack(side=tk.LEFT)
        
        self.duration_var = tk.StringVar(value="10")
        self.duration_entry = ttk.Entry(duration_control_frame, textvariable=self.duration_var, width=10, state=tk.DISABLED)
        self.duration_entry.pack(side=tk.LEFT, padx=(10, 5))
        
        ttk.Label(duration_control_frame, text="分钟").pack(side=tk.LEFT)
        
        # 无限时长选项
        unlimited_duration_frame = ttk.Frame(duration_frame)
        unlimited_duration_frame.pack(fill=tk.X)
        
        self.unlimited_duration_var = tk.BooleanVar(value=True)
        unlimited_duration_checkbox = ttk.Checkbutton(
            unlimited_duration_frame,
            text="无限时长运行",
            variable=self.unlimited_duration_var,
            command=self.toggle_unlimited_duration
        )
        unlimited_duration_checkbox.pack(side=tk.LEFT)
        
        # 分隔线
        separator = ttk.Separator(limit_frame, orient='horizontal')
        separator.pack(fill=tk.X, pady=10)
        
        # 次数限制设置
        count_frame = ttk.Frame(limit_frame)
        count_frame.pack(fill=tk.X)
        
        # 次数限制复选框和输入框
        count_control_frame = ttk.Frame(count_frame)
        count_control_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.count_limit_var = tk.BooleanVar(value=False)
        count_checkbox = ttk.Checkbutton(
            count_control_frame,
            text="限制总点击次数:",
            variable=self.count_limit_var,
            command=self.toggle_count_limit
        )
        count_checkbox.pack(side=tk.LEFT)
        
        self.max_total_clicks_var = tk.StringVar(value="1000")
        self.count_entry = ttk.Entry(count_control_frame, textvariable=self.max_total_clicks_var, width=10, state=tk.DISABLED)
        self.count_entry.pack(side=tk.LEFT, padx=(10, 5))
        
        ttk.Label(count_control_frame, text="次").pack(side=tk.LEFT)
        
        # 无限次数选项
        unlimited_count_frame = ttk.Frame(count_frame)
        unlimited_count_frame.pack(fill=tk.X)
        
        self.unlimited_count_var = tk.BooleanVar(value=True)
        unlimited_count_checkbox = ttk.Checkbutton(
            unlimited_count_frame,
            text="无限次数点击",
            variable=self.unlimited_count_var,
            command=self.toggle_unlimited_count
        )
        unlimited_count_checkbox.pack(side=tk.LEFT)
        
    def toggle_duration_limit(self):
        """切换时长限制状态"""
        if self.duration_limit_var.get():
            self.duration_entry.config(state=tk.NORMAL)
            self.unlimited_duration_var.set(False)
        else:
            self.duration_entry.config(state=tk.DISABLED)
            if not self.count_limit_var.get():
                self.unlimited_duration_var.set(True)
                
    def toggle_unlimited_duration(self):
        """切换无限时长状态"""
        if self.unlimited_duration_var.get():
            self.duration_limit_var.set(False)
            self.duration_entry.config(state=tk.DISABLED)
            
    def toggle_count_limit(self):
        """切换次数限制状态"""
        if self.count_limit_var.get():
            self.count_entry.config(state=tk.NORMAL)
            self.unlimited_count_var.set(False)
        else:
            self.count_entry.config(state=tk.DISABLED)
            if not self.duration_limit_var.get():
                self.unlimited_count_var.set(True)
                
    def toggle_unlimited_count(self):
        """切换无限次数状态"""
        if self.unlimited_count_var.get():
            self.count_limit_var.set(False)
            self.count_entry.config(state=tk.DISABLED)
        
    def create_config_section(self, parent):
        """创建配置管理部分"""
        config_frame = ttk.LabelFrame(parent, text="💾 配置管理", padding="10")
        config_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 配置名称输入
        name_frame = ttk.Frame(config_frame)
        name_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(name_frame, text="配置名称:").pack(side=tk.LEFT)
        self.config_name_var = tk.StringVar()
        self.config_name_entry = ttk.Entry(name_frame, textvariable=self.config_name_var, width=20)
        self.config_name_entry.pack(side=tk.LEFT, padx=(5, 10))
        
        # 保存配置按钮
        save_config_btn = ttk.Button(
            name_frame,
            text="保存配置",
            command=self.save_config,
            width=12
        )
        save_config_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # 配置选择和加载
        load_frame = ttk.Frame(config_frame)
        load_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Label(load_frame, text="选择配置:").pack(side=tk.LEFT)
        self.config_list_var = tk.StringVar()
        self.config_combobox = ttk.Combobox(
            load_frame,
            textvariable=self.config_list_var,
            width=18,
            state="readonly"
        )
        self.config_combobox.pack(side=tk.LEFT, padx=(5, 10))
        
        # 加载配置按钮
        load_config_btn = ttk.Button(
            load_frame,
            text="加载配置",
            command=self.load_config,
            width=12
        )
        load_config_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # 删除配置按钮
        delete_config_btn = ttk.Button(
            load_frame,
            text="删除配置",
            command=self.delete_config,
            width=12
        )
        delete_config_btn.pack(side=tk.LEFT, padx=(0, 0))
        
        # 延迟刷新配置列表，确保config_dir已经初始化
        self.root.after(100, self.refresh_config_list)
        
    def create_control_section(self, parent):
        """创建控制按钮部分"""
        control_frame = ttk.Frame(parent)
        control_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.start_button = ttk.Button(
            control_frame,
            text="▶️ 开始自动点击 (Ctrl+Enter)",
            command=self.start_clicking,
            style="Accent.TButton"
        )
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_button = ttk.Button(
            control_frame,
            text="⏹️ 停止点击 (ESC)",
            command=self.stop_clicking,
            state=tk.DISABLED
        )
        self.stop_button.pack(side=tk.LEFT)
        
        # 紧急停止提示
        emergency_label = tk.Label(
            control_frame,
            text="紧急停止: ESC键 或 移动鼠标到屏幕左上角",
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
        
        # 剩余时间显示
        self.remaining_time_label = tk.Label(
            status_frame,
            text="剩余时间: --",
            fg="#9b59b6"
        )
        self.remaining_time_label.pack()
        
        # 剩余次数显示
        self.remaining_count_label = tk.Label(
            status_frame,
            text="剩余次数: --",
            fg="#e67e22"
        )
        self.remaining_count_label.pack()
        
        # 当前区域显示
        self.current_area_label = tk.Label(
            status_frame,
            text="当前区域: --",
            fg="#8e44ad"
        )
        self.current_area_label.pack()
        
        # 快捷键提示
        hotkey_frame = ttk.LabelFrame(status_frame, text="⌨️ 快捷键", padding="5")
        hotkey_frame.pack(fill=tk.X, pady=(10, 0))
        
        hotkey_text = (
            "Ctrl+S: 选择区域\n"
            "Ctrl+Enter: 开始/停止点击\n"
            "ESC: 强制停止\n"
            "Ctrl+Q: 退出程序"
        )
        
        hotkey_label = tk.Label(
            hotkey_frame,
            text=hotkey_text,
            fg="#7f8c8d",
            font=("Arial", 9),
            justify=tk.LEFT
        )
        hotkey_label.pack(anchor="w")
        
        self.click_count = 0
        
    def select_click_areas(self):
        """选择多个点击区域"""
        if self.is_running:
            messagebox.showwarning("警告", "请先停止自动点击")
            return
            
        try:
            area_count = int(self.area_count_var.get())
            if area_count < 1 or area_count > 10:
                messagebox.showerror("错误", "区域数量必须在1-10之间")
                return
        except ValueError:
            messagebox.showerror("错误", "请输入有效的区域数量")
            return
            
        def areas_callback(areas):
            self.click_areas = areas
            self.current_area_index = 0
            if len(areas) == 1:
                area = areas[0]
                self.area_label.config(
                    text=f"区域: ({area[0]}, {area[1]}) - ({area[2]}, {area[3]})",
                    fg="#27ae60"
                )
            else:
                self.area_label.config(
                    text=f"已选择 {len(areas)} 个区域",
                    fg="#27ae60"
                )
            
        selector = AreaSelector(areas_callback, area_count)
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
                
            # 验证无偏差概率设置
            no_offset_prob = float(self.no_offset_probability_var.get())
            if no_offset_prob < 0 or no_offset_prob > 1:
                raise ValueError("无偏差概率必须在0.0-1.0之间")
                
            # 验证点击区域
            if not self.click_areas:
                raise ValueError("请先选择点击区域")
                
            # 验证区域间隔
            if len(self.click_areas) > 1:
                min_area_interval = float(self.min_area_interval_var.get())
                max_area_interval = float(self.max_area_interval_var.get())
                if min_area_interval < 0 or max_area_interval < 0:
                    raise ValueError("区域间隔不能为负数")
                if min_area_interval > max_area_interval:
                    raise ValueError("区域间隔最小值不能大于最大值")
                
            # 验证时长限制设置
            if self.duration_limit_var.get():
                duration = float(self.duration_var.get())
                if duration <= 0:
                    raise ValueError("运行时长必须大于0")
                    
            # 验证次数限制设置
            if self.count_limit_var.get():
                max_total_clicks = int(self.max_total_clicks_var.get())
                if max_total_clicks <= 0:
                    raise ValueError("总点击次数必须大于0")
                    
            # 确保至少有一个限制条件或者选择了无限选项
            if not self.unlimited_duration_var.get() and not self.duration_limit_var.get() and \
               not self.unlimited_count_var.get() and not self.count_limit_var.get():
                raise ValueError("请至少选择一种运行模式（时长限制、次数限制或无限模式）")
                
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
        
        # 初始化运行状态
        self.start_time = time.time()
        self.total_click_count = 0
        self.click_count = 0  # 重置总点击次数显示
        
        # 立即更新显示
        self.update_click_count()
        
        # 启动点击线程
        self.click_thread = threading.Thread(target=self.clicking_loop, daemon=True)
        self.click_thread.start()
        
        # 启动状态更新线程
        self.status_thread = threading.Thread(target=self.update_status_loop, daemon=True)
        self.status_thread.start()
        
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
                # 检查时长限制
                if self.duration_limit_var.get():
                    duration_limit = float(self.duration_var.get()) * 60  # 转换为秒
                    elapsed_time = time.time() - self.start_time
                    if elapsed_time >= duration_limit:
                        self.root.after(0, self.stop_clicking)
                        break
                        
                # 检查次数限制
                if self.count_limit_var.get():
                    max_total_clicks = int(self.max_total_clicks_var.get())
                    if self.total_click_count >= max_total_clicks:
                        self.root.after(0, self.stop_clicking)
                        break
                
                # 执行一轮完整的循环（所有区域）
                self.execute_one_cycle()
                
                if not self.is_running:
                    break
                
                # 循环间隔：完成所有区域一轮点击后的等待时间
                min_time = float(self.min_time_var.get())
                max_time = float(self.max_time_var.get())
                cycle_wait_time = random.uniform(min_time, max_time)
                time.sleep(cycle_wait_time)
                        
            except Exception as e:
                print(f"点击过程中发生错误: {e}")
                self.root.after(0, self.stop_clicking)
                break
                
    def execute_one_cycle(self):
        """执行一轮完整的循环（所有区域）"""
        # 获取连续点击间隔范围
        min_click_interval = float(self.min_click_interval_var.get())
        max_click_interval = float(self.max_click_interval_var.get())
        
        # 获取位置偏差设置
        x_offset = int(self.x_offset_var.get())
        y_offset = int(self.y_offset_var.get())
        
        # 获取区域间隔范围
        min_area_interval = float(self.min_area_interval_var.get())
        max_area_interval = float(self.max_area_interval_var.get())
        
        # 遍历所有区域
        for area_index in range(len(self.click_areas)):
            if not self.is_running:
                break
                
            # 更新当前区域索引
            self.current_area_index = area_index
            
            # 获取当前区域
            current_area = self.click_areas[area_index]
            x1, y1, x2, y2 = current_area
            
            # 执行当前区域的点击事件
            self.execute_area_clicks(x1, y1, x2, y2, x_offset, y_offset, min_click_interval, max_click_interval)
            
            # 区域间隔：切换到下一个区域前的随机等待时间（最后一个区域不需要等待）
            if area_index < len(self.click_areas) - 1 and max_area_interval > 0:
                random_area_interval = random.uniform(min_area_interval, max_area_interval)
                time.sleep(random_area_interval)
                
    def execute_area_clicks(self, x1, y1, x2, y2, x_offset, y_offset, min_click_interval, max_click_interval):
        """执行单个区域的点击事件"""
        # 获取随机点击次数
        min_clicks = int(self.min_clicks_var.get())
        max_clicks = int(self.max_clicks_var.get())
        click_count = random.randint(min_clicks, max_clicks)
        
        # 在区域内随机选择基础点击位置
        base_x = random.randint(x1, x2)
        base_y = random.randint(y1, y2)
        
        # 执行连续点击
        for i in range(click_count):
            if not self.is_running:
                break
                
            # 计算当前点击位置（带随机偏差概率）
            if i == 0:
                # 第一次点击总是在基础位置
                click_x, click_y = base_x, base_y
            else:
                # 根据用户设置的概率决定是否使用偏差
                no_offset_prob = float(self.no_offset_probability_var.get())
                use_offset = random.random() >= no_offset_prob  # 大于等于无偏差概率时使用偏差
                
                if use_offset:
                    # 有偏差：在基础位置上添加随机偏差
                    offset_x = random.randint(-x_offset, x_offset)
                    offset_y = random.randint(-y_offset, y_offset)
                    click_x = max(x1, min(x2, base_x + offset_x))
                    click_y = max(y1, min(y2, base_y + offset_y))
                else:
                    # 无偏差：在基础位置点击
                    click_x, click_y = base_x, base_y
            
            # 执行点击
            pyautogui.click(click_x, click_y)
            self.click_count += 1
            self.total_click_count += 1
            
            # 更新UI（在主线程中）
            self.root.after(0, self.update_click_count)
            
            # 检查次数限制（在每次点击后）
            if self.count_limit_var.get():
                max_total_clicks = int(self.max_total_clicks_var.get())
                if self.total_click_count >= max_total_clicks:
                    self.root.after(0, self.stop_clicking)
                    return
            
            # 连续点击间隔：同一区域内连续点击之间的快速间隔
            if i < click_count - 1:
                random_interval = random.uniform(min_click_interval, max_click_interval)
                time.sleep(random_interval)
                
    def update_click_count(self):
        """更新点击计数显示"""
        self.click_count_label.config(text=f"总点击次数: {self.click_count}")
        
    def update_status_loop(self):
        """状态更新循环"""
        while self.is_running:
            try:
                # 更新剩余时间
                if self.duration_limit_var.get():
                    duration_limit = float(self.duration_var.get()) * 60  # 转换为秒
                    elapsed_time = time.time() - self.start_time
                    remaining_time = max(0, duration_limit - elapsed_time)
                    
                    if remaining_time > 0:
                        minutes = int(remaining_time // 60)
                        seconds = int(remaining_time % 60)
                        time_text = f"剩余时间: {minutes:02d}:{seconds:02d}"
                    else:
                        time_text = "剩余时间: 00:00"
                else:
                    time_text = "剩余时间: 无限"
                    
                # 更新剩余次数
                if self.count_limit_var.get():
                    max_total_clicks = int(self.max_total_clicks_var.get())
                    remaining_clicks = max(0, max_total_clicks - self.total_click_count)
                    count_text = f"剩余次数: {remaining_clicks}"
                else:
                    count_text = "剩余次数: 无限"
                    
                # 更新当前区域信息
                if len(self.click_areas) > 1:
                    area_text = f"当前区域: {self.current_area_index + 1}/{len(self.click_areas)}"
                else:
                    area_text = "当前区域: 单区域"
                
                # 在主线程中更新UI
                self.root.after(0, lambda: self.remaining_time_label.config(text=time_text))
                self.root.after(0, lambda: self.remaining_count_label.config(text=count_text))
                self.root.after(0, lambda: self.current_area_label.config(text=area_text))
                
                time.sleep(1)  # 每秒更新一次
                
            except Exception as e:
                print(f"状态更新过程中发生错误: {e}")
                break
        
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
        
    def bind_hotkeys(self):
        """绑定快捷键"""
        # 绑定快捷键到主窗口
        self.root.bind('<Control-s>', lambda e: self.hotkey_select_area())  # Ctrl+S 选择区域
        self.root.bind('<Control-Return>', lambda e: self.hotkey_start_stop())  # Ctrl+Enter 开始/停止
        self.root.bind('<Escape>', lambda e: self.hotkey_stop())  # ESC 强制停止
        self.root.bind('<Control-q>', lambda e: self.root.quit())  # Ctrl+Q 退出程序
        
        # 确保窗口可以获得焦点以接收键盘事件
        self.root.focus_set()
        
    def hotkey_select_area(self):
        """快捷键：选择区域"""
        if not self.is_running:
            self.select_click_areas()
        else:
            # 如果正在运行，显示提示
            self.show_hotkey_message("请先停止点击再选择区域")
            
    def hotkey_start_stop(self):
        """快捷键：开始/停止点击"""
        if self.is_running:
            self.stop_clicking()
        else:
            self.start_clicking()
            
    def hotkey_stop(self):
        """快捷键：强制停止"""
        if self.is_running:
            self.stop_clicking()
            self.show_hotkey_message("已通过快捷键停止点击")
            
    def show_hotkey_message(self, message):
        """显示快捷键操作提示消息"""
        # 创建一个临时的状态消息
        original_text = self.status_label.cget("text")
        original_color = self.status_label.cget("fg")
        
        # 显示快捷键消息
        self.status_label.config(text=f"⌨️ {message}", fg="#f39c12")
        
        # 2秒后恢复原始状态
        self.root.after(2000, lambda: self.status_label.config(text=original_text, fg=original_color))
        
    def get_current_config(self):
        """获取当前所有配置设置（除了选择区域）"""
        config = {
            # 区域设置（不包括具体区域坐标）
            "area_count": self.area_count_var.get(),
            "min_area_interval": self.min_area_interval_var.get(),
            "max_area_interval": self.max_area_interval_var.get(),
            
            # 时间设置
            "min_time": self.min_time_var.get(),
            "max_time": self.max_time_var.get(),
            
            # 连续点击设置
            "min_clicks": self.min_clicks_var.get(),
            "max_clicks": self.max_clicks_var.get(),
            "min_click_interval": self.min_click_interval_var.get(),
            "max_click_interval": self.max_click_interval_var.get(),
            
            # 位置偏差设置
            "no_offset_probability": self.no_offset_probability_var.get(),
            "x_offset": self.x_offset_var.get(),
            "y_offset": self.y_offset_var.get(),
            
            # 运行限制设置
            "duration_limit": self.duration_limit_var.get(),
            "duration": self.duration_var.get(),
            "unlimited_duration": self.unlimited_duration_var.get(),
            "count_limit": self.count_limit_var.get(),
            "max_total_clicks": self.max_total_clicks_var.get(),
            "unlimited_count": self.unlimited_count_var.get(),
            
            # 保存时间戳
            "created_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        return config
        
    def apply_config(self, config):
        """应用配置到界面"""
        try:
            # 区域设置
            self.area_count_var.set(config.get("area_count", "1"))
            self.min_area_interval_var.set(config.get("min_area_interval", "0.3"))
            self.max_area_interval_var.set(config.get("max_area_interval", "0.7"))
            
            # 时间设置
            self.min_time_var.set(config.get("min_time", "1.0"))
            self.max_time_var.set(config.get("max_time", "3.0"))
            
            # 连续点击设置
            self.min_clicks_var.set(config.get("min_clicks", "1"))
            self.max_clicks_var.set(config.get("max_clicks", "3"))
            self.min_click_interval_var.set(config.get("min_click_interval", "0.05"))
            self.max_click_interval_var.set(config.get("max_click_interval", "0.2"))
            
            # 位置偏差设置
            self.no_offset_probability_var.set(config.get("no_offset_probability", "0.67"))
            self.x_offset_var.set(config.get("x_offset", "10"))
            self.y_offset_var.set(config.get("y_offset", "10"))
            
            # 运行限制设置
            self.duration_limit_var.set(config.get("duration_limit", False))
            self.duration_var.set(config.get("duration", "60"))
            self.unlimited_duration_var.set(config.get("unlimited_duration", True))
            self.count_limit_var.set(config.get("count_limit", False))
            self.max_total_clicks_var.set(config.get("max_total_clicks", "100"))
            self.unlimited_count_var.set(config.get("unlimited_count", False))
            
            # 更新界面状态
            self.toggle_duration_limit()
            self.toggle_count_limit()
            self.toggle_unlimited_duration()
            self.toggle_unlimited_count()
            
        except Exception as e:
            messagebox.showerror("错误", f"应用配置时发生错误: {str(e)}")
            
    def save_config(self):
        """保存当前配置"""
        config_name = self.config_name_var.get().strip()
        if not config_name:
            messagebox.showwarning("警告", "请输入配置名称")
            return
            
        # 检查配置名称是否合法
        if any(char in config_name for char in ['/', '\\', ':', '*', '?', '"', '<', '>', '|']):
            messagebox.showerror("错误", "配置名称不能包含特殊字符")
            return
            
        try:
            config = self.get_current_config()
            config_file = os.path.join(self.config_dir, f"{config_name}.json")
            
            # 如果文件已存在，询问是否覆盖
            if os.path.exists(config_file):
                if not messagebox.askyesno("确认", f"配置 '{config_name}' 已存在，是否覆盖？"):
                    return
                    
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
                
            messagebox.showinfo("成功", f"配置 '{config_name}' 保存成功")
            self.refresh_config_list()
            self.config_name_var.set("")  # 清空输入框
            
        except Exception as e:
            messagebox.showerror("错误", f"保存配置失败: {str(e)}")
            
    def load_config(self):
        """加载选中的配置"""
        config_name = self.config_list_var.get()
        if not config_name:
            messagebox.showwarning("警告", "请选择要加载的配置")
            return
            
        try:
            config_file = os.path.join(self.config_dir, f"{config_name}.json")
            if not os.path.exists(config_file):
                messagebox.showerror("错误", "配置文件不存在")
                self.refresh_config_list()
                return
                
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            self.apply_config(config)
            # 保存最后使用的配置名称
            self.save_last_used_config(config_name)
            messagebox.showinfo("成功", f"配置 '{config_name}' 加载成功")
            
        except Exception as e:
            messagebox.showerror("错误", f"加载配置失败: {str(e)}")
            
    def delete_config(self):
        """删除选中的配置"""
        config_name = self.config_list_var.get()
        if not config_name:
            messagebox.showwarning("警告", "请选择要删除的配置")
            return
            
        if not messagebox.askyesno("确认", f"确定要删除配置 '{config_name}' 吗？"):
            return
            
        try:
            config_file = os.path.join(self.config_dir, f"{config_name}.json")
            if os.path.exists(config_file):
                os.remove(config_file)
                messagebox.showinfo("成功", f"配置 '{config_name}' 删除成功")
                self.refresh_config_list()
            else:
                messagebox.showerror("错误", "配置文件不存在")
                self.refresh_config_list()
                
        except Exception as e:
            messagebox.showerror("错误", f"删除配置失败: {str(e)}")
            
    def refresh_config_list(self):
        """刷新配置列表"""
        try:
            if not os.path.exists(self.config_dir):
                os.makedirs(self.config_dir)
                
            config_files = [f[:-5] for f in os.listdir(self.config_dir) if f.endswith('.json')]
            config_files.sort()
            
            self.config_combobox['values'] = config_files
            
            # 尝试加载最后使用的配置
            last_used = self.get_last_used_config()
            if last_used and last_used in config_files:
                self.config_list_var.set(last_used)
            elif config_files and not self.config_list_var.get():
                self.config_list_var.set(config_files[0])
                
        except Exception as e:
            print(f"刷新配置列表失败: {str(e)}")
            
    def save_last_used_config(self, config_name):
        """保存最后使用的配置名称"""
        try:
            with open(self.last_config_file, 'w', encoding='utf-8') as f:
                f.write(config_name)
        except Exception as e:
            print(f"保存最后使用配置失败: {str(e)}")
            
    def get_last_used_config(self):
        """获取最后使用的配置名称"""
        try:
            if os.path.exists(self.last_config_file):
                with open(self.last_config_file, 'r', encoding='utf-8') as f:
                    return f.read().strip()
        except Exception as e:
            print(f"读取最后使用配置失败: {str(e)}")
        return None
        
    def load_last_used_config_on_startup(self):
        """启动时自动加载最后使用的配置"""
        last_used = self.get_last_used_config()
        if last_used:
            try:
                config_file = os.path.join(self.config_dir, f"{last_used}.json")
                if os.path.exists(config_file):
                    with open(config_file, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                    self.apply_config(config)
                    print(f"自动加载配置: {last_used}")
            except Exception as e:
                print(f"自动加载配置失败: {str(e)}")


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

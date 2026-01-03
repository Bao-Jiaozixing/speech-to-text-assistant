import tkinter as tk
from tkinter import ttk, scrolledtext
from vosk import Model, KaldiRecognizer
import pyaudio
import threading
import json

class SpeechToTextApp:
    def __init__(self, root):
        self.root = root
        self.root.title("语音转文字")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # 状态变量
        self.is_listening = False
        self.model = None
        self.rec = None
        self.p = None
        self.stream = None
        
        # 模型路径 - 使用简单方式确保能找到模型文件夹
        import os
        # 直接使用当前工作目录，程序会在当前目录查找vosk_model
        self.model_path = "vosk_model"
        
        # 创建UI组件
        self.create_widgets()
        
        # 加载模型
        self.load_model()
    
    def create_widgets(self):
        # 设置全局非框线字体 - 增大字体适合低视力老人
        self.root.option_add("*Font", "SimHei 24")  # 全局字体增大到24px
        
        # 设置窗口大小和位置 - 增大窗口尺寸
        self.root.geometry("1200x900")  # 增大窗口大小
        self.root.minsize(1000, 700)  # 设置更大的最小尺寸
        
        # 获取屏幕尺寸用于居中
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - 1200) // 2
        y = (screen_height - 900) // 2
        self.root.geometry(f"1200x900+{x}+{y}")  # 居中显示
        
        # 设置ttk样式
        style = ttk.Style()
        
        # 设置高对比度配色方案
        self.root.configure(bg="#ffffff")  # 纯白色背景，减少眼睛疲劳
        
        # 移除未使用的样式配置
        # 只保留ExtraLarge.TButton样式，在后续代码中定义
        
        # 移除了顶部的标题区域和模型状态显示，将在底部控制面板后添加
        
        # 主内容区域 - 使用grid布局，更精确控制高度比例
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 配置grid行和列
        # 转录区域，增大占比
        main_frame.grid_rowconfigure(0, weight=6, minsize=400)  # 增加权重到6，增大最小高度到400px
        main_frame.grid_rowconfigure(1, weight=1, minsize=150)  # 底部控制区域，保持权重1，减小最小高度到150px
        main_frame.grid_columnconfigure(0, weight=1)
        
        # 转录结果主框架 - 淡蓝色背景
        result_container = tk.Frame(
            main_frame, 
            bg="#e6f3ff",  # 淡蓝色背景
            relief=tk.RAISED,
            bd=2
        )
        result_container.grid(row=0, column=0, sticky="nsew", pady=0)
        
        # 实时文本标签 - 调整为3号字体
        result_title = tk.Label(
            result_container, 
            text="实时文本",
            font=("SimHei", 16, "bold"),  # 3号字体对应16px
            fg="#3498db",  # 醒目的蓝色
            bg="#e6f3ff"
        )
        result_title.pack(pady=15)
        
        # 转录结果文本框 - 进一步增大字体并使用醒目颜色
        self.result_text = scrolledtext.ScrolledText(
            result_container, 
            wrap=tk.WORD, 
            font=("SimHei", 50),  # 增大字体到50px，更醒目
            bg="#ffffff",  # 白色背景
            fg="#2c3e50",  # 深灰色文字，比纯黑更柔和但仍醒目
            relief=tk.SUNKEN,
            bd=4,  # 加粗边框，更清晰
            height=5,  # 保持5行，适应更大字体
            spacing1=15,  # 增加行间距到15
            spacing2=10,  # 增加段间距到10
            highlightthickness=4,  # 高亮边框厚度
            highlightbackground="#4a90e2",  # 高亮边框颜色
            cursor="arrow"  # 大箭头光标
        )
        self.result_text.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)  # 增大边距
        self.result_text.insert(tk.END, "等待录音...")
        
        # 配置滚动条样式 - 增大滚动条尺寸
        style = ttk.Style()
        style.configure("Vertical.TScrollbar", width=30)  # 增大垂直滚动条宽度
        style.configure("Horizontal.TScrollbar", height=30)  # 增大水平滚动条高度
        
        # 底部控制面板 - 包含所有按钮和设置，更紧凑的布局
        bottom_panel = tk.Frame(
            main_frame,  # 放在main_frame内，使用grid布局
            bg="#f0f0f0",
            relief=tk.RAISED,
            bd=2
        )
        # 使用grid布局，放在第二行
        bottom_panel.grid(row=1, column=0, sticky="nsew", padx=0, pady=10)
        
        # 设置区域 - 包含字体大小、句子数量和显示选项调节（减小占比）
        settings_frame = tk.Frame(bottom_panel, bg="#ffffff")
        settings_frame.pack(fill=tk.X, pady=5, padx=10)  # 减小边距
        
        # 第一行：字体大小和句子数量
        settings_row1 = tk.Frame(settings_frame, bg="#ffffff")
        settings_row1.pack(fill=tk.X, pady=2)  # 减小边距
        
        # 字体大小设置
        font_frame = ttk.Frame(settings_row1)
        font_frame.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)  # 减小边距
        
        ttk.Label(font_frame, text="字体:", font=("SimHei", 18, "bold"), foreground="#333333").pack(side=tk.LEFT, padx=3, pady=5)  # 减小字体和边距
        
        self.font_size_var = tk.IntVar()
        self.font_size_var.set(50)  # 当前字体大小
        
        font_scale = ttk.Scale(
            font_frame, 
            from_=20, to=70,  # 字体大小范围
            variable=self.font_size_var, 
            orient=tk.HORIZONTAL, 
            command=self.update_font_size,
            length=200  # 减小滑块长度
        )
        font_scale.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)  # 减小边距
        
        self.font_size_label = ttk.Label(font_frame, text="50px", font=("SimHei", 18, "bold"), foreground="#333333")
        self.font_size_label.pack(side=tk.LEFT, padx=3, pady=5)  # 减小字体和边距
        
        # 显示句子数量设置
        sentences_frame = ttk.Frame(settings_row1)
        sentences_frame.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)  # 减小边距
        
        ttk.Label(sentences_frame, text="句子数:", font=("SimHei", 18, "bold"), foreground="#333333").pack(side=tk.LEFT, padx=3, pady=5)  # 减小字体和边距
        
        self.max_sentences_var = tk.IntVar()
        self.max_sentences_var.set(3)  # 默认保存3条
        
        sentences_scale = ttk.Scale(
            sentences_frame, 
            from_=1, to=10,  # 句子数量范围
            variable=self.max_sentences_var, 
            orient=tk.HORIZONTAL, 
            command=self.update_sentences_count,
            length=200  # 减小滑块长度
        )
        sentences_scale.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)  # 减小边距
        
        self.sentences_label = ttk.Label(sentences_frame, text="3", font=("SimHei", 18, "bold"), foreground="#333333")
        self.sentences_label.pack(side=tk.LEFT, padx=3, pady=5)  # 减小字体和边距
        
        # 第二行：显示部分结果选项（减小占比）
        settings_row2 = tk.Frame(settings_frame, bg="#ffffff")
        settings_row2.pack(fill=tk.X, pady=2)  # 减小边距
        
        # 显示部分结果复选框
        partial_frame = tk.Frame(settings_row2, bg="#ffffff")
        partial_frame.pack(side=tk.LEFT, padx=5, pady=5)  # 减小边距
        
        ttk.Label(partial_frame, text="显示部分结果", font=("SimHei", 18, "bold"), foreground="#333333").pack(side=tk.LEFT, padx=5, pady=3)  # 减小字体和边距，去掉冒号
        
        self.show_partial_var = tk.BooleanVar()
        self.show_partial_var.set(False)  # 默认不显示部分结果，只显示整句
        
        partial_check = ttk.Checkbutton(
            partial_frame, 
            variable=self.show_partial_var,
            text="",
            style="Small.TCheckbutton"
        )
        partial_check.pack(side=tk.LEFT, padx=5, pady=3)  # 减小边距
        
        # 设置复选框样式
        style = ttk.Style()
        style.configure("Small.TCheckbutton", font=("SimHei", 18))  # 减小字体
        
        # 添加标题和模型状态显示（移到此处，减小占比）
        info_frame = tk.Frame(bottom_panel, bg="#e6f3ff", relief=tk.RAISED, bd=2)
        info_frame.pack(fill=tk.X, pady=5, padx=10)  # 减小边距
        
        # 标题 - 减小字体
        title_label = tk.Label(
            info_frame, 
            text="语音转文字", 
            font=("SimHei", 24, "bold"),  # 减小字号到24px
            fg="#e74c3c",  # 醒目的红色
            bg="#e6f3ff"  # 淡蓝色背景
        )
        title_label.pack(pady=5)  # 减小边距
        
        # 模型状态显示 - 减小字体
        self.model_status_var = tk.StringVar()
        self.model_status_var.set("正在加载模型...")
        model_status_label = tk.Label(
            info_frame, 
            textvariable=self.model_status_var, 
            font=("SimHei", 16, "bold"),  # 减小字体到16px
            fg="#27ae60",  # 绿色文字，醒目
            bg="#e6f3ff"
        )
        model_status_label.pack(pady=2, padx=10)  # 减小边距
        
        # 按钮区域 - 减小占比
        button_frame = tk.Frame(bottom_panel, bg="#ffffff")
        button_frame.pack(fill=tk.X, pady=10, padx=10)  # 减小边距
        
        # 设置按钮样式，适当减小尺寸
        style = ttk.Style()
        style.configure(
            "Medium.TButton", 
            font=("SimHei", 24, "bold"),  # 减小按钮字体到24px，加粗
            padding=15,  # 减小按钮内边距到15px
            width=12,  # 减小按钮宽度到12
            background="#4a90e2",  # 蓝色背景
            foreground="#000000",  # 黑色文字
            borderwidth=2,  # 减小边框宽度到2
            relief="raised"  # 凸起效果
        )
        
        # 按钮悬停效果
        style.map(
            "Medium.TButton",
            background=[("active", "#357abd")],  # 悬停时颜色加深
            foreground=[("active", "#000000")]  # 悬停时保持黑色文字
        )
        
        # 左侧：开始/停止按钮
        self.start_stop_btn = ttk.Button(
            button_frame, 
            text="开始录音", 
            command=self.toggle_listening,
            style="Medium.TButton"
        )
        self.start_stop_btn.pack(side=tk.LEFT, padx=15, expand=True, fill=tk.BOTH)  # 减小边距
        
        # 右侧：清空文本按钮
        self.clear_btn = ttk.Button(
            button_frame, 
            text="清空文本", 
            command=self.clear_text,
            style="Medium.TButton"
        )
        self.clear_btn.pack(side=tk.RIGHT, padx=15, expand=True, fill=tk.BOTH)  # 减小边距
        
        # 添加全屏功能
        self.is_fullscreen = False
        self.root.bind("<F11>", self.toggle_fullscreen)
        self.root.bind("<Escape>", self.exit_fullscreen)
    
    def load_model(self):
        """加载Vosk模型"""
        def _load_model():
            try:
                self.model = Model(self.model_path)
                self.rec = KaldiRecognizer(self.model, 16000)
                self.model_status_var.set(f"模型加载成功: {self.model_path}")
            except Exception as e:
                self.model_status_var.set(f"模型加载失败: {str(e)}")
        
        # 在后台线程加载模型，避免UI卡顿
        threading.Thread(target=_load_model, daemon=True).start()
    
    def toggle_listening(self):
        """开始/停止录音"""
        if self.is_listening:
            self.stop_listening()
        else:
            self.start_listening()
    
    def start_listening(self):
        """开始录音"""
        if not self.model:
            # 模型未加载时，更新模型状态提示
            self.model_status_var.set("模型未加载，无法开始录音")
            return
        
        try:
            self.p = pyaudio.PyAudio()
            self.stream = self.p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=8000
            )
            self.stream.start_stream()
            
            self.is_listening = True
            self.start_stop_btn.config(text="停止录音")
            
            # 清空初始文本
            if self.result_text.get(1.0, tk.END).strip() == "等待录音...":
                self.result_text.delete(1.0, tk.END)
            
            # 在后台线程处理录音
            threading.Thread(target=self.process_audio, daemon=True).start()
        except Exception as e:
            # 发生错误时，停止录音并更新模型状态
            self.is_listening = False
            self.start_stop_btn.config(text="开始录音")
            self.model_status_var.set(f"录音错误: {str(e)}")
    
    def stop_listening(self):
        """停止录音"""
        self.is_listening = False
        self.start_stop_btn.config(text="开始录音")
        
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        
        if self.p:
            self.p.terminate()
    
    def process_audio(self):
        """处理音频流"""
        while self.is_listening:
            try:
                data = self.stream.read(4000, exception_on_overflow=False)
                if self.rec.AcceptWaveform(data):
                    result = self.rec.Result()
                    self.update_final_result(result)
                else:
                    partial = self.rec.PartialResult()
                    self.update_partial_result(partial)
            except Exception as e:
                # 发生错误时，停止录音
                self.is_listening = False
                self.start_stop_btn.config(text="开始录音")
                break
    
    def update_final_result(self, result):
        """更新最终识别结果"""
        import json
        result_dict = json.loads(result)
        text = result_dict.get("text", "")
        
        if text:
            # 获取当前显示的文本
            current_text = self.result_text.get(1.0, tk.END).strip()
            
            # 如果是初始状态，直接替换
            if current_text == "等待录音...":
                self.result_text.delete(1.0, tk.END)
                self.result_text.insert(tk.END, text + "\n")
            else:
                # 移除最后一行的临时结果
                lines = current_text.split("\n")
                if lines and lines[-1].startswith("临时:"):
                    lines = lines[:-1]
                
                # 添加新的结果
                lines.append(text)
                
                # 根据设置显示最近N个句子
                lines = lines[-self.max_sentences_var.get():]
                
                # 更新显示
                self.result_text.delete(1.0, tk.END)
                self.result_text.insert(tk.END, "\n".join(lines) + "\n")
    
    def update_partial_result(self, partial):
        """更新临时识别结果"""
        import json
        partial_dict = json.loads(partial)
        text = partial_dict.get("partial", "")
        
        # 检查是否需要显示部分结果
        if not self.show_partial_var.get() or not text:
            return
        
        # 获取当前显示的文本
        current_text = self.result_text.get(1.0, tk.END).strip()
        
        # 移除最后一行的临时结果
        lines = current_text.split("\n")
        if lines and lines[-1].startswith("临时:"):
            lines = lines[:-1]
        
        # 添加临时结果
        lines.append(f"临时: {text}")
        
        # 更新显示
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, "\n".join(lines))
    
    def update_font_size(self, value):
        """更新字体大小"""
        font_size = int(float(value))
        self.font_size_label.config(text=f"{font_size}px")
        self.result_text.config(font=("SimHei", font_size))
    
    def update_sentences_count(self, value):
        """更新保存句子数量"""
        sentences_count = int(float(value))
        self.sentences_label.config(text=str(sentences_count))
        self.max_sentences_var.set(sentences_count)
    
    def clear_text(self):
        """清空转录结果"""
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, "等待录音...")
    
    def toggle_fullscreen(self, event=None):
        """切换全屏模式"""
        self.is_fullscreen = not self.is_fullscreen
        self.root.attributes('-fullscreen', self.is_fullscreen)
        # 全屏时隐藏窗口边框和标题栏
        self.root.attributes('-topmost', self.is_fullscreen)
        self.root.update()
    
    def exit_fullscreen(self, event=None):
        """退出全屏模式"""
        self.is_fullscreen = False
        self.root.attributes('-fullscreen', False)
        self.root.attributes('-topmost', False)
        self.root.update()

# 运行应用程序
if __name__ == "__main__":
    root = tk.Tk()
    app = SpeechToTextApp(root)
    root.mainloop()
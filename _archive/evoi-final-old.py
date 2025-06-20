#!/usr/bin/env python3
"""
EVOI多狀態交易時鐘 v4.1 - Antonio字體最終版
恢復使用 Antonio 字體，並完成最終外觀打磨。

核心功能保持：
✅ 三種模式自動切換 (Normal/NYAM/Quote)
✅ NYAM時段K棒倒數計時
✅ 全金句庫依序輪播系統 (含推播動畫)
✅ 快捷鍵控制 (F12/Esc)
✅ 拖拽移動 + 置頂顯示

UI/UX 調整：
🎨 全局統一淺灰色背景
🎨 NYAM模式採金色主題 (邊框+文字)
🎨 Quote模式採黑色文字，風格簡潔
✒️ 數字字體確認為 Antonio (Regular)，移除粗體
🔒 視窗大小固定為 350x140，不可調整
"""

import tkinter as tk
from tkinter import font
import datetime
import random
import platform
import sys
import cnlunar

class ModernFontManager:
    """現代化字體管理器 (移除粗體)"""
    def __init__(self):
        self.fonts = self._load_fonts()
        
    def _load_fonts(self):
        system = platform.system()
        if system == "Darwin":
            return {'primary': 'SF Pro Display', 'mono': 'Antonio'}
        elif system == "Windows":
            return {'primary': 'Segoe UI', 'mono': 'Antonio'}
        else:
            return {'primary': 'Inter', 'mono': 'JetBrains Mono'}
            
    def get_font(self, font_type, size, **kwargs):
        family = self.fonts.get(font_type, 'Arial')
        try:
            return font.Font(family=family, size=size, **kwargs)
        except tk.TclError:
            return font.Font(family='TkDefaultFont', size=size, **kwargs)

class StaticDigit:
    """靜態的數字卡片，擁有翻頁時鐘的外觀但沒有動畫"""
    def __init__(self, parent, font_manager, height):
        self.font_manager = font_manager
        self.bg_color = '#000000'
        
        self.height = height
        self.width = int(height * 0.5) # 嚴格的 1:2 瘦長比例

        self.canvas = tk.Canvas(parent, width=self.width, height=self.height, bg=parent.cget("bg"), highlightthickness=0)
        
        self.card = self.canvas.create_rectangle(0, 0, self.width, self.height, fill=self.bg_color, outline="")
        self.text_item = self.canvas.create_text(self.width/2, self.height/2, text='0', fill='#ffffff', anchor='center')
        self.line = self.canvas.create_line(0, self.height/2, self.width, self.height/2, fill=parent.cget("bg"), width=2)
        
        self.current_value = '0'
        self.set_font_size(self.height)

    def set_font_size(self, size):
        self.height = size
        self.width = int(size * 0.5) # 嚴格的 1:2 瘦長比例
        self.canvas.config(width=self.width, height=self.height)
        
        font_size = int(self.height * 0.9) # 調整字體大小以適應
        font = self.font_manager.get_font('mono', font_size) # 移除 weight='bold'
        self.canvas.itemconfig(self.text_item, font=font)
        
        self.canvas.coords(self.card, 0, 0, self.width, self.height)
        self.canvas.coords(self.text_item, self.width/2, self.height/2)
        self.canvas.coords(self.line, 0, self.height/2, self.width, self.height/2)
    
    def update_value(self, new_value):
        new_value = str(new_value)
        if new_value != self.current_value:
            self.current_value = new_value
            self.canvas.itemconfig(self.text_item, text=new_value)

    def set_theme(self, bg_color, fg_color):
        self.canvas.config(bg=bg_color)
        self.canvas.itemconfig(self.line, fill=bg_color)
        self.canvas.itemconfig(self.text_item, fill=fg_color)


class ColonDisplay:
    """靜態的冒號卡片，外觀與數字卡片統一"""
    def __init__(self, parent, font_manager, height):
        self.font_manager = font_manager
        self.bg_color = '#000000'
        
        self.height = height
        self.width = int(height * 0.5)

        self.canvas = tk.Canvas(parent, width=self.width, height=self.height, bg=parent.cget("bg"), highlightthickness=0)
        
        self.card = self.canvas.create_rectangle(0, 0, self.width, self.height, fill=self.bg_color, outline="")
        self.dots_text = self.canvas.create_text(self.width/2, self.height/2, text="•\n•", fill='#ffffff', anchor='center', justify='center')
        
        self.set_font_size(self.height)

    def set_font_size(self, size):
        self.height = size
        self.width = int(size * 0.5)
        self.canvas.config(width=self.width, height=self.height)
        
        font_size = int(self.height * 0.4)
        font = self.font_manager.get_font('mono', font_size)
        self.canvas.itemconfig(self.dots_text, font=font)
        
        self.canvas.coords(self.card, 0, 0, self.width, self.height)
        self.canvas.coords(self.dots_text, self.width/2, self.height/2)
    
    def set_theme(self, bg_color, fg_color):
        self.canvas.config(bg=bg_color)
        self.canvas.itemconfig(self.dots_text, fill=fg_color)


class EVOIMultiStateClock:
    def __init__(self):
        self.font_manager = ModernFontManager()
        self.root = tk.Tk()
        
        self.digit_height = 70 # 固定數字高度

        self.current_mode = 'normal'
        self.animation_running = False
        self.drag_data = {"x": 0, "y": 0}

        self.themes = {
            'normal': {'bg': '#f0f0f0', 'border': '#f0f0f0', 'subtitle': '#000000'},
            'nyam':   {'bg': '#f0f0f0', 'border': '#ffd700', 'subtitle': '#ffd700'},
            'quote':  {'bg': '#f0f0f0', 'border': '#f0f0f0', 'subtitle': '#000000'}
        }
        
        self.setup_window()
        
        self.trading_quotes = [
            '三單停手不貪法', '定時定法定量好', '跟隨鯊魚去交易', '展開運鈔車人生',
            '機構創造流動性', '機構清除流動性', '機構創造不平衡', '機構平衡不平衡',
            '建立盤前偏見', '識別鯊魚覓食區', '建立盤中方向', '識別鯊魚去那裡',
            '一單一口不用貪', '連輸二單必停手', '頭頭高底底高', '頭頭低底底低',
            '上漲盤整猜上漲', '下跌盤整猜下跌', '識別慣性要練習', '慣性延續不要怕',
            '慣性改變有線索', '二百美金真的夠', '細水常流比氣長',
            '我是來市場賺錢', '不是來賭場輸錢'
        ]
        self.global_quote_index = 0
        self.quote_job = None

        self.weekdays_map = ["週一", "週二", "週三", "週四", "週五", "週六", "週日"]

        self.setup_ui()
        self.setup_bindings()
        self.start_clock()

    def setup_window(self):
        self.root.geometry("350x140+100+100") # 固定視窗大小
        self.root.title('EVOI NYAM 三單不貪停手')
        self.root.resizable(False, False)
        self.root.attributes('-topmost', True)
        self.root.config(bg=self.themes['normal']['bg'])

    def setup_ui(self):
        self.root.config(bg=self.themes['normal']['bg'])

        self.subtitle_label = tk.Label(
            self.root, text="", font=self.font_manager.get_font('primary', 14),
            fg=self.themes['normal']['subtitle'], bg=self.themes['normal']['bg']
        )
        self.subtitle_label.pack(pady=(8, 4))

        # --- Main area for switching between clock and quote ---
        self.main_area = tk.Frame(self.root, bg=self.themes['normal']['bg'])
        self.main_area.pack(fill="both", expand=True)

        # --- Quote container (placed first, will be in the back initially) ---
        self.quote_container = tk.Frame(self.main_area, bg=self.themes['normal']['bg'])
        self.quote_container.place(relx=0.5, rely=0.5, anchor='center')
        self.quote_display_label = tk.Label(
            self.quote_container, text="", font=self.font_manager.get_font('primary', 30),
            fg=self.themes['quote']['subtitle'], bg=self.themes['quote']['bg'],
            wraplength=320, justify='center'
        )
        self.quote_display_label.pack(pady=10)

        # --- Clock frame (placed on top) ---
        self.clock_frame = tk.Frame(self.main_area, bg=self.themes['normal']['bg'])
        self.clock_frame.place(relx=0.5, rely=0.5, anchor='center')
        
        self.digits = {}
        comp_map = ['h1', 'h2', 'c1', 'm1', 'm2', 'c2', 's1', 's2']
        for comp_id in comp_map:
            is_colon = comp_id.startswith('c')
            if is_colon:
                self.digits[comp_id] = ColonDisplay(self.clock_frame, self.font_manager, self.digit_height)
                self.digits[comp_id].canvas.pack(side='left', padx=1)
            else:
                self.digits[comp_id] = StaticDigit(self.clock_frame, self.font_manager, self.digit_height)
                self.digits[comp_id].canvas.pack(side='left', padx=1)
        
        self.clock_frame.tkraise()

    def on_resize(self, event):
        pass

    def setup_bindings(self):
        widgets_to_bind = [
            self.root, self.subtitle_label, self.main_area, 
            self.clock_frame, self.quote_container, self.quote_display_label
        ]
        for widget in widgets_to_bind:
            widget.bind("<Button-1>", self.start_drag)
            widget.bind("<B1-Motion>", self.do_drag)
        
        for digit in self.digits.values():
            widget = getattr(digit, 'canvas', getattr(digit, 'label', None))
            if widget:
                widget.bind("<Button-1>", self.start_drag)
                widget.bind("<B1-Motion>", self.do_drag)

        self.root.bind('<KeyPress>', self.on_key_press)

    def start_drag(self, event):
        self.drag_data["x"] = event.x_root - self.root.winfo_x()
        self.drag_data["y"] = event.y_root - self.root.winfo_y()
        
    def do_drag(self, event):
        self.root.geometry(f"+{event.x_root - self.drag_data['x']}+{event.y_root - self.drag_data['y']}")

    def on_key_press(self, event):
        if event.keysym == 'F12': self.toggle_visibility()
        elif event.keysym == 'Escape': self.root.quit()
            
    def toggle_visibility(self):
        if self.root.winfo_viewable(): self.root.withdraw()
        else: self.root.deiconify()

    def is_nyam_time(self, now): return 1290 <= now.hour * 60 + now.minute < 1380
    def is_quote_time(self, now): return now.minute % 10 == 0 and now.second < 60

    def get_clock_mode(self, now):
        if self.is_nyam_time(now): return 'nyam'
        if self.is_quote_time(now): return 'quote'
        return 'normal'
    
    def start_quote_mode(self):
        self.current_mode = 'quote'
        self.apply_theme('quote')
        self.quote_container.tkraise()
        self.schedule_next_quote(first_run=True)

    def schedule_next_quote(self, first_run=False):
        if self.current_mode != 'quote': return
        new_quote = self.trading_quotes[self.global_quote_index]
        self.global_quote_index = (self.global_quote_index + 1) % len(self.trading_quotes)
        
        if first_run:
            self.quote_display_label.config(text=new_quote)
        else:
            self.animate_quote_transition(new_quote)
        
        self.quote_job = self.root.after(5000, self.schedule_next_quote)

    def animate_quote_transition(self, new_text):
        old_label = self.quote_display_label
        
        new_label = tk.Label(
            self.quote_container, text=new_text, font=self.font_manager.get_font('primary', 30),
            fg=self.themes['quote']['subtitle'], bg=self.themes['quote']['bg'],
            wraplength=self.root.winfo_width() - 40, justify='center'
        )
        new_label.place(relx=0.5, rely=1.5, anchor='center')

        self.quote_display_label = new_label

        def step(pos_fraction):
            if pos_fraction > 1.0:
                old_label.destroy()
                new_label.place(relx=0.5, rely=0.5, anchor='center')
                return

            new_y = 1.5 - pos_fraction
            old_y = 0.5 - pos_fraction
            
            new_label.place(relx=0.5, rely=new_y, anchor='center')
            old_label.place(relx=0.5, rely=old_y, anchor='center')
            
            self.root.after(15, lambda: step(pos_fraction + 0.05))
        
        step(0.0)

    def end_quote_mode(self):
        if self.quote_job:
            self.root.after_cancel(self.quote_job)
            self.quote_job = None
        self.current_mode = 'normal'
        self.clock_frame.tkraise()
        self.apply_theme('normal')

    def apply_theme(self, theme_name):
        theme = self.themes[theme_name]
        self.root.config(bg=theme['bg'])
        self.subtitle_label.config(bg=theme['bg'], fg=theme['subtitle'])
        
        if hasattr(self, 'main_area'):
            self.main_area.config(bg=theme['bg'])
        if hasattr(self, 'quote_container'):
            self.quote_container.config(bg=theme['bg'])
        if hasattr(self, 'quote_display_label'):
             self.quote_display_label.config(bg=theme['bg'], fg=theme['subtitle'])

        self.clock_frame.config(bg=theme['bg'])

        digit_fg_color = '#ffd700' if theme_name == 'nyam' else '#ffffff'
        colon_fg_color = digit_fg_color # 冒號顏色與數字顏色統一

        for comp_id, digit_obj in self.digits.items():
            if comp_id.startswith('c'):
                digit_obj.set_theme(bg_color=theme['bg'], fg_color=colon_fg_color)
            else:
                digit_obj.set_theme(bg_color=theme['bg'], fg_color=digit_fg_color)
        
        border_width = 3 if theme_name == 'nyam' else 0
        
        self.root.config(highlightbackground=theme['border'], highlightthickness=border_width)

    def update_time_display(self, time_str):
        h, m, s = time_str.split(':')
        self.digits['h1'].update_value(h[0])
        self.digits['h2'].update_value(h[1])
        self.digits['m1'].update_value(m[0])
        self.digits['m2'].update_value(m[1])
        self.digits['s1'].update_value(s[0])
        self.digits['s2'].update_value(s[1])

    def update_nyam_clock(self, now):
        self.update_time_display(now.strftime("%H:%M:%S"))
        seconds_to_next = 60 - now.second
        self.subtitle_label.config(text=f"下一K棒: {seconds_to_next}s")
        self.handle_stage_warning(seconds_to_next)

    def update_normal_clock(self, now):
        """更新正常時鐘 (加入農曆/節氣)"""
        self.update_time_display(now.strftime("%H:%M:%S"))

        lunar_date = cnlunar.Lunar(now)
        lunar_str = lunar_date.lunarMonthCn + lunar_date.lunarDayCn
        jq_str = f" {lunar_date.todaySolarTerms}" if lunar_date.todaySolarTerms and lunar_date.todaySolarTerms != '无' else ""
        weekday_str = lunar_date.weekDayCn
        
        date_display = f"{lunar_str} {weekday_str}{jq_str}"
        self.subtitle_label.config(text=date_display)

    def update_quote_clock(self, now):
        self.subtitle_label.config(text=now.strftime('%Y-%m-%d %H:%M:%S'))
        if not self.is_quote_time(now):
            self.end_quote_mode()

    def handle_stage_warning(self, seconds_to_next):
        if seconds_to_next <= 3:
            if not self.animation_running: self.start_warning_animation('#ff5252')
        else:
            self.stop_warning_animation()
            
    def start_warning_animation(self, color):
        self.animation_running = True
        self.animate_border(color, 0)
            
    def animate_border(self, color, count):
        if not self.animation_running or count >= 6:
            self.animation_running = False
            self.apply_theme(self.current_mode)
            return
        
        current_border = self.themes[self.current_mode]['border']
        border_color = color if count % 2 == 0 else current_border
        
        self.root.config(highlightbackground=border_color, highlightthickness=3)
        self.root.after(200, lambda: self.animate_border(color, count + 1))
        
    def stop_warning_animation(self):
        if self.animation_running:
            self.animation_running = False
            self.apply_theme(self.current_mode)

    def update_clock(self):
        try:
            now = datetime.datetime.now()
            new_mode = self.get_clock_mode(now)

            if new_mode != self.current_mode:
                if self.current_mode == 'quote': self.end_quote_mode()
                
                if new_mode == 'quote':
                    self.start_quote_mode()
                else: 
                    self.current_mode = new_mode
                    self.apply_theme(new_mode)

            if self.current_mode == 'nyam': self.update_nyam_clock(now)
            elif self.current_mode == 'normal': self.update_normal_clock(now)
            elif self.current_mode == 'quote': self.update_quote_clock(now)

        except Exception as e:
            print(f"❌ 更新錯誤: {e}")
            self.root.after(1000, self.update_clock)
        else:
            self.root.after(100, self.update_clock)

    def start_clock(self):
        print("🚀 EVOI多狀態交易時鐘 v4.1 - Antonio字體最終版啟動")
        now = datetime.datetime.now()
        initial_mode = self.get_clock_mode(now)
        if initial_mode == 'quote':
            self.start_quote_mode()
        else:
            self.current_mode = initial_mode
            self.apply_theme(initial_mode)
        self.update_clock()
        
    def run(self):
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        self.root.mainloop()

if __name__ == "__main__":
    if platform.system() == "Darwin":
        try:
            root = tk.Tk()
            root.withdraw()
            fonts = list(font.families())
            if "Antonio" not in fonts:
                print("⚠️ 警告：未找到 'Antonio' 字體，將使用預設字體。")
                print("   請確認字體是否已正確安裝並在 Font Book 中啟用。")
            root.destroy()
        except Exception:
            pass

    app = EVOIMultiStateClock()
    app.run()
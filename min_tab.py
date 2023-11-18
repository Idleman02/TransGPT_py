import os
import threading
import wave
from datetime import datetime

import chatglm_cpp
import openai
from openai import OpenAI
import pyaudio
from PySide6 import QtWidgets, QtGui
from PySide6.QtCore import Signal
from PySide6.QtCore import Slot, QTimer
from PySide6.QtGui import QIcon, QClipboard

# 管理主应用程序窗口，处理与GPT模型的消息交换
class MinTab(QtWidgets.QWidget):
    update_chat_log_signal = Signal(str, str)    # 传递聊天信息更新的信号，包括内容和发送者

    def __init__(self, api_key, api, language, style):
        super().__init__()
        self.language = language
        self.selected_api = api
        self.api_key = api_key
        self.selected_style = style

        # 获取剪贴板实例
        self.clipboard = QClipboard()

        # 上一次剪贴板内容
        self.last_clipboard_text = ""

        # 使用定时器实时监测剪贴板内容
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_clipboard)
        self.timer.start(1000)  # 设置定时器间隔（毫秒）

        # 用于显示聊天记录的文本框
        self.chat_log = QtWidgets.QTextEdit(self)
        self.chat_log.setReadOnly(True)
        normal_height_log = self.chat_log.sizeHint().height()
        self.chat_log.setFixedHeight(normal_height_log * 1.6)

        # 功能按钮
        self.export_button = QtWidgets.QPushButton("Export", self)
        self.clear_button = QtWidgets.QPushButton("Clear", self)

        # 整体GUI布局
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addWidget(self.chat_log)

        self.button_layout = QtWidgets.QHBoxLayout()
        self.button_layout.addWidget(self.export_button)
        self.button_layout.addWidget(self.clear_button)
        self.layout.addLayout(self.button_layout)

        # 设置按钮外观
        self.demo_ui()

        self.update_chat_log_signal.connect(self.update_chat_log)
        self.export_button.clicked.connect(self.export_chat)
        self.clear_button.clicked.connect(self.clear)

    @Slot()
    def check_clipboard(self):
        clipboard_text = self.clipboard.text()
        if clipboard_text != self.last_clipboard_text:
            # 如果剪贴板中的文本与上一次不同，执行翻译
            self.translate(clipboard_text)
            self.last_clipboard_text = clipboard_text

    # 翻译功能
    @Slot()
    def translate(self, message):
        if not message:
            return  # 如果没有输入，返回

        selected_language = self.language
        selected_style = self.selected_style
        request = f"Please translate the following sentence to {selected_language}，use {selected_style} translation style, and give me translation outcome without anything else: {message}"
        self.update_chat_log_signal.emit(message, "user")

        try:
            if self.selected_api == "local model":
                message_thread = threading.Thread(target=self.local_translate_message, args=(request,))
            else:
                message_thread = threading.Thread(target=self.translate_message, args=(request,))
            message_thread.start()
        except Exception as e:
            print(f"Exception in translate: {str(e)}")

    # 调用api让gpt翻译
    def translate_message(self, message):
        try:
            user_message = {"role": "user", "content": message}
            # openai.api_key = self.api_key  # Set the OpenAI API key
            client = OpenAI(api_key = self.api_key)
            response = client.chat.completions.create(
                model=self.selected_api,
                messages=[user_message],  # Use the conversation history
                stream=True
            )

            self.update_chat_log_signal.emit("", "gpt-start-translation")
            for chunk in response:  # 遍历数据流的事件
                chunk_message = chunk.choices[0].delta.content # 提取消息
                if chunk_message is not None:
                    self.update_chat_log_signal.emit(chunk_message, "gpt-translation")
            # response_text = response.choices[0].message.content
            # self.update_chat_log_signal.emit(response_text, "gpt-translation")
            self.update_chat_log_signal.emit("", "gpt-end-translation")


        except Exception as e:
            error_msg = f"Error: {str(e)}"
            # Emit the signal to update the chat log with the error message
            self.update_chat_log_signal.emit(error_msg, "error")

    # 让部署在本地的ChatGLM-3 模型翻译
    def local_translate_message(self, message, max_length=2048, max_context_length=512, top_k=0, top_p=0.7, temp=0.95,
                                repeat_penalty=1.0):
        try:
            pipeline = chatglm_cpp.Pipeline(self.model_path)
            # 2. 定义生成参数
            generation_kwargs = dict(
                max_length=max_length,
                max_context_length=max_context_length,
                do_sample=temp > 0,
                top_k=top_k,
                top_p=top_p,
                temperature=temp,
                repetition_penalty=repeat_penalty,
                stream=True,
            )

            self.update_chat_log_signal.emit("", "gpt-start-translation")
            for response_text in pipeline.chat([message], **generation_kwargs):
                self.update_chat_log_signal.emit(response_text, "gpt")
            self.update_chat_log_signal.emit("", "gpt-end-translation")

        except Exception as e:
            error_msg = f"Error: {str(e)}"
            # Emit the signal to update the chat log with the error message
            self.update_chat_log_signal.emit(error_msg, "error")

    # 导出聊天记录为.txt文件
    @Slot()
    def export_chat(self):
        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%d-%H-%M-%S")
        file_name = f"chat_{timestamp}.txt"  # 文件名为chat_时间戳.txt

        try:
            with open(file_name, "w") as f:
                f.write(self.chat_log.toPlainText())
            QtWidgets.QMessageBox.information(
                self, "Export Successful", f"The chat has been exported to {file_name}."
            )
        except Exception as e:
            # 错误处理
            QtWidgets.QMessageBox.critical(
                self,
                "Export Error",
                f"An error occurred while exporting the chat: {str(e)}",
            )

    # 清空聊天记录
    @Slot()
    def clear(self):
        self.chat_log.clear()

    
    # 更新聊天记录并设置外观颜色
    @Slot(str, str)
    def update_chat_log(self, message, message_type):
        response_cursor = self.chat_log.textCursor()
        if message_type == "user":
            response_cursor.insertHtml("<span style='color: black; font-style: italic;'>You: </span>")
            response_cursor.insertText(f"{message}\n\n")
        elif message_type == "gpt-start":
            response_cursor.insertHtml("<span style='color: green;'>GPT: </span>")
            response_cursor.insertText(f"{message}")
        elif message_type == "gpt":
            response_cursor.insertHtml("<span style='color: green;'> </span>")
            response_cursor.insertText(f"{message}")
        elif message_type == "gpt-end":
            response_cursor.insertHtml("<span style='color: green;'> </span>")
            response_cursor.insertText(f"{message}\n\n")
        elif message_type == "gpt-start-translation":
            response_cursor.insertHtml("<span style='color: blue;'>GPT: </span>")
            response_cursor.insertText(f"{message}")
        elif message_type == "gpt-translation":
            response_cursor.insertHtml("<span style='color: blue;'> </span>")
            response_cursor.insertText(f"{message}")
        elif message_type == "gpt-end-translation":
            response_cursor.insertHtml("<span style='color: blue;'> </span>")
            response_cursor.insertText(f"{message}\n\n")
        elif message_type == "error":
            response_cursor.insertHtml("<span style='color: red;'>ERROR: </span>")
            response_cursor.insertText(f"{message}\n\n")

    # 设置按钮样式
    def demo_ui(self):
        self.chat_log.setStyleSheet("""
                            QTextEdit {
                                border: 2px solid black;
                                border-radius: 10px;
                                padding: 8px;
                                font-size: 16px;
                            }
                            QScrollBar:vertical {
                                border: 1px solid #696969;
                                background: #FFFFFF;
                                width: 10px; /* 调整滚动条宽度为10像素 */
                                margin: 22px 0 22px 0;
                                border-radius: 4px;
                            }
                            QScrollBar::handle:vertical {
                                background: #696969;
                                min-height: 20px;
                                border-radius: 4px;
                            }
                            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                                border: 1px solid grey;
                                background: #696969;
                                height: 15px;
                                border-radius: 4px;
                                subcontrol-origin: margin;
                            }
                            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                                background: none;
                            }
                        """)


        self.export_button.setStyleSheet("""
                            QPushButton {
                                background-color: #003366;  /* Dark Blue */
                                color: #FFFFFF;  /* White */
                                border: 2px solid #5F9E6E;  /* Dark Sea Green */
                                border-radius: 15px;  /* Rounded corners */
                                padding: 10px 25px;  /* Padding: vertical, horizontal */
                                font-size: 16px;  /* Text size */
                                font-family: "Arial";  /* Font family */
                            }
                            QPushButton:hover {
                                background-color: #336699;  /* Lighter Dark Blue */
                                border: 2px solid #20B2AA;  /* Light Sea Green */
                            }
                            QPushButton:pressed {
                                background-color: #6699CC;  /* Even Lighter Dark Blue */
                                border: 2px solid #3CB371;  /* Medium Sea Green */
                            }
                            QPushButton:disabled {
                                color: #D3D3D3;  /* Light Gray text when disabled */
                                border: 2px solid #D3D3D3;  /* Light Gray border when disabled */
                                background-color: #A9A9A9;  /* Dark Gray background when disabled */
                            }
                        """)

        # 对clear_button的优化
        self.clear_button.setStyleSheet("""
                    QPushButton {
                        background-color: #DD4132;  /* Tomato Red */
                        color: #FFFFFF;  /* White */
                        border: 2px solid #FAE03C;  /* Daffodil Yellow */
                        border-radius: 15px;  /* Rounded corners */
                        padding: 10px 25px;  /* Padding: vertical, horizontal */
                        font-size: 16px;  /* Text size */
                        font-family: "Arial";  /* Font family */
                    }
                    QPushButton:hover {
                        background-color: #E94E77;  /* Pink */
                        border: 2px solid #FFD662;  /* Sunflower Yellow */
                    }
                    QPushButton:pressed {
                        background-color: #D2386C;  /* Rose */
                        border: 2px solid #ECC81A;  /* Golden Poppy */
                    }
                    QPushButton:disabled {
                        color: #D3D3D3;  /* Light Gray text when disabled */
                        border: 2px solid #D3D3D3;  /* Light Gray border when disabled */
                        background-color: #A9A9A9;  /* Dark Gray background when disabled */
                    }
                """)
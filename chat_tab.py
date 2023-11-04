import threading
import wave
import os
from datetime import datetime

import chatglm_cpp
import openai
import pyaudio
from PySide6 import QtWidgets, QtGui
from PySide6.QtCore import Signal
from PySide6.QtCore import Slot
from PySide6.QtGui import QIcon


class ChatTab(QtWidgets.QWidget):
    update_chat_log_signal = Signal(str, str)
    set_button_state_signal = Signal(bool)
    set_api_button_state_signal = Signal(bool)
    def __init__(self, api_key):
        super().__init__()
        self.model_path="model/model.bin"
        self.conversation_history = []
        self.selected_api = "gpt-3.5-turbo"
        self.api_key = api_key

        self.chat_log = QtWidgets.QTextEdit(self)
        self.chat_log.setReadOnly(True)
        normal_height_log = self.chat_log.sizeHint().height()
        self.chat_log.setFixedHeight(normal_height_log * 1.5)

        self.chat_input = QtWidgets.QTextEdit(self)
        self.chat_input.setPlaceholderText("Send a message")

        shadow_input = QtWidgets.QGraphicsDropShadowEffect(self.chat_input)
        shadow_input.setBlurRadius(15)
        shadow_input.setOffset(0, 0)
        shadow_input.setColor(QtGui.QColor("grey"))
        self.chat_input.setGraphicsEffect(shadow_input)

        normal_height_input = self.chat_input.sizeHint().height()
        self.chat_input.setFixedHeight(normal_height_input * 0.75)

        self.config_layout = QtWidgets.QHBoxLayout()

        self.api_group_box = QtWidgets.QGroupBox("Model:")
        self.api_group_box_layout = QtWidgets.QVBoxLayout(self.api_group_box)

        self.api_gpt35_radio_button = QtWidgets.QRadioButton("GPT-3.5")
        self.api_gpt4_radio_button = QtWidgets.QRadioButton("GPT-4")
        self.api_local_model_radio_button = QtWidgets.QRadioButton("Local Model")

        self.api_group_box_layout.addWidget(self.api_gpt35_radio_button)
        self.api_group_box_layout.addWidget(self.api_gpt4_radio_button)
        self.api_group_box_layout.addWidget(self.api_local_model_radio_button)

        self.api_gpt35_radio_button.toggled.connect(self.api_radio_button_toggled)
        self.api_gpt4_radio_button.toggled.connect(self.api_radio_button_toggled)
        self.api_local_model_radio_button.toggled.connect(self.api_radio_button_toggled)

        self.api_gpt35_radio_button.setChecked(True)

        self.par_group_box = QtWidgets.QGroupBox("Parameter:")
        self.par_layout = QtWidgets.QVBoxLayout(self.par_group_box)
        self.temperature_label = QtWidgets.QLabel("Temperature:")
        self.temperature_input = QtWidgets.QLineEdit("0.5", self)

        shadow_temp = QtWidgets.QGraphicsDropShadowEffect(self.temperature_input)
        shadow_temp.setBlurRadius(15)
        shadow_temp.setOffset(0, 0)
        shadow_temp.setColor(QtGui.QColor("grey"))
        self.temperature_input.setGraphicsEffect(shadow_temp)

        self.max_tokens_label = QtWidgets.QLabel("Max Tokens:")
        self.max_tokens_input = QtWidgets.QLineEdit("4000", self)

        shadow_max = QtWidgets.QGraphicsDropShadowEffect(self.max_tokens_input)
        shadow_max.setBlurRadius(15)
        shadow_max.setOffset(0, 0)
        shadow_max.setColor(QtGui.QColor("grey"))

        self.max_tokens_input.setGraphicsEffect(shadow_max)
        self.par_layout.addWidget(self.temperature_label)
        self.par_layout.addWidget(self.temperature_input)
        self.par_layout.addWidget(self.max_tokens_label)
        self.par_layout.addWidget(self.max_tokens_input)

        self.trans_group_box = QtWidgets.QGroupBox("Translation Settings:")
        self.trans_layout = QtWidgets.QVBoxLayout(self.trans_group_box)

        self.language_label = QtWidgets.QLabel("请选择您翻译的目标语言:")
        self.language_combobox = QtWidgets.QComboBox()
        languages = ["Chinese", "English", "German", "French", "Japanese"]
        flags = ["icon/China.png", "icon/America.png", "icon/Germany.jpg", "icon/France.jpg", "icon/Japan.png"]
        for lang, flag in zip(languages, flags):
            self.language_combobox.addItem(QIcon(flag), lang)

        language_layout = QtWidgets.QVBoxLayout()
        language_layout.addWidget(self.language_label)
        language_layout.addStretch(1)
        language_layout.addWidget(self.language_combobox)
        language_layout.addStretch(1)

        self.trans_layout.addLayout(language_layout)

        self.config_layout.addWidget(self.api_group_box)
        self.config_layout.addWidget(self.par_group_box)
        self.config_layout.addWidget(self.trans_group_box)
        self.config_layout.setStretchFactor(self.api_group_box, 3)
        self.config_layout.setStretchFactor(self.par_group_box, 7)
        self.config_layout.setStretchFactor(self.trans_group_box, 4)

        self.send_button = QtWidgets.QPushButton("Send", self)
        self.translate_button = QtWidgets.QPushButton("Translate", self)
        self.export_button = QtWidgets.QPushButton("Export", self)
        self.record_translate_button = QtWidgets.QPushButton("Record to Translate", self)
        self.record_send_button = QtWidgets.QPushButton("Record to Transcriptions", self)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addWidget(self.chat_log)
        self.layout.addLayout(self.config_layout)
        self.layout.addWidget(self.chat_input)

        self.button_layout = QtWidgets.QHBoxLayout()
        self.button_layout.addWidget(self.send_button)
        self.button_layout.addWidget(self.translate_button)
        self.button_layout.addWidget(self.export_button)
        self.layout.addLayout(self.button_layout)

        self.record_layout = QtWidgets.QHBoxLayout()
        self.record_layout.addWidget(self.record_translate_button)
        self.record_layout.addWidget(self.record_send_button)
        self.layout.addLayout(self.record_layout)

        self.demo_ui()

        self.send_button.clicked.connect(self.send)
        self.translate_button.clicked.connect(self.translate)
        self.update_chat_log_signal.connect(self.update_chat_log)
        self.set_button_state_signal.connect(self.set_button_state)
        self.set_api_button_state_signal.connect(self.set_api_button_state)
        self.export_button.clicked.connect(self.export_chat)
        self.record_send_button.clicked.connect(self.start_recording)


        self.p = pyaudio.PyAudio()
        self.stream = None
        self.frames = []
        self.recording = False
        self.recorded_files = 0


    @Slot()
    def set_button_disabled(self,bool):
        self.send_button.setDisabled(bool)
        self.translate_button.setDisabled(bool)
        self.export_button.setDisabled(bool)
        self.record_send_button.setDisabled(bool)
        self.record_translate_button.setDisabled(bool)

    @Slot()
    def set_api_button_disabled(self,bool):
        self.api_gpt35_radio_button.setDisabled(bool)
        self.api_gpt4_radio_button.setDisabled(bool)
        self.api_local_model_radio_button.setDisabled(bool)


    @Slot(str, str)
    def update_chat_log(self, message, message_type):
        # This slot function updates the chat log with the message
        # message_type is either 'user' or 'gpt' to differentiate the source of the message
        response_cursor = self.chat_log.textCursor()
        if message_type == "user":
            response_cursor.insertHtml("<span style='color: black; font-style: italic;'>You: </span>")
            response_cursor.insertText(f"{message}\n\n")
        elif message_type == "gpt-start":
            response_cursor.insertHtml("<span style='color: red;'>GPT: </span>")
            response_cursor.insertText(f"{message}")
        elif message_type == "gpt":
            response_cursor.insertHtml("<span style='color: red;'> </span>")
            response_cursor.insertText(f"{message}")
        elif message_type == "gpt-end":
            response_cursor.insertHtml("<span style='color: red;'> </span>")
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
            response_cursor.insertHtml("<span style='color: green;'> </span>")
            response_cursor.insertText(f"{message}\n\n")

    @Slot(bool)
    def set_button_state(self, state):
        self.set_button_disabled(state)

    @Slot(bool)
    def set_api_button_state(self, state):
        self.set_api_button_disabled(state)

    @Slot()
    def send(self):
        # Disable the send button to prevent multiple clicks
        self.set_button_state_signal.emit(True)
        self.set_api_button_state_signal.emit(True)

        message = self.chat_input.toPlainText()  # Get the user input
        if not message:
            self.set_button_state_signal.emit(False)
            return  # If there is no input, return

        self.chat_input.clear()  # Clear the input box
        self.update_chat_log_signal.emit(message, "user")  # Update the chat log with the user message

        if self.selected_api == "local model":
            message_thread = threading.Thread(target=self.local_process_message, args=(message,))
        else:
            message_thread = threading.Thread(target=self.process_message,args=(message,))
        # Start the message processing in a new thread
        message_thread.start()


    def process_message(self,message):
        try:
            user_message = {"role": "user", "content": message}
            self.conversation_history.append(user_message)
            openai.api_key = self.api_key  # Set the OpenAI API key
            response = openai.ChatCompletion.create(
                model=self.selected_api,
                messages=self.conversation_history,  # Use the conversation history
                stream=True
            )

            collected_messages = ""
            self.update_chat_log_signal.emit("", "gpt-start")
            for chunk in response:  # 遍历数据流的事件
                chunk_message = chunk['choices'][0]['delta']  # 提取消息
                response_text = chunk_message.get('content', '')  # 获取响应文本
                collected_messages += response_text  # 保存消息
                self.update_chat_log_signal.emit(response_text, "gpt")
            self.update_chat_log_signal.emit("", "gpt-end")
            self.conversation_history.append({"role":"assistant","content":collected_messages})
            # Re-enable the send button once message processing is complete
            self.set_button_state_signal.emit(False)

        except Exception as e:
            error_msg = f"Error: {str(e)}"
            # Emit the signal to update the chat log with the error message
            self.update_chat_log_signal.emit(error_msg, "error")
            self.set_button_state_signal.emit(False)

    def local_process_message(self,message, max_length=2048, max_context_length=512, top_k=0, top_p=0.7, temp=0.95, repeat_penalty=1.0):
        try:
            pipeline = chatglm_cpp.Pipeline(self.model_path)
            self.conversation_history.append(message)
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

            collected_messages = ""
            self.update_chat_log_signal.emit("", "gpt-start")
            for response_text in pipeline.chat(self.conversation_history, **generation_kwargs):
                collected_messages += response_text
                self.update_chat_log_signal.emit(response_text, "gpt")
            self.update_chat_log_signal.emit("", "gpt-end")
            self.conversation_history.append(collected_messages)
            self.set_button_state_signal.emit(False)
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            # Emit the signal to update the chat log with the error message
            self.update_chat_log_signal.emit(error_msg, "error")
            self.set_button_state_signal.emit(False)

    @Slot()
    def translate(self):
        # Disable the send button to prevent multiple clicks
        self.set_button_state_signal.emit(True)
        self.set_api_button_state_signal.emit(True)

        message = self.chat_input.toPlainText()  # Get the user input
        if not message:
            self.set_button_state_signal.emit(False)
            return  # If there is no input, return
        self.chat_input.clear()  # Clear the input box

        selected_language = self.language_combobox.currentText()
        request = f"Please translate the following sentence to {selected_language}，and give me translation outcome without anything else: {message}"
        self.update_chat_log_signal.emit(message, "user")  # Update the chat log with the user message
        # Start the message processing in a new thread

        if self.selected_api == "local model":
            message_thread = threading.Thread(target=self.local_translate_message, args=(request,))
        else:
            message_thread = threading.Thread(target=self.translate_message, args=(request,))
        message_thread.start()


    def translate_message(self,message):
        try:
            user_message = {"role": "user", "content": message}
            openai.api_key = self.api_key  # Set the OpenAI API key
            response = openai.ChatCompletion.create(
                model=self.selected_api,
                messages=[user_message],  # Use the conversation history
                stream=True
            )

            self.update_chat_log_signal.emit("", "gpt-start-translation")
            for chunk in response:  # 遍历数据流的事件
                chunk_message = chunk['choices'][0]['delta']  # 提取消息
                response_text = chunk_message.get('content', '')  # 获取响应文本
                self.update_chat_log_signal.emit(response_text, "gpt-translation")
            self.update_chat_log_signal.emit("", "gpt-end-translation")

            # Re-enable the send button once message processing is complete
            self.set_button_state_signal.emit(False)

        except Exception as e:
            error_msg = f"Error: {str(e)}"
            # Emit the signal to update the chat log with the error message
            self.update_chat_log_signal.emit(error_msg, "error")
            self.set_button_state_signal.emit(False)


    def local_translate_message(self,message, max_length=2048, max_context_length=512, top_k=0, top_p=0.7, temp=0.95, repeat_penalty=1.0):
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
            self.set_button_state_signal.emit(False)

        except Exception as e:
            error_msg = f"Error: {str(e)}"
            # Emit the signal to update the chat log with the error message
            self.update_chat_log_signal.emit(error_msg, "error")
            self.set_button_state_signal.emit(False)


    @Slot()
    def api_radio_button_toggled(self):
        # 切换API版本
        if self.api_gpt35_radio_button.isChecked():
            self.selected_api = "gpt-3.5-turbo"
        elif self.api_gpt4_radio_button.isChecked():
            self.selected_api = "gpt-4"
        elif self.api_local_model_radio_button.isChecked():
            self.selected_api = "local model"

    @Slot()
    def export_chat(self):
        # 导出聊天记录为.txt文件
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

    @Slot()
    def start_recording(self):
        sender_button = self.sender()  # 获取触发信号的按钮

        if self.stream is None:
            # 打开音频流
            self.stream = self.p.open(format=pyaudio.paInt16, channels=1, rate=10000, input=True,
                                      frames_per_buffer=2048)
            self.frames = []  # 初始化录音帧列表

            if sender_button == self.record_translate_button:
                self.record_translate_button.setText("Stop Record")  # 更改按钮文本为 "Stop Record"
            else:
                self.record_send_button.setText("Stop Record")  # 更改按钮文本为 "Stop Record"

            self.recording = True
            while self.recording:
                audio_data = self.stream.read(2048)  # 读出声卡缓冲区的音频数据
                self.frames.append(audio_data)
                QtWidgets.QApplication.processEvents()  # 强制处理事件，以确保按钮响应
        else:
            self.recording = False
            output_folder = "record"
            # 目标文件夹路径
            if not os.path.exists(output_folder):
                os.makedirs(output_folder)  # 如果文件夹不存在，创建它
            # 构建目标文件的完整路径
            output_path = os.path.join(output_folder, "recorded_audio.wav")

            # 将录制的音频保存为WAV文件
            wf = wave.open(output_path, "wb")
            wf.setnchannels(2)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes("".encode().join(self.frames))
            wf.close()

            # 停止录音并保存音频文件
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
            self.p.terminate()
            if sender_button == self.record_translate_button:
                self.record_translate_button.setText("Record to Translate")
            else:
                self.record_send_button.setText("Record to Transcriptions")




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
        self.chat_input.setStyleSheet("""
                    QTextEdit {
                        border: none;
                        border-radius: 10px;
                        padding: 8px;
                        font-size: 16px;
                        background-color: #FFFFFF;
                    }
                    QScrollBar:vertical {
                        border: 1px solid #696969;
                        background: #FFFFFF;
                        width: 10px; 
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

        self.api_group_box.setStyleSheet("""
                QGroupBox {
                    background-color: #FFFFFF;
                    border: 2px solid black;
                    border-radius: 5px;
                    margin-top: 1ex;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    subcontrol-position: top center;
                    padding: 0 3px;
                    font-size: 61px;  /* make font size larger */
                    font-weight: bold; /* make font bold */
                }
                """)
        self.par_group_box.setStyleSheet("""
                QGroupBox {
                    background-color: #FFFFFF;
                    border: 2px solid black;
                    border-radius: 5px;
                    margin-top: 1ex;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    subcontrol-position: top center;
                    padding: 0 3px;
                    font-size: 6px;  /* make font size larger */
                    font-weight: bold; /* make font bold */
                }
                """)
        self.temperature_input.setStyleSheet("""
                    QLineEdit {
                        border: none;  /* Remove border */
                        font-size: 16px;  /* Increase font size */
                        padding: 10px;  /* Add some padding */
                        background-color: #FFFFFF;  /* White background color */
                        border-radius: 10px;  /* Add rounded corners */
                    }
                """)
        self.temperature_input.setStyleSheet("""
                            QLineEdit {
                                border: none;  /* Remove border */
                                font-size: 16px;  /* Increase font size */
                                padding: 10px;  /* Add some padding */
                                background-color: #FFFFFF;  /* White background color */
                                border-radius: 10px;  /* Add rounded corners */
                            }
                        """)

        self.max_tokens_input.setStyleSheet("""
                    QLineEdit {
                        border: none;  /* Remove border */
                        font-size: 16px;  /* Increase font size */
                        padding: 10px;  /* Add some padding */
                        background-color: #FFFFFF;  /* White background color */
                        border-radius: 10px;  /* Add rounded corners */
                    }
                """)

        self.trans_group_box.setStyleSheet("""
                QGroupBox {
                    background-color: #FFFFFF;
                    border: 2px solid black;
                    border-radius: 5px;
                    margin-top: 1ex;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    subcontrol-position: top center;
                    padding: 0 3px;
                    font-size: 6px;  /* make font size larger */
                    font-weight: bold; /* make font bold */
                }
                """)
        self.language_label.setStyleSheet("""
                    QLabel {
                        font-size: 12px;  /* Decrease font size */
                        color: #333;  /* Darker text color */
                    }
                """)
        self.language_combobox.setStyleSheet("""
                    QComboBox {
                        font-size: 16px;
                        padding: 10px;
                        border: 2px solid #4CAF50;  /* Green border */
                        border-radius: 10px;  /* Rounded corners */
                        background-color: #E8F5E9;  /* Light Green background */
                    }
                    QComboBox:hover {
                        border: 2px solid #388E3C;  /* Darker green border when hovered */
                    }
                    QComboBox QAbstractItemView {
                        font-size: 16px;
                        padding: 10px;
                        selection-background-color: #C8E6C9;  /* Slightly darker light green selection */
                        selection-color: black;  /* Black text for selected item */
                    }
                    QComboBox::drop-down {
                        border: 0;  /* No border for the drop-down arrow */
                        padding-right: 8px;  /* Adjust padding for the drop-down arrow */
                    }
                    QComboBox::down-arrow {
                        image: url(/path-to-your-icon/arrow-down-icon.png);  /* Customize drop-down arrow icon */
                    }
                    QComboBox::item:selected {
                        color: black;
                    }
                    QComboBox::item {
                        color: black;
                    }
                """)
        self.send_button.setStyleSheet("""
                    QPushButton {
                        background-color: #007FFF;  /* Light Blue */
                        color: #FFFFFF;  /* White */
                        border: 2px solid #1E90FF;  /* Dodger Blue */
                        border-radius: 15px;  /* Rounded corners */
                        padding: 10px 25px;  /* Padding: vertical, horizontal */
                        font-size: 16px;  /* Text size */
                        font-family: "Arial";  /* Font family */
                    }
                    QPushButton:hover {
                        background-color: #B0E0E6;  /* Powder Blue */
                        color: #4682B4;  /* Steel Blue */
                        border: 2px solid #4682B4;  /* Steel Blue */
                    }
                    QPushButton:pressed {
                        background-color: #87CEFA;  /* Light Sky Blue */
                        color: #2E8B57;  /* Sea Green */
                        border: 2px solid #2E8B57;  /* Sea Green */
                    }
                """)
        self.translate_button.setStyleSheet("""
                    QPushButton {
                        background-color: #FFA07A;  /* Light Salmon */
                        color: #FFFFFF;  /* White */
                        border: 2px solid #FFDEAD;  /* Navajo White */
                        border-radius: 15px;  /* Rounded corners */
                        padding: 10px 25px;  /* Padding: vertical, horizontal */
                        font-size: 16px;  /* Text size */
                        font-family: "Arial";  /* Font family */
                    }
                    QPushButton:hover {
                        background-color: #FFE4B5;  /* Moccasin */
                        color: #FF6347;  /* Tomato */
                        border: 2px solid #FF6347;  /* Tomato */
                    }
                    QPushButton:pressed {
                        background-color: #FFDAB9;  /* Peach Puff */
                        color: #FF4500;  /* Orange Red */
                        border: 2px solid #FF4500;  /* Orange Red */
                    }
                """)

        self.export_button.setStyleSheet("""
                    QPushButton {
                        background-color: #5F9E6E;  /* 深绿色 */
                        color: #FFFFFF;  /* White */
                        border: none;  /* 移除外侧轮廓 */
                        border-radius: 15px;  /* Rounded corners */
                        padding: 10px 25px;  /* Padding: vertical, horizontal */
                        font-size: 16px;  /* Text size */
                        font-family: "Arial";  /* Font family */
                    }
                    QPushButton:hover {
                        background-color: #4682B4;  /* Steel Blue */
                        color: #FFFFFF;  /* White */
                    }
                    QPushButton:pressed {
                        background-color: #2E8B57;  /* Sea Green */
                        color: #FFFFFF;  /* White */
                    }
                """)

        self.record_translate_button.setStyleSheet("""
                    QPushButton {
                        background-color: #FFD700;  /* Gold */
                        color: #FFFFFF;  /* White */
                        border: none;  /* 移除外侧轮廓 */
                        border-radius: 15px;  /* Rounded corners */
                        padding: 10px 25px;  /* Padding: vertical, horizontal */
                        font-size: 16px;  /* Text size */
                        font-family: "Arial";  /* Font family */
                    }
                    QPushButton:hover {
                        background-color: #FFEC8B;  /* Lighter gold for hover */
                    }
                    QPushButton:pressed {
                        background-color: #FFEC8B;  /* Lighter gold for hover */
                    }
                """)
        self.record_send_button.setStyleSheet("""
                    QPushButton {
                        background-color: #FF4500;  /* Orange Red */
                        color: #FFFFFF;  /* White */
                        border: 2px solid #FF6347;  /* Tomato */
                        border-radius: 15px;  /* Rounded corners */
                        padding: 10px 25px;  /* Padding: vertical, horizontal */
                        font-size: 16px;  /* Text size */
                        font-family: "Arial";  /* Font family */
                    }
                    QPushButton:hover {
                        background-color: #FF6347;  /* Tomato */
                    }
                    QPushButton:pressed {
                        background-color: #FFA07A;  /* Light Salmon */
                    }
                """)

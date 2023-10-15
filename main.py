import configparser
import sys
from datetime import datetime

import openai
import pyperclip
from PySide6 import QtWidgets, QtGui
from PySide6.QtCore import Slot


# 以下函数只是一个示例, 你应该按照你的实际情况去验证API密钥
def is_api_key_valid(api_key):
    return bool(api_key)


class ChatTab(QtWidgets.QWidget):
    def __init__(self, api_key):
        super().__init__()
        self.conversation_history = []
        self.selected_api = "gpt-3.5-turbo"
        self.api_key = api_key
        self.chat_log = QtWidgets.QTextEdit(self)
        self.chat_log.setReadOnly(True)
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
        normal_height_log = self.chat_log.sizeHint().height()
        self.chat_log.setFixedHeight(normal_height_log * 1.3)
        self.chat_input = QtWidgets.QTextEdit(self)
        self.chat_input.setPlaceholderText("Send a messages")

        # 设置QTextEdit的最小高度、圆角效果、滚动条和其他样式
        #  self.chat_input.setMinimumHeight(40)
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

        shadow = QtWidgets.QGraphicsDropShadowEffect(self.chat_input)
        shadow.setBlurRadius(15)
        shadow.setOffset(0, 0)
        shadow.setColor(QtGui.QColor("grey"))
        self.chat_input.setGraphicsEffect(shadow)
        normal_height_input = self.chat_input.sizeHint().height()
        self.chat_input.setFixedHeight(normal_height_input * 0.75)

        self.config_layout = QtWidgets.QHBoxLayout()

        self.api_group_box = QtWidgets.QGroupBox("Model:")
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
        self.api_group_box_layout = QtWidgets.QVBoxLayout(self.api_group_box)

        self.api_gpt35_radio_button = QtWidgets.QRadioButton("GPT-3.5")
        self.api_gpt35_radio_button.toggled.connect(self.api_radio_button_toggled)
        self.api_group_box_layout.addWidget(self.api_gpt35_radio_button)
        self.api_gpt35_radio_button.setChecked(True)

        self.api_gpt4_radio_button = QtWidgets.QRadioButton("GPT-4")
        self.api_gpt4_radio_button.toggled.connect(self.api_radio_button_toggled)
        self.api_group_box_layout.addWidget(self.api_gpt4_radio_button)

        self.par_group_box = QtWidgets.QGroupBox("Parameter:")
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
        self.par_layout = QtWidgets.QVBoxLayout(self.par_group_box)

        self.temperature_label = QtWidgets.QLabel("Temperature:")
        self.temperature_input = QtWidgets.QLineEdit("0.5", self)
        self.temperature_input.setStyleSheet("""
            QLineEdit {
                border: none;  /* Remove border */
                font-size: 16px;  /* Increase font size */
                padding: 10px;  /* Add some padding */
                background-color: #FFFFFF;  /* White background color */
                border-radius: 10px;  /* Add rounded corners */
            }
        """)

        # Creating a QGraphicsDropShadowEffect object and setting properties
        shadow = QtWidgets.QGraphicsDropShadowEffect(self.temperature_input)
        shadow.setBlurRadius(15)  # Shadow blur radius
        shadow.setOffset(0, 0)  # No offset, so shadow is spread equally around the text box
        shadow.setColor(QtGui.QColor("grey"))  # Shadow color
        # Applying the shadow effect to your QLineEdit widget
        self.temperature_input.setGraphicsEffect(shadow)

        self.max_tokens_label = QtWidgets.QLabel("Max Tokens:")
        self.temperature_input.setStyleSheet("""
                    QLineEdit {
                        border: none;  /* Remove border */
                        font-size: 16px;  /* Increase font size */
                        padding: 10px;  /* Add some padding */
                        background-color: #FFFFFF;  /* White background color */
                        border-radius: 10px;  /* Add rounded corners */
                    }
                """)

        # Creating a QGraphicsDropShadowEffect object and setting properties
        shadow = QtWidgets.QGraphicsDropShadowEffect(self.temperature_input)
        shadow.setBlurRadius(15)  # Shadow blur radius
        shadow.setOffset(0, 0)  # No offset, so shadow is spread equally around the text box
        shadow.setColor(QtGui.QColor("grey"))  # Shadow color
        # Applying the shadow effect to your QLineEdit widget
        self.temperature_input.setGraphicsEffect(shadow)
        self.max_tokens_input = QtWidgets.QLineEdit("4000", self)

        self.max_tokens_input.setStyleSheet("""
            QLineEdit {
                border: none;  /* Remove border */
                font-size: 16px;  /* Increase font size */
                padding: 10px;  /* Add some padding */
                background-color: #FFFFFF;  /* White background color */
                border-radius: 10px;  /* Add rounded corners */
            }
        """)

        # Creating a QGraphicsDropShadowEffect object and setting properties
        shadow = QtWidgets.QGraphicsDropShadowEffect(self.max_tokens_input)
        shadow.setBlurRadius(15)  # Shadow blur radius
        shadow.setOffset(0, 0)  # No offset, so shadow is spread equally around the text box
        shadow.setColor(QtGui.QColor("grey"))  # Shadow color

        # Applying the shadow effect to your QLineEdit widget
        self.max_tokens_input.setGraphicsEffect(shadow)
        self.par_layout.addWidget(self.temperature_label)
        self.par_layout.addWidget(self.temperature_input)
        self.par_layout.addWidget(self.max_tokens_label)
        self.par_layout.addWidget(self.max_tokens_input)

        self.trans_group_box = QtWidgets.QGroupBox("Translation Settings:")
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
        self.trans_layout = QtWidgets.QVBoxLayout(self.trans_group_box)

        # 创建一个下拉框
        self.language_combobox = QtWidgets.QComboBox()
        # 添加所述的选项
        languages = ["Chinese", "English", "German", "French", "Japanese"]

        self.language_combobox.addItems(languages)

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
        # 将下拉框添加到布局中
        self.trans_layout.addWidget(self.language_combobox)
        self.config_layout.addWidget(self.api_group_box)
        self.config_layout.addWidget(self.par_group_box)
        self.config_layout.addWidget(self.trans_group_box)
        self.config_layout.setStretchFactor(self.api_group_box, 3)
        self.config_layout.setStretchFactor(self.par_group_box, 7)
        self.config_layout.setStretchFactor(self.trans_group_box, 4)
        self.send_button = QtWidgets.QPushButton("Send", self)
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

        self.send_button.clicked.connect(self.send_message)

        self.translate_button = QtWidgets.QPushButton("Translate", self)
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
        self.translate_button.clicked.connect(self.translate_from_clipboard)

        self.export_button = QtWidgets.QPushButton("Export", self)
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

        self.export_button.clicked.connect(self.export_chat)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addWidget(self.chat_log)
        self.layout.addLayout(self.config_layout)
        self.layout.addWidget(self.chat_input)

        self.button_layout = QtWidgets.QHBoxLayout()
        self.button_layout.addWidget(self.send_button)
        self.button_layout.addWidget(self.translate_button)
        self.button_layout.addWidget(self.export_button)
        self.layout.addLayout(self.button_layout)

    @Slot()
    def translate_from_clipboard(self):
        api_key = self.api_key
        if not api_key:
            return

        clipboard = QtWidgets.QApplication.clipboard()
        clipboard_text = clipboard.text()

        if not clipboard_text:
            return

        selected_language = self.language_combobox.currentText()

        max_tokens_text = self.max_tokens_input.text()
        if (not max_tokens_text.isdigit() or int(max_tokens_text) < 0 or int(max_tokens_text) > 4000):
            QtWidgets.QMessageBox.warning(self, "Invalid Max Tokens",
                                          "Please enter a valid max tokens value between 0 and 2046.")
            return

        temperature_text = self.temperature_input.text()
        if float(temperature_text) < 0:
            QtWidgets.QMessageBox.warning(self, "Invalid Temperature",
                                          "Please enter a valid temperature value greater than 0.")
            return

        openai.api_key = api_key
        try:
            request = f"Please translate the following sentence to {selected_language}: {clipboard_text}"
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",  # 使用正确的模型
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that translates text."},
                    {"role": "user", "content": request}
                ]
            )
            response_text = response.choices[0].message["content"]
            response_cursor = self.chat_log.textCursor()

            # 设置GPT返回文本的颜色为黑色
            response_cursor.insertHtml("<span style='color: black'>GPT: </span>")
            response_cursor.insertText(f"翻译结果为：{response_text}\n\n")

            self.chat_log.setReadOnly(False)
            #self.chat_log.append(f"User: {request}")
            #self.chat_log.append(f"GPT: {response_text}\n")
            self.chat_log.setReadOnly(True)
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            QtWidgets.QMessageBox.critical(self, "API Error", error_msg)
            self.chat_log.append(f"{error_msg}\n")

    def showEvent(self, event):
        super().showEvent(event)
        self.chat_input.setFocus()

    @Slot()
    def api_radio_button_toggled(self):
        if self.api_gpt35_radio_button.isChecked():
            self.selected_api = "gpt-3.5-turbo"
        elif self.api_gpt4_radio_button.isChecked():
            self.selected_api = "gpt-4"

    def send_message(self):
        message = self.chat_input.toPlainText()
        if not message:
            return
        self.chat_input.clear()

        # 获取用户输入内容
        user_input = message

        # 创建用户消息对象并添加到历史对话中
        user_message = {"role": "user", "content": user_input}
        self.conversation_history.append(user_message)

        self.chat_log.setReadOnly(True)

        try:
            openai.api_key = self.api_key

            # 发送包含整个历史对话的请求
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=self.conversation_history  # 使用历史对话
            )

            response_text = response.choices[0].message["content"]

            response_cursor = self.chat_log.textCursor()

            # 显示用户输入和 GPT 响应
            response_cursor.insertHtml("<span style='color: blue'>You: </span>")
            response_cursor.insertText(f"\n{user_input}\n\n")
            response_cursor.insertHtml("<span style='color: red'>GPT: </span>")
            response_cursor.insertText(f"{response_text}\n\n")
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            QtWidgets.QMessageBox.critical(self, "API Error", error_msg)
            self.chat_log.append(f"{error_msg}\n\n")

    def export_chat(self):
        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%d-%H-%M-%S")
        file_name = f"chat_{timestamp}.txt"

        try:
            with open(file_name, "w") as f:
                f.write(self.chat_log.toPlainText())
            QtWidgets.QMessageBox.information(
                self, "Export Successful", f"The chat has been exported to {file_name}."
            )
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self,
                "Export Error",
                f"An error occurred while exporting the chat: {str(e)}",
            )


class ChatWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: white;")
        self.setWindowTitle("GUI-GPT")
        self.setGeometry(50, 50, 800, 600)

        self.tab_widget = QtWidgets.QTabWidget(self)
        self.tab_widget.setStyleSheet("background-color: white;")
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.tabCloseRequested.connect(self.check_tab_count)

        self.new_tab_button = QtWidgets.QPushButton("New Chat Tab", self)
        self.new_tab_button.setStyleSheet("""
            QPushButton {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                                  stop: 0 #e6f7ff, stop: 1 #b3e0ff);  /* Light blue gradient background */
                color: #2F4F4F;  /* Dark Slate Gray */
                border: 2px solid #6699cc;  /* Light blue border */
                border-radius: 15px;  /* Rounded corners */
                padding: 10px 25px;  /* Padding: vertical, horizontal */
                font-size: 16px;  /* Text size */
                font-family: "Arial";  /* Font family */

            }
            QPushButton:hover {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                                  stop: 0 #cce6ff, stop: 1 #99c2ff);  /* Lighter blue gradient when hovered */
                border: 2px solid #336699;  /* Darker blue border when hovered */
            }
            QPushButton:pressed {
                background-color: #6699cc;  /* Solid light blue when pressed */
                color: #FFFFFF;  /* White text when pressed */
            }
        """)

        self.new_tab_button.clicked.connect(self.add_new_tab)
        self.copyright = QtWidgets.QLabel("© [2023] Oops Computing Team. All Rights Reserved.")
        self.copyright.setStyleSheet("background-color: white;")
        self.bottom_box = QtWidgets.QGroupBox()
        self.bottom_layout = QtWidgets.QHBoxLayout(self.bottom_box)
        self.bottom_layout.addWidget(self.copyright)
        self.bottom_layout.addWidget(self.new_tab_button)
        self.layout = QtWidgets.QVBoxLayout(self)

        self.layout.addWidget(self.tab_widget)
        self.layout.addWidget(self.bottom_box)

        self.tab_count = 0
        self.add_new_tab()

    def add_new_tab(self):
        self.tab_count += 1
        api_key = self.get_api_key()
        if api_key:
            chat_tab = ChatTab(api_key)
            index = self.tab_widget.addTab(chat_tab, f"Chat {self.tab_count}")
            self.tab_widget.setCurrentIndex(index)

    def close_tab(self, index):
        widget = self.tab_widget.widget(index)
        widget.deleteLater()
        self.tab_widget.removeTab(index)

    def check_tab_count(self):
        if self.tab_widget.count() == 0:
            QtWidgets.QApplication.quit()

    def get_api_key(self):
        config = configparser.ConfigParser()
        config.read("config.ini")
        api_key_value = config.get("API", "key", fallback=None)  # 尝试从配置文件中获取API密钥

        if is_api_key_valid(api_key_value):
            return api_key_value  # 如果已经存在有效的API密钥，直接返回

        api_key_value, ok = QtWidgets.QInputDialog.getMultiLineText(
            self,
            "OpenAI API Key",
            "Enter your OpenAI API key:",
            "",
        )
        if not ok:
            sys.exit()

        while not is_api_key_valid(api_key_value):
            QtWidgets.QMessageBox.warning(
                self,
                "Invalid API Key",
                "The API key you entered is invalid. Please try again.",
            )
            api_key_value, ok = QtWidgets.QInputDialog.getMultiLineText(
                self,
                "OpenAI API Key",
                "Enter your OpenAI API key:",
                "",
            )
            if not ok:
                sys.exit()

        config["API"] = {"key": api_key_value}
        with open("config.ini", "w") as configfile:
            config.write(configfile)

        return api_key_value


app = QtWidgets.QApplication([])
window = ChatWindow()
window.show()

app.exec()



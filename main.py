import configparser
import sys
from datetime import datetime

import openai
from PySide6 import QtWidgets, QtGui
from PySide6.QtCore import Slot


# 以下函数只是一个示例, 你应该按照你的实际情况去验证API密钥
def is_api_key_valid(api_key):
    return bool(api_key)


class ChatTab(QtWidgets.QWidget):
    def __init__(self, api_key):
        super().__init__()
        self.selected_api = "text-davinci-003"
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
        self.chat_input = QtWidgets.QTextEdit(self)
        self.chat_input.setPlaceholderText("Send a messages")
        # 注意: QTextEdit 使用的信号是 textChanged,
        # 但它不是在按回车时触发的，你可能需要使用一个按钮或其他方法来发送消息
        self.chat_input.textChanged.connect(self.send_message)

        # 设置QTextEdit的最小高度、圆角效果、滚动条和其他样式
        self.chat_input.setMinimumHeight(40)
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

        # 创建一个 QGraphicsDropShadowEffect 对象并设置属性
        shadow = QtWidgets.QGraphicsDropShadowEffect(self.chat_input)
        shadow.setBlurRadius(15)  # 阴影模糊半径
        shadow.setOffset(0, 0)  # 阴影的偏移量
        shadow.setColor(QtGui.QColor("grey"))  # 阴影的颜色

        # 应用阴影效果到你的 QTextEdit 组件上
        self.chat_input.setGraphicsEffect(shadow)

        # 如果你希望在按下“Enter”键时触发某些操作（例如，发送消息），而不是插入一个新行，
        # 你可能需要重新实现 QTextEdit 的键盘事件处理。
        # 例如，通过在你的类中添加一个自定义的 QTextEdit 并重新实现其 keyPressEvent 方法。

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
                font-size: 18px;  /* Increase font size */
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
                transition: background-color 0.5s, color 0.5s, border 0.5s;  /* Smooth transition for background, color, and border */
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

        self.export_button = QtWidgets.QPushButton("Translate", self)
        self.export_button.setStyleSheet("""
            QPushButton {
                background-color: #FFA07A;  /* Light Salmon */
                color: #FFFFFF;  /* White */
                border: 2px solid #FFDEAD;  /* Navajo White */
                border-radius: 15px;  /* Rounded corners */
                padding: 10px 25px;  /* Padding: vertical, horizontal */
                font-size: 16px;  /* Text size */
                font-family: "Arial";  /* Font family */
                transition: background-color 0.5s, color 0.5s, border 0.5s;  /* Smooth transition for background, color, and border */
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

        self.export_button.clicked.connect(self.export_chat)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addWidget(self.chat_log)
        self.layout.addLayout(self.config_layout)
        self.layout.addWidget(self.chat_input)

        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addWidget(self.send_button)
        button_layout.addWidget(self.export_button)
        self.layout.addLayout(button_layout)

    @Slot()
    def showEvent(self, event):
        super().showEvent(event)
        self.chat_input.setFocus()

    def api_radio_button_toggled(self):
        if self.api_davinci_radio_button.isChecked():
            self.selected_api = "text-davinci-003"
        elif self.api_curie_radio_button.isChecked():
            self.selected_api = "text-curie-001"
        elif self.api_babbage_radio_button.isChecked():
            self.selected_api = "text-babbage-001"
        elif self.api_ada_radio_button.isChecked():
            self.selected_api = "text-ada-001"

    def send_message(self):
        message = self.chat_input.text()
        if not message:
            return
        self.chat_input.clear()
        self.chat_log.setReadOnly(True)

        user_cursor = self.chat_log.textCursor()
        user_cursor.insertHtml("<span style='color: blue'>You: </span>")
        user_cursor.insertText(f"\n{message}\n\n")

        max_tokens_text = self.max_tokens_input.text()
        if self.api_davinci_radio_button.isChecked():
            if (
                    not max_tokens_text.isdigit()
                    or int(max_tokens_text) < 0
                    or int(max_tokens_text) > 4000
            ):
                QtWidgets.QMessageBox.warning(
                    self,
                    "Invalid Max Tokens",
                    "Please enter a valid max tokens value between 0 and 4000.",
                )
                return
        else:
            if (
                    not max_tokens_text.isdigit()
                    or int(max_tokens_text) < 0
                    or int(max_tokens_text) > 2046
            ):
                QtWidgets.QMessageBox.warning(
                    self,
                    "Invalid Max Tokens",
                    "Please enter a valid max tokens value between 0 and 2046.",
                )
                return

        temperature_text = self.temperature_input.text()
        if float(temperature_text) < 0:
            QtWidgets.QMessageBox.warning(
                self,
                "Invalid Temperature",
                "Please enter a valid temperature value greater than 0.",
            )
            return

        try:
            openai.api_key = self.api_key
            response = openai.Completion.create(
                engine=self.selected_api,
                prompt=f"{message}\n",
                max_tokens=int(max_tokens_text),
                temperature=float(temperature_text),
            )
            response_text = response["choices"][0]["text"]

            response_cursor = self.chat_log.textCursor()
            response_cursor.insertHtml("<span style='color: red'>GPT: </span>")
            response_cursor.insertText(f"{response_text}\n\n")

        except Exception as e:
            error_msg = f"Error: {str(e)}"
            QtWidgets.QMessageBox.critical(self, "API Error", error_msg)
            self.chat_log.append(f"{error_msg}\n\n")

        self.chat_log.setReadOnly(True)

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
                transition: background-color 0.5s, color 0.5s, border 0.5s;  /* Smooth transition for background, color and border */
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
        #self.copyright.setStyleSheet("background-color: white;")
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
        api_key = config.get("API", "key", fallback="")
        while not api_key or not is_api_key_valid(api_key):
            api_key, ok = QtWidgets.QInputDialog.getText(
                self,
                "OpenAI API Key",
                "Enter your OpenAI API key:",
                QtWidgets.QLineEdit.Normal,
                "",
            )
            if not ok:
                sys.exit()
            if is_api_key_valid(api_key):
                config["API"] = {"key": api_key}
                with open("config.ini", "w") as configfile:
                    config.write(configfile)
            else:
                QtWidgets.QMessageBox.warning(
                    self,
                    "Invalid API Key",
                    "The API key you entered is invalid. Please try again.",
                )
        return api_key


app = QtWidgets.QApplication([])
window = ChatWindow()
window.show()
app.exec_()

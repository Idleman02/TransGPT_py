from chat_window import *
from config import *

# 应用程序的入口点，GUI的初始化
app = QtWidgets.QApplication(sys.argv)
config = Configuration("config.ini")
window = ChatWindow(config)
window.show()
app.exec()

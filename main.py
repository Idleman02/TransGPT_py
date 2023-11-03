from chat_window import *
from config import *

app = QtWidgets.QApplication(sys.argv)
config = Configuration("config.ini")
window = ChatWindow(config)
window.show()
app.exec()

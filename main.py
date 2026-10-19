import os
import sys
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication
from src.views.main_window import MainWindow
from src.controllers.main_controller import MainController
from src.utils.resource_path import get_resource_path


def main():
    app = QApplication(sys.argv)

    # 루트 폴더(또는 PyInstaller 번들 내부)의 아이콘 적용
    icon_path = get_resource_path("My_pdf_editer_icon.png")
    if os.path.exists(icon_path):
        app_icon = QIcon(icon_path)
        app.setWindowIcon(app_icon)

    window = MainWindow()
    if os.path.exists(icon_path):
        window.setWindowIcon(QIcon(icon_path))

    controller = MainController(window)  # noqa: F841 - 이벤트 컨트롤러 참조 유지
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

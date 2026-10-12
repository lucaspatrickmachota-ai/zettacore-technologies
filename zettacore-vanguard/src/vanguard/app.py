"""Initial PySide6 desktop shell for ZettaCore Vanguard."""

from __future__ import annotations

import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from vanguard.storage import AssetStore


STYLE = """
QMainWindow, QWidget { background: #080d14; color: #d9e1ea; font-size: 13px; }
QLabel#brand { color: #d9e1ea; font-size: 24px; font-weight: 700; }
QLabel#tagline { color: #8da4bc; font-size: 11px; letter-spacing: 2px; }
QLabel#section { color: #2e9aff; font-size: 16px; font-weight: 600; }
QLineEdit, QComboBox { background: #101c2b; border: 1px solid #26384d; border-radius: 5px; padding: 7px; }
QPushButton { background: #1674c8; color: white; border: 0; border-radius: 5px; padding: 9px 14px; font-weight: 600; }
QPushButton:hover { background: #2e9aff; }
QTableWidget { background: #0c131d; alternate-background-color: #101c2b; gridline-color: #233347; border: 1px solid #233347; }
QHeaderView::section { background: #101c2b; color: #b9c9da; padding: 7px; border: 0; }
"""


class VanguardWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.store = AssetStore()
        self.setWindowTitle("ZettaCore Vanguard")
        self.resize(1050, 720)
        self.setMinimumSize(800, 560)

        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(16)

        brand = QLabel("ZETTACORE VANGUARD")
        brand.setObjectName("brand")
        tagline = QLabel("INTELLIGENCE. SECURITY. RESILIENCE.")
        tagline.setObjectName("tagline")
        layout.addWidget(brand)
        layout.addWidget(tagline)

        intro = QLabel(
            "Local security workspace · MVP 0.1.0\n"
            "This prototype manages an inventory only. It does not scan networks or detect malware."
        )
        intro.setWordWrap(True)
        intro.setStyleSheet("color: #aab9c9; padding: 10px 0;")
        layout.addWidget(intro)

        section = QLabel("Authorized asset inventory")
        section.setObjectName("section")
        layout.addWidget(section)

        form_widget = QWidget()
        form = QFormLayout(form_widget)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Example: Company web server")
        self.type_input = QComboBox()
        self.type_input.addItems(["Server", "Workstation", "Website / domain", "Cloud resource", "Other"])
        self.environment_input = QComboBox()
        self.environment_input.addItems(["Production", "Staging", "Development", "Lab", "Unknown"])
        self.owner_input = QLineEdit()
        self.owner_input.setPlaceholderText("Asset owner / team")
        self.authorization_input = QLineEdit()
        self.authorization_input.setPlaceholderText("Scope or authorization reference (optional)")
        form.addRow("Asset name *", self.name_input)
        form.addRow("Type", self.type_input)
        form.addRow("Environment", self.environment_input)
        form.addRow("Owner", self.owner_input)
        form.addRow("Authorization note", self.authorization_input)
        layout.addWidget(form_widget)

        buttons = QHBoxLayout()
        add_button = QPushButton("Add asset")
        add_button.clicked.connect(self.add_asset)
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh_assets)
        refresh_button.setStyleSheet("background: #26384d;")
        buttons.addWidget(add_button)
        buttons.addWidget(refresh_button)
        buttons.addStretch(1)
        layout.addLayout(buttons)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["ID", "Name", "Type", "Environment", "Owner"])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table, 1)

        footer = QLabel("Data stays on this computer · No telemetry · No active scans")
        footer.setStyleSheet("color: #71869c; font-size: 11px;")
        footer.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(footer)

        self.setCentralWidget(root)
        self.setStyleSheet(STYLE)
        self.refresh_assets()

    def add_asset(self) -> None:
        try:
            self.store.add_asset(
                self.name_input.text(),
                self.type_input.currentText(),
                self.environment_input.currentText().lower(),
                self.owner_input.text(),
                self.authorization_input.text(),
            )
        except ValueError as error:
            QMessageBox.warning(self, "Asset not added", str(error))
            return
        self.name_input.clear()
        self.owner_input.clear()
        self.authorization_input.clear()
        self.refresh_assets()

    def refresh_assets(self) -> None:
        assets = self.store.list_assets()
        self.table.setRowCount(len(assets))
        for row_index, asset in enumerate(assets):
            values = [
                str(asset["id"]),
                asset["name"],
                asset["asset_type"],
                asset["environment"],
                asset["owner"],
            ]
            for column_index, value in enumerate(values):
                item = QTableWidgetItem(value)
                if column_index == 0:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row_index, column_index, item)


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("ZettaCore Vanguard")
    app.setOrganizationName("ZettaCore")
    window = VanguardWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

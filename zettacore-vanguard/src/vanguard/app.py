"""Initial PySide6 desktop app for ZettaCore Vanguard."""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from vanguard.intelligence import (
    IntelligenceSourceError,
    VulnerabilityRecord,
    enrich_with_kev,
    fetch_cve,
    fetch_kev_catalog,
)
from vanguard.reporting import generate_vulnerability_report
from vanguard.storage import AssetStore
from vanguard.vulnerability_store import VulnerabilityStore


STYLE = """
QMainWindow, QWidget { background: #080d14; color: #d9e1ea; font-size: 13px; }
QLabel#brand { color: #d9e1ea; font-size: 24px; font-weight: 700; }
QLabel#tagline { color: #8da4bc; font-size: 11px; letter-spacing: 2px; }
QLabel#section { color: #2e9aff; font-size: 16px; font-weight: 600; }
QLineEdit, QComboBox { background: #101c2b; border: 1px solid #26384d; border-radius: 5px; padding: 7px; }
QPushButton { background: #1674c8; color: white; border: 0; border-radius: 5px; padding: 9px 14px; font-weight: 600; }
QPushButton:hover { background: #2e9aff; }
QPushButton:disabled { background: #26384d; color: #8292a4; }
QTabWidget::pane { border: 1px solid #233347; }
QTabBar::tab { background: #101c2b; color: #b9c9da; padding: 10px 16px; }
QTabBar::tab:selected { background: #173b5c; color: #ffffff; }
QTableWidget { background: #0c131d; alternate-background-color: #101c2b; gridline-color: #233347; border: 1px solid #233347; }
QHeaderView::section { background: #101c2b; color: #b9c9da; padding: 7px; border: 0; }
"""


class IntelligenceWorker(QThread):
    """Run public-source lookups away from the UI thread."""

    succeeded = Signal(object)
    failed = Signal(str)

    def __init__(self, cve_id: str) -> None:
        super().__init__()
        self.cve_id = cve_id

    def run(self) -> None:
        try:
            records = fetch_cve(self.cve_id)
            if not records:
                self.failed.emit(f"No NVD record was returned for {self.cve_id}.")
                return
            catalog = fetch_kev_catalog()
            self.succeeded.emit(enrich_with_kev(records, catalog))
        except (ValueError, IntelligenceSourceError) as error:
            self.failed.emit(str(error))
        except Exception as error:  # Convert unexpected network/decoder failures into UI feedback.
            self.failed.emit(f"Lookup failed safely: {error}")


class VanguardWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.store = AssetStore()
        self.vulnerability_store = VulnerabilityStore(self.store.path)
        self.lookup_worker: IntelligenceWorker | None = None
        self.setWindowTitle("ZettaCore Vanguard")
        self.resize(1120, 760)
        self.setMinimumSize(820, 600)

        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(14)

        brand = QLabel("ZETTACORE VANGUARD")
        brand.setObjectName("brand")
        tagline = QLabel("INTELLIGENCE. SECURITY. RESILIENCE.")
        tagline.setObjectName("tagline")
        layout.addWidget(brand)
        layout.addWidget(tagline)

        intro = QLabel(
            "Local-first security workspace · Early MVP\n"
            "Public CVE intelligence is not proof that an asset is vulnerable or compromised. "
            "No active scanning or malware detection is performed."
        )
        intro.setWordWrap(True)
        intro.setStyleSheet("color: #aab9c9; padding: 8px 0;")
        layout.addWidget(intro)

        tabs = QTabWidget()
        tabs.addTab(self._build_assets_tab(), "Authorized assets")
        tabs.addTab(self._build_vulnerabilities_tab(), "Vulnerability intelligence")
        layout.addWidget(tabs, 1)

        footer = QLabel("Local data · No telemetry · Public-source lookups require an internet connection")
        footer.setStyleSheet("color: #71869c; font-size: 11px;")
        footer.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(footer)

        self.setCentralWidget(root)
        self.setStyleSheet(STYLE)
        self.refresh_assets()
        self.refresh_vulnerabilities()

    def _build_assets_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        section = QLabel("Asset inventory")
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
        delete_button = QPushButton("Delete selected")
        delete_button.clicked.connect(self.delete_selected_asset)
        delete_button.setStyleSheet("background: #7f2932;")
        for button in (add_button, refresh_button, delete_button):
            buttons.addWidget(button)
        buttons.addStretch(1)
        layout.addLayout(buttons)

        self.asset_table = QTableWidget(0, 5)
        self.asset_table.setHorizontalHeaderLabels(["ID", "Name", "Type", "Environment", "Owner"])
        self.asset_table.setAlternatingRowColors(True)
        self.asset_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.asset_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.asset_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.asset_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.asset_table, 1)
        return page

    def _build_vulnerabilities_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        section = QLabel("Public vulnerability intelligence")
        section.setObjectName("section")
        layout.addWidget(section)
        note = QLabel(
            "Look up a specific CVE in NIST NVD and enrich it using the CISA KEV catalog. "
            "The lookup runs in the background; results are saved locally."
        )
        note.setWordWrap(True)
        note.setStyleSheet("color: #aab9c9;")
        layout.addWidget(note)

        controls = QHBoxLayout()
        self.cve_input = QLineEdit()
        self.cve_input.setPlaceholderText("CVE-2025-12345")
        self.cve_input.returnPressed.connect(self.lookup_cve)
        self.lookup_button = QPushButton("Look up CVE")
        self.lookup_button.clicked.connect(self.lookup_cve)
        self.export_button = QPushButton("Export PDF")
        self.export_button.clicked.connect(self.export_report)
        self.export_button.setStyleSheet("background: #26384d;")
        controls.addWidget(self.cve_input, 1)
        controls.addWidget(self.lookup_button)
        controls.addWidget(self.export_button)
        layout.addLayout(controls)

        self.intel_status = QLabel("No lookup performed in this session.")
        self.intel_status.setWordWrap(True)
        self.intel_status.setStyleSheet("color: #8da4bc; padding: 4px 0;")
        layout.addWidget(self.intel_status)

        self.vulnerability_table = QTableWidget(0, 6)
        self.vulnerability_table.setHorizontalHeaderLabels(
            ["CVE", "Priority", "CVSS", "Severity", "CISA KEV", "Source / retrieved"]
        )
        self.vulnerability_table.setAlternatingRowColors(True)
        self.vulnerability_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.vulnerability_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.vulnerability_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.vulnerability_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.vulnerability_table, 1)
        return page

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

    def delete_selected_asset(self) -> None:
        row = self.asset_table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Select an asset", "Choose an asset in the table first.")
            return
        item = self.asset_table.item(row, 0)
        if item is None:
            return
        asset_id = int(item.text())
        answer = QMessageBox.question(
            self,
            "Delete asset",
            "Delete the selected asset from this computer?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer == QMessageBox.StandardButton.Yes:
            self.store.delete_asset(asset_id)
            self.refresh_assets()

    def refresh_assets(self) -> None:
        assets = self.store.list_assets()
        self.asset_table.setRowCount(len(assets))
        for row_index, asset in enumerate(assets):
            values = [str(asset["id"]), asset["name"], asset["asset_type"], asset["environment"], asset["owner"]]
            for column_index, value in enumerate(values):
                self.asset_table.setItem(row_index, column_index, QTableWidgetItem(value))

    def lookup_cve(self) -> None:
        cve_id = self.cve_input.text().strip()
        if self.lookup_worker is not None and self.lookup_worker.isRunning():
            return
        if not cve_id:
            QMessageBox.information(self, "CVE required", "Enter a CVE identifier such as CVE-2025-12345.")
            return
        self.lookup_button.setEnabled(False)
        self.intel_status.setText("Querying NIST NVD and CISA KEV…")
        self.lookup_worker = IntelligenceWorker(cve_id)
        self.lookup_worker.succeeded.connect(self.on_lookup_succeeded)
        self.lookup_worker.failed.connect(self.on_lookup_failed)
        self.lookup_worker.finished.connect(self.on_lookup_finished)
        self.lookup_worker.start()

    def on_lookup_succeeded(self, records: object) -> None:
        if not isinstance(records, list) or not all(isinstance(record, VulnerabilityRecord) for record in records):
            self.intel_status.setText("The source returned an unexpected response; nothing was saved.")
            return
        count = self.vulnerability_store.upsert_records(records)
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        self.vulnerability_store.record_sync(
            "NIST NVD + CISA KEV", now, now, "success", count, "Single-CVE lookup"
        )
        self.refresh_vulnerabilities()
        self.intel_status.setText(f"Saved {count} CVE record(s). Source dates are shown in the table and report.")

    def on_lookup_failed(self, message: str) -> None:
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        self.vulnerability_store.record_sync(
            "NIST NVD + CISA KEV", now, now, "error", 0, message[:500]
        )
        self.intel_status.setText(f"Lookup failed. No new vulnerability records were saved. {message}")

    def on_lookup_finished(self) -> None:
        self.lookup_button.setEnabled(True)

    def refresh_vulnerabilities(self) -> None:
        records = self.vulnerability_store.list_records()
        self.vulnerability_table.setRowCount(len(records))
        from vanguard.prioritization import assess_priority

        for row_index, record in enumerate(records):
            vulnerability = VulnerabilityRecord(
                cve_id=record["cve_id"], description=record["description"], published=record["published"],
                last_modified=record["last_modified"], cvss_score=record["cvss_score"],
                cvss_severity=record["cvss_severity"], source=record["source"],
                retrieved_at=record["retrieved_at"], known_exploited=bool(record["known_exploited"]),
            )
            priority = assess_priority(vulnerability).priority
            values = [
                record["cve_id"], priority,
                str(record["cvss_score"]) if record["cvss_score"] is not None else "N/A",
                record["cvss_severity"] or "Unknown",
                "Yes" if record["known_exploited"] else "No",
                f'{record["source"]} · {record["retrieved_at"]}',
            ]
            for column_index, value in enumerate(values):
                self.vulnerability_table.setItem(row_index, column_index, QTableWidgetItem(value))

    def export_report(self) -> None:
        records = self.vulnerability_store.list_records()
        if not records:
            QMessageBox.information(self, "No records", "Look up and save at least one CVE before exporting.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export vulnerability report", str(Path.home() / "vanguard-report.pdf"), "PDF files (*.pdf)"
        )
        if not path:
            return
        if not path.lower().endswith(".pdf"):
            path += ".pdf"
        try:
            output = generate_vulnerability_report(path, records, language="en")
        except (OSError, RuntimeError, ValueError) as error:
            QMessageBox.warning(self, "PDF export failed", str(error))
            return
        QMessageBox.information(self, "Report exported", f"Saved PDF report to:\n{output}")


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("ZettaCore Vanguard")
    app.setOrganizationName("ZettaCore")
    window = VanguardWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

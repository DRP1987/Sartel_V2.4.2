"""Update notification dialog for SarTel application."""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QMessageBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont
from utils.updater import download_update, apply_update
from config.app_config import APP_VERSION


class DownloadThread(QThread):
    """Background thread for downloading the update ZIP."""

    progress = pyqtSignal(int, int)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, download_url, checksum=None):
        super().__init__()
        self.download_url = download_url
        self.checksum = checksum

    def run(self):
        path = download_update(
            self.download_url,
            checksum_sha256=self.checksum,
            progress_callback=self._on_progress,
        )
        if path:
            self.finished.emit(path)
        else:
            self.error.emit("Download failed or checksum mismatch. Please try again later.")

    def _on_progress(self, downloaded, total):
        self.progress.emit(downloaded, total)


class UpdateDialog(QDialog):
    """
    Dialog shown when an update is available.
    Lets the user choose to update now or skip.
    Shows download progress and applies the update on completion.
    """

    def __init__(self, manifest, parent=None):
        """
        Args:
            manifest: dict from version.json with keys:
                      latest_version, release_date, download_url,
                      (optional) checksum_sha256, (optional) release_notes
        """
        super().__init__(parent)
        self.manifest = manifest
        self.download_thread = None
        self._zip_path = None

        self.setWindowTitle("Software Update Available")
        self.setMinimumWidth(500)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        title = QLabel("Update Available")
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        title.setFont(font)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        latest   = self.manifest.get("latest_version", "?")
        rel_date = self.manifest.get("release_date", "?")
        info = QLabel(
            "<b>Current version:</b> {current}<br>"
            "<b>New version:</b> {latest}<br>"
            "<b>Release date:</b> {date}".format(
                current=APP_VERSION, latest=latest, date=rel_date
            )
        )
        info.setAlignment(Qt.AlignCenter)
        layout.addWidget(info)

        notes = self.manifest.get("release_notes", "")
        if notes:
            notes_label = QLabel("<i>{}</i>".format(notes))
            notes_label.setWordWrap(True)
            notes_label.setAlignment(Qt.AlignCenter)
            notes_label.setStyleSheet("color: #555555; font-size: 10pt;")
            layout.addWidget(notes_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet(
            "QProgressBar { border: 2px solid #cccccc; border-radius: 5px; text-align: center; }"
            "QProgressBar::chunk { background-color: #4CAF50; border-radius: 3px; }"
        )
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 10pt; color: #555555;")
        layout.addWidget(self.status_label)

        btn_layout = QHBoxLayout()

        self.skip_btn = QPushButton("Skip This Update")
        self.skip_btn.setMinimumHeight(36)
        self.skip_btn.setStyleSheet(
            "QPushButton { background-color: #9E9E9E; color: white; border: none; border-radius: 5px; font-size: 10pt; }"
            "QPushButton:hover { background-color: #757575; }"
        )
        self.skip_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.skip_btn)

        self.update_btn = QPushButton("Download and Install")
        self.update_btn.setMinimumHeight(36)
        self.update_btn.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; border: none; border-radius: 5px; font-size: 10pt; font-weight: bold; }"
            "QPushButton:hover { background-color: #388E3C; }"
            "QPushButton:disabled { background-color: #cccccc; color: #666666; }"
        )
        self.update_btn.clicked.connect(self._start_download)
        btn_layout.addWidget(self.update_btn)

        layout.addLayout(btn_layout)

    def _start_download(self):
        """Begin downloading the update in a background thread."""
        url      = self.manifest.get("download_url", "")
        checksum = self.manifest.get("checksum_sha256", None)

        if not url:
            QMessageBox.critical(self, "Error", "No download URL found in update manifest.")
            return

        self.update_btn.setEnabled(False)
        self.skip_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.status_label.setText("Connecting...")

        self.download_thread = DownloadThread(url, checksum)
        self.download_thread.progress.connect(self._on_progress)
        self.download_thread.finished.connect(self._on_download_finished)
        self.download_thread.error.connect(self._on_download_error)
        self.download_thread.start()

    def _on_progress(self, downloaded, total):
        if total > 0:
            self.progress_bar.setRange(0, total)
            self.progress_bar.setValue(downloaded)
            mb_done  = downloaded / 1048576
            mb_total = total / 1048576
            self.status_label.setText("Downloading... {:.1f} / {:.1f} MB".format(mb_done, mb_total))
        else:
            self.progress_bar.setRange(0, 0)
            self.status_label.setText("Downloading...")

    def _on_download_finished(self, zip_path):
        self._zip_path = zip_path
        self.status_label.setText("Download complete! Preparing to install...")
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(1)

        QMessageBox.information(
            self,
            "Download Complete",
            "The application will now close and the update will be installed automatically.\n"
            "It will relaunch once the update is complete.\n\n"
            "Be patient, the tool will be opening in one minute."
        )
        apply_update(zip_path)

    def _on_download_error(self, message):
        self.progress_bar.setVisible(False)
        self.status_label.setText("")
        self.update_btn.setEnabled(True)
        self.skip_btn.setEnabled(True)
        QMessageBox.critical(self, "Download Failed", message)

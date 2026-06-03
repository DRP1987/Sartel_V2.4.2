"""Documentation widget for displaying available documents with PDF links."""

import os
import sys
import platform
import subprocess
import json
from functools import partial
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QListWidget, QListWidgetItem, QPushButton,
                             QMessageBox, QFrame)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from utils.resource_path import resource_path


class DocumentationWidget(QWidget):
    """Widget to display a list of available documents with PDF links."""

    def __init__(self, parent=None):
        """Initialize documentation widget."""
        super().__init__(parent)
        self.documents = []
        self.init_ui()
        self.load_documents()

    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Header
        header_layout = QHBoxLayout()

        title_label = QLabel("📄 Documentation")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.load_documents)
        header_layout.addWidget(refresh_btn)

        layout.addLayout(header_layout)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator)

        # Instructions
        instructions = QLabel(
            "Select a document from the list below and click the 📖 button to open it."
        )
        instructions.setStyleSheet("font-size: 12px; color: #666666; margin-bottom: 5px;")
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        # Document list label
        list_label = QLabel("Available Documents:")
        list_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(list_label)

        # Document list
        self.doc_list = QListWidget()
        self.doc_list.setStyleSheet("""
            QListWidget {
                background-color: white;
                border: 1px solid #cccccc;
                border-radius: 5px;
                padding: 5px;
                font-size: 10pt;
            }
            QListWidget::item {
                padding: 5px;
            }
            QListWidget::item:selected {
                background-color: #E3F2FD;
            }
        """)
        self.doc_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.doc_list)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("margin: 5px; color: red;")
        layout.addWidget(self.status_label)

        # Footer
        footer_label = QLabel("💡 Double-click a document or click the 📖 button to open it")
        footer_label.setStyleSheet("color: #666666; font-style: italic;")
        footer_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(footer_label)

    def load_documents(self):
        """Load documents from JSON configuration file."""
        self.doc_list.clear()
        self.documents = []
        self.status_label.setText("")

        try:
            docs_file = resource_path("config/documents.json")

            if not os.path.exists(docs_file):
                self.status_label.setText("Documents configuration file not found.")
                return

            with open(docs_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.documents = data.get('documents', [])

            if not self.documents:
                self.status_label.setText("No documents available.")
                return

            # Populate list
            for idx, doc in enumerate(self.documents):
                doc_name = doc.get('name', 'Unnamed Document')
                pdf_path = doc.get('pdf_path', '')

                # Create list item
                item = QListWidgetItem(self.doc_list)

                # Create widget for this item
                item_widget = QWidget()
                item_layout = QHBoxLayout(item_widget)
                item_layout.setContentsMargins(5, 2, 5, 2)

                # Document name label
                name_label = QLabel(f"📄 {doc_name}")
                name_label.setStyleSheet("font-size: 11pt;")
                item_layout.addWidget(name_label)
                item_layout.addStretch()

                # Open button
                open_button = QPushButton("📖 Open")
                open_button.setMinimumSize(80, 30)
                open_button.setToolTip(f"Open {doc_name}")
                open_button.setStyleSheet("""
                    QPushButton {
                        font-size: 10pt;
                        border: 1px solid #ccc;
                        border-radius: 5px;
                        background-color: #f0f0f0;
                        padding: 3px 10px;
                    }
                    QPushButton:hover {
                        background-color: #e0e0e0;
                    }
                """)
                open_button.clicked.connect(partial(self._open_document, idx))
                item_layout.addWidget(open_button)

                item_widget.setLayout(item_layout)

                # Set the widget for the item
                item.setSizeHint(item_widget.sizeHint())
                self.doc_list.addItem(item)
                self.doc_list.setItemWidget(item, item_widget)

        except Exception as e:
            self.status_label.setText(f"Error loading documents: {str(e)}")

    def _on_item_double_clicked(self, item):
        """Handle double-click on a document item."""
        row = self.doc_list.row(item)
        if row >= 0:
            self._open_document(row)

    def _open_document(self, doc_index):
        """Open PDF document with system default viewer."""
        if doc_index < 0 or doc_index >= len(self.documents):
            return

        doc = self.documents[doc_index]
        pdf_path_str = doc.get('pdf_path', '')

        if not pdf_path_str:
            QMessageBox.warning(self, "No Document",
                                "No PDF file is linked to this document.")
            return

        try:
            pdf_path = resource_path(pdf_path_str)

            if not os.path.exists(pdf_path):
                QMessageBox.critical(self, "Document Not Found",
                                     f"Document file not found:\n{pdf_path_str}\n\n"
                                     f"Expected at: {pdf_path}\n\n"
                                     f"Please ensure the PDF file exists in the correct location.")
                return

            # Open PDF with system default viewer
            system = platform.system()
            if system == 'Windows':
                os.startfile(pdf_path)
            elif system == 'Darwin':  # macOS
                subprocess.run(['open', pdf_path], check=True)
            else:  # Linux
                subprocess.run(['xdg-open', pdf_path], check=True)

        except FileNotFoundError:
            QMessageBox.critical(self, "File Not Found",
                                 f"The PDF file could not be found:\n{pdf_path_str}")
        except subprocess.CalledProcessError as e:
            QMessageBox.critical(self, "Error Opening Document",
                                 f"Failed to open document:\n{str(e)}\n\n"
                                 f"Please ensure you have a PDF viewer installed.")
        except Exception as e:
            QMessageBox.critical(self, "Error Opening Document",
                                 f"Failed to open document:\n{str(e)}\n\n"
                                 f"Please ensure you have a PDF viewer installed.")

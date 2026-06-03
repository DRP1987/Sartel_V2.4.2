"""Release notes widget for displaying version history."""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QTextBrowser, QComboBox, QPushButton, QFrame)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import json
import os
from utils.resource_path import resource_path


class ReleaseNotesWidget(QWidget):
    """Widget to display release notes and version history."""
    
    def __init__(self, parent=None):
        """Initialize release notes widget."""
        super().__init__(parent)
        self.releases = []
        self.current_version = "Unknown"
        self.init_ui()
        self.load_release_notes()
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Header
        header_layout = QHBoxLayout()
        
        title_label = QLabel("📋 Release Notes")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Current version label
        self.version_label = QLabel("Current App Version: Loading...")
        version_font = QFont()
        version_font.setPointSize(10)
        self.version_label.setFont(version_font)
        self.version_label.setStyleSheet("color: #2196F3; font-weight: bold;")
        header_layout.addWidget(self.version_label)
        
        layout.addLayout(header_layout)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator)
        
        # Version selector
        selector_layout = QHBoxLayout()
        
        selector_label = QLabel("Select Version:")
        selector_layout.addWidget(selector_label)
        
        self.version_combo = QComboBox()
        self.version_combo.setMinimumWidth(150)
        self.version_combo.currentIndexChanged.connect(self.on_version_changed)
        selector_layout.addWidget(self. version_combo)
        
        selector_layout.addStretch()
        
        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.load_release_notes)
        selector_layout.addWidget(refresh_btn)
        
        layout.addLayout(selector_layout)
        
        # Release notes browser
        self.notes_browser = QTextBrowser()
        self.notes_browser. setOpenExternalLinks(True)
        self.notes_browser.setStyleSheet("""
            QTextBrowser {
                background-color: white;
                border: 1px solid #cccccc;
                border-radius: 5px;
                padding: 15px;
                font-size: 10pt;
            }
        """)
        layout.addWidget(self.notes_browser)
        
        # Footer
        footer_label = QLabel("💡 Check this tab for updates timeline")
        footer_label.setStyleSheet("color: #666666; font-style: italic;")
        footer_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(footer_label)
    
    def load_release_notes(self):
        """Load release notes from JSON file."""
        try:
            notes_file = resource_path("config/release_notes.json")
            
            if not os.path.exists(notes_file):
                self.show_error("Release notes file not found.")
                return
            
            with open(notes_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.current_version = data.get('current_version', 'Unknown')
            self.releases = data. get('releases', [])
            
            # Update version label
            self.version_label.setText(f"Current App Version: {self.current_version}")
            
            # Populate version combo box
            self.version_combo. clear()
            for release in self.releases:
                version = release.get('version', 'Unknown')
                date = release.get('date', '')
                self.version_combo. addItem(f"v{version} - {date}")
            
            # Show the latest release
            if self.releases:
                self.display_release(0)
            else:
                self.show_error("No release information available.")
                
        except Exception as e:
            self.show_error(f"Error loading release notes: {str(e)}")
    
    def on_version_changed(self, index):
        """Handle version selection change."""
        if index >= 0:
            self.display_release(index)
    
    def display_release(self, index):
        """Display release notes for specific version."""
        if index < 0 or index >= len(self.releases):
            return
        
        release = self.releases[index]
        
        # Build HTML content
        html = self.build_release_html(release)
        self.notes_browser.setHtml(html)
    
    def build_release_html(self, release):
        """Build HTML content for release notes."""
        version = release.get('version', 'Unknown')
        date = release.get('date', '')
        title = release.get('title', '')
        highlights = release.get('highlights', [])
        features = release.get('features', [])
        bug_fixes = release. get('bug_fixes', [])
        known_issues = release. get('known_issues', [])
        
        html = f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: 'Segoe UI', Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                h1 {{
                    color:  #2196F3;
                    border-bottom: 2px solid #2196F3;
                    padding-bottom: 10px;
                }}
                h2 {{
                    color: #1976D2;
                    margin-top: 20px;
                    margin-bottom: 10px;
                }}
                . version-header {{
                    background:  linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 20px;
                    border-radius: 8px;
                    margin-bottom: 20px;
                }}
                .version-title {{
                    font-size:  24px;
                    font-weight: bold;
                    margin:  0;
                }}
                .version-date {{
                    font-size:  14px;
                    opacity: 0.9;
                    margin-top: 5px;
                }}
                .section {{
                    margin-bottom:  20px;
                }}
                ul {{
                    margin-top: 5px;
                    padding-left: 25px;
                }}
                li {{
                    margin-bottom: 8px;
                }}
                .highlights {{
                    background-color: #E3F2FD;
                    padding: 15px;
                    border-radius: 5px;
                    border-left: 4px solid #2196F3;
                }}
                .bug-fixes {{
                    background-color: #E8F5E9;
                    padding: 15px;
                    border-radius: 5px;
                    border-left: 4px solid #4CAF50;
                }}
                .badge {{
                    display: inline-block;
                    padding: 3px 8px;
                    border-radius: 3px;
                    font-size: 12px;
                    font-weight: bold;
                    margin-right: 5px;
                }}
                .badge-new {{
                    background-color:  #4CAF50;
                    color: white;
                }}
                .badge-fix {{
                    background-color:  #2196F3;
                    color: white;
                }}
                .badge-issue {{
                    background-color:  #FF9800;
                    color: white;
                }}
            </style>
        </head>
        <body>
            <div class="version-header">
                <div class="version-title">Version {version} - {title}</div>
                <div class="version-date">Released: {date}</div>
            </div>
        """
        
        # Highlights section
        if highlights:
            html += """
            <div class="section highlights">
                <h2>✨ Highlights</h2>
                <ul>
            """
            for item in highlights:
                html += f"<li>{item}</li>"
            html += "</ul></div>"
        
        # Features section
        if features:
            html += """
            <div class="section">
                <h2><span class="badge badge-new">NEW</span> Features</h2>
                <ul>
            """
            for item in features: 
                html += f"<li>{item}</li>"
            html += "</ul></div>"
        
        # Bug fixes section
        if bug_fixes:
            html += """
            <div class="section bug-fixes">
                <h2><span class="badge badge-fix">FIX</span> Bug Fixes</h2>
                <ul>
            """
            for item in bug_fixes: 
                html += f"<li>{item}</li>"
            html += "</ul></div>"
        
        # Known issues section
        if known_issues:
            html += """
            <div class="section known-issues">
                <h2><span class="badge badge-issue">! </span> Known Issues</h2>
                <ul>
            """
            for item in known_issues:
                html += f"<li>{item}</li>"
            html += "</ul></div>"
        
        html += """
        </body>
        </html>
        """
        
        return html
    
    def show_error(self, message):
        """Display error message in the browser."""
        html = f"""
        <html>
        <body style="font-family: Arial; padding: 20px; text-align: center;">
            <h2 style="color: #f44336;">⚠️ Error</h2>
            <p>{message}</p>
        </body>
        </html>
        """
        self.notes_browser.setHtml(html)
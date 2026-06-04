"""Signal monitoring screen with tabs for CAN bus monitoring application."""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QTabWidget, QTextEdit,
                             QScrollArea, QPushButton, QHBoxLayout, QLabel,
                             QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog,
                             QSplitter, QCheckBox, QMessageBox, QLineEdit)
from PyQt5.QtCore import Qt, pyqtSlot, pyqtSignal, QTimer
from PyQt5.QtGui import QTextCursor
from datetime import datetime
from typing import Dict, Any, List, Set, Optional
import csv
from gui.widgets import SignalStatusWidget, ConnectionStatusWidget
from gui.utils import create_logo_widget
from canbus.pcan_interface import PCANInterface
from canbus.signal_matcher import SignalMatcher
from canbus.pgn_decoder import PGNDecoder
from canbus.dm1_decoder import DM1_PGN, decode_dm1
from config.app_config import APP_NAME



class MonitoringScreen(QWidget):
    """Main monitoring screen with signal status and logging tabs."""

    # Signal to navigate back to configuration selection
    back_to_config = pyqtSignal()

    def __init__(self, pcan_interface: PCANInterface, configuration: Dict[str, Any], 
                 baudrate: Optional[int], channel: Optional[str], connected: bool = True, parent=None):
        """
        Initialize monitoring screen.

        Args:
            pcan_interface: PCAN interface instance
            configuration: Selected configuration dictionary
            baudrate: CAN bus baud rate (None if offline)
            channel: PCAN channel name (None if offline)
            connected: Whether CAN connection is active
            parent: Parent widget
        """
        super().__init__(parent)
        self.pcan_interface = pcan_interface
        self.configuration = configuration
        self.baudrate = baudrate
        self.channel = channel
        self.connected = connected
        self.signal_widgets: Dict[str, SignalStatusWidget] = {}
        self.signal_matchers: Dict[str, Dict[str, Any]] = {}
        self.signal_last_status: Dict[str, bool] = {}  # Track last status for each signal
        
        # Real-time display buffer (limited size, for viewing)
        self.display_messages: List[Dict[str, Any]] = []
        self.max_display_messages = 1000  # Keep last 1000 messages visible

        # Logging buffer (unlimited, for CSV export)
        self.log_buffer: List[Dict[str, Any]] = []
        self.is_logging = False

        # Display pause state
        self.display_paused = False

        # Track last message time per CAN ID for cycle time calculation
        self.last_message_time: Dict[int, datetime] = {}

        # Pending messages queue for batched GUI updates
        self.pending_display_messages: List[Dict[str, Any]] = []
        self.max_pending_messages = 100  # Threshold to force immediate processing

        # CAN ID filtering
        self.active_can_ids: Dict[int, Dict[str, Any]] = {}  # {can_id: {'count': int, 'checkbox': QCheckBox}}
        self.filtered_can_ids: Set[int] = set()  # CAN IDs that are currently checked

        # Override mode tracking
        self.override_mode = False  # False = Append mode, True = Override mode
        self.override_row_map: Dict[int, int] = {}  # {can_id: row_index} for override mode

        # CAN ID column sort state (True = ascending, False = descending)
        self._sort_ascending = True

        # PGN live data decoder (None if config has no pgn_channels)
        self.pgn_decoder: Optional[PGNDecoder] = None
        # Live value label widgets: {label_name: QLabel}
        self.live_value_labels: Dict[str, QLabel] = {}

        # DM1 fault code tab (present when dm1_enabled is True in config)
        self.dm1_enabled: bool = bool(self.configuration.get('dm1_enabled', False))
        # Lamp status indicator labels: {lamp_key: QLabel}
        self.dm1_lamp_labels: Dict[str, QLabel] = {}
        # DTC table widget (set when tab is created)
        self.dm1_dtc_table = None
        # Status label shown above DTC table
        self.dm1_status_label = None
        # Per-source DM1 data: {source_addr: decoded_dict} - keyed by SA (0x00-0xFF)
        self.dm1_data_by_source: Dict[int, dict] = {}

        # Timer for batched GUI updates (60 FPS = smooth, no latency)
        self.display_update_timer = QTimer()
        self.display_update_timer.timeout.connect(self._batch_update_table)
        self.display_update_timer.setInterval(16)  # 16ms = ~60 FPS
        self.display_update_timer.start()

        self._init_ui()
        self._setup_signals()
        self._connect_to_can()

    def _init_ui(self):
        """Initialize user interface."""
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(800, 600)

        # Main layout
        layout = QVBoxLayout()

        # Top bar with logo and connection status
        top_bar = QHBoxLayout()
        
        # Logo in top left
        logo_widget = create_logo_widget(self)
        if logo_widget:
            top_bar.addWidget(logo_widget)
        
        top_bar.addStretch()
        
        # Connection status in top right
        self.connection_status_widget = ConnectionStatusWidget()
        self.connection_status_widget.set_connected(self.connected)
        top_bar.addWidget(self.connection_status_widget)
        
        layout.addLayout(top_bar)

        # Header with configuration info and back button
        header_layout = QHBoxLayout()
        
        # Back button
        self.back_button = QPushButton("← Back to Configuration")
        self.back_button.setMaximumWidth(200)
        self.back_button.clicked.connect(self._on_back_clicked)
        header_layout.addWidget(self.back_button)
        
        # Configuration info
        config_name = self.configuration.get('name', 'Unknown')
        if self.connected and self.baudrate and self.channel:
            header_text = f"Configuration: {config_name} | Channel: {self.channel} | Baud Rate: {self.baudrate} bps"
        else:
            header_text = f"Configuration: {config_name} | OFFLINE MODE"
        header_label = QLabel(header_text)
        header_label.setStyleSheet("font-size: 14px; font-weight: bold; margin: 10px;")
        header_layout.addWidget(header_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Offline mode warning
        if not self.connected:
            warning_label = QLabel("⚠️ Running in offline mode - No live CAN data available")
            warning_label.setStyleSheet(
                "background-color: #fff3cd; color: #856404; padding: 10px; "
                "border: 1px solid #ffc107; border-radius: 4px; margin: 10px;"
            )
            warning_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(warning_label)

        # Tab widget
        self.tab_widget = QTabWidget()

        # Tab 1: Signal Status
        self.signal_tab = self._create_signal_tab()
        self.tab_widget.addTab(self.signal_tab, "Signal Status")

        # Tab 2: Logging
        self.log_tab = self._create_log_tab()
        self.tab_widget.addTab(self.log_tab, "CAN Bus Log")

        # Tab 3: Live Engine Data — only if configuration has pgn_channels
        pgn_channels = self.configuration.get('pgn_channels', [])
        if pgn_channels:
            self.pgn_decoder = PGNDecoder(pgn_channels)
            self.live_data_tab = self._create_live_data_tab()
            self.tab_widget.addTab(self.live_data_tab, "📊 Live Engine Data")

        # Tab 4: DM1 Fault Codes — only if dm1_enabled is set in configuration
        if self.dm1_enabled:
            self.dm1_tab = self._create_dm1_tab()
            self.tab_widget.addTab(self.dm1_tab, "⚠️ DM1 Fault Codes")

        layout.addWidget(self.tab_widget)

        # Control buttons
        button_layout = QHBoxLayout()

        # Display control section
        display_control_layout = QHBoxLayout()
        display_label = QLabel("Display Control:")
        display_control_layout.addWidget(display_label)

        # Pause Display button
        self.pause_display_button = QPushButton("⏸ Pause Display")
        self.pause_display_button.clicked.connect(self._pause_display)
        display_control_layout.addWidget(self.pause_display_button)

        # Resume Display button
        self.resume_display_button = QPushButton("▶ Resume Display")
        self.resume_display_button.clicked.connect(self._resume_display)
        self.resume_display_button.setEnabled(False)  # Disabled by default
        display_control_layout.addWidget(self.resume_display_button)

        button_layout.addLayout(display_control_layout)

        # Separator
        separator = QLabel("|")
        separator.setStyleSheet("margin: 0 10px; color: gray;")
        button_layout.addWidget(separator)

        # Logging status indicator
        self.log_status_label = QLabel("Logging: Inactive")
        self.log_status_label.setStyleSheet("padding: 5px;")
        button_layout.addWidget(self.log_status_label)

        button_layout.addStretch()

        # Start Log button (NO BACKGROUND COLOR)
        self.start_log_button = QPushButton("Start Log")
        self.start_log_button.clicked.connect(self._start_logging)
        button_layout.addWidget(self.start_log_button)

        # Stop Log button (NO BACKGROUND COLOR)
        self.stop_log_button = QPushButton("Stop Log")
        self.stop_log_button.clicked.connect(self._stop_logging)
        self.stop_log_button.setEnabled(False)
        button_layout.addWidget(self.stop_log_button)

        layout.addLayout(button_layout)

        self.setLayout(layout)


    def _create_signal_tab(self) -> QWidget:
        """
        Create signal status tab.

        Returns:
            Signal status tab widget
        """
        tab = QWidget()
        layout = QVBoxLayout()

        # Scroll area for signals
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        # Container for signal widgets
        signals_container = QWidget()
        signals_layout = QVBoxLayout()
        signals_layout.setAlignment(Qt.AlignTop)

        # Create signal widgets from configuration
        signals = self.configuration.get('signals', [])
        for signal_config in signals:
            signal_name = signal_config.get('name', 'Unknown')
            signal_widget = SignalStatusWidget(signal_name)
            signals_layout.addWidget(signal_widget)

            # Store widget and config for later matching
            self.signal_widgets[signal_name] = signal_widget
            self.signal_matchers[signal_name] = signal_config
            
            # Pre-compute PGN for J1939 signals to optimize message processing
            if signal_config.get('protocol') == 'j1939':
                signal_config['_cached_pgn'] = SignalMatcher._extract_pgn(signal_config.get('can_id'))
            
            # Initialize status tracking to match LED's initial state (RED/False)
            self.signal_last_status[signal_name] = False

        signals_container.setLayout(signals_layout)
        scroll_area.setWidget(signals_container)
        layout.addWidget(scroll_area)

        tab.setLayout(layout)
        return tab

    def _create_log_tab(self) -> QWidget:
        """
        Create logging tab with CAN ID filter panel and table display.

        Returns:
            Logging tab widget
        """
        tab = QWidget()
        main_layout = QVBoxLayout()

        # Add Override Mode checkbox at the top
        self.override_mode_checkbox = QCheckBox("Override Mode (show latest message per CAN ID only)")
        self.override_mode_checkbox.setChecked(False)  # Default: Append mode
        self.override_mode_checkbox.stateChanged.connect(self._on_override_mode_changed)
        main_layout.addWidget(self.override_mode_checkbox)

        # Create horizontal splitter for filter panel and log table
        splitter = QSplitter(Qt.Horizontal)
        
        # LEFT PANEL: CAN ID Filter
        filter_panel = self._create_filter_panel()
        splitter.addWidget(filter_panel)
        
        # RIGHT PANEL: Log Table
        log_panel = self._create_log_table_panel()
        splitter.addWidget(log_panel)
        
        # Set initial sizes (20% filter, 80% table)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 8)
        
        main_layout.addWidget(splitter)
        tab.setLayout(main_layout)
        return tab

    def _create_live_data_tab(self) -> QWidget:
        """
        Create the Live Engine Data tab with a grid of value cards.

        Returns:
            Live data tab widget
        """
        from PyQt5.QtWidgets import QFrame, QGridLayout

        tab = QWidget()
        outer_layout = QVBoxLayout()

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        grid_container = QWidget()
        grid_layout = QGridLayout()
        grid_layout.setSpacing(12)
        grid_layout.setContentsMargins(12, 12, 12, 12)

        labels = self.pgn_decoder.get_channel_labels()
        columns = 3
        for index, label in enumerate(labels):
            row = index // columns
            col = index % columns

            # Card frame
            card = QFrame()
            card.setFrameShape(QFrame.Box)
            card.setStyleSheet(
                "QFrame { background-color: #f8f9fa; border: 1px solid #dee2e6; "
                "border-radius: 8px; padding: 4px; }"
            )

            card_layout = QVBoxLayout()
            card_layout.setContentsMargins(8, 8, 8, 8)
            card_layout.setSpacing(4)

            # Channel name label
            name_label = QLabel(label)
            name_label.setAlignment(Qt.AlignCenter)
            name_label.setStyleSheet("font-size: 10pt; color: #495057;")
            name_label.setWordWrap(True)
            card_layout.addWidget(name_label)

            # Live value label
            value_label = QLabel("---")
            value_label.setAlignment(Qt.AlignCenter)
            value_label.setStyleSheet("font-size: 18pt; font-weight: bold; color: #212529;")
            card_layout.addWidget(value_label)

            card.setLayout(card_layout)
            grid_layout.addWidget(card, row, col)

            # Store reference for real-time updates
            self.live_value_labels[label] = value_label

        grid_container.setLayout(grid_layout)
        scroll_area.setWidget(grid_container)
        outer_layout.addWidget(scroll_area)

        # Footer note
        if self.connected:
            note_text = "Values update in real-time from J1939 CAN bus data"
        else:
            note_text = "⚠️ Offline mode — no live data. Values will show '---' until connected."
        note_label = QLabel(note_text)
        note_label.setAlignment(Qt.AlignCenter)
        note_label.setStyleSheet("color: #6c757d; font-size: 9pt; padding: 4px;")
        outer_layout.addWidget(note_label)

        tab.setLayout(outer_layout)
        return tab

    def _create_dm1_tab(self) -> QWidget:
        """
        Create the DM1 Fault Codes tab with lamp status indicators and a DTC table.

        Returns:
            DM1 fault codes tab widget
        """
        from PyQt5.QtWidgets import QFrame, QGridLayout, QTableWidget, QTableWidgetItem, QHeaderView

        tab = QWidget()
        outer_layout = QVBoxLayout()
        outer_layout.setContentsMargins(12, 12, 12, 12)
        outer_layout.setSpacing(10)

        # --- Lamp Status Section ---
        lamp_frame = QFrame()
        lamp_frame.setFrameShape(QFrame.Box)
        lamp_frame.setStyleSheet(
            "QFrame { background-color: #f8f9fa; border: 1px solid #dee2e6; "
            "border-radius: 8px; padding: 4px; }"
        )
        lamp_grid = QGridLayout()
        lamp_grid.setSpacing(10)
        lamp_grid.setContentsMargins(10, 8, 10, 8)

        lamp_section_title = QLabel("Lamp Status")
        lamp_section_title.setStyleSheet("font-size: 11pt; font-weight: bold; color: #343a40;")
        lamp_grid.addWidget(lamp_section_title, 0, 0, 1, 4)

        # Lamp definitions: (key, display name, on-colour, off-colour)
        lamp_defs = [
            ('red_stop',       'Red Stop\nLamp',       '#dc3545', '#e9ecef'),
            ('amber_warning',  'Amber Warning\nLamp',  '#fd7e14', '#e9ecef'),
            ('protect',        'Protect\nLamp',        '#dc3545', '#e9ecef'),
            ('aftertreatment', 'Aftertreatment\n(AdBlue/Exhaust)', '#007bff', '#e9ecef'),
        ]

        for col, (key, name, on_color, off_color) in enumerate(lamp_defs):
            card = QFrame()
            card.setFrameShape(QFrame.Box)
            card.setStyleSheet(
                f"QFrame {{ background-color: {off_color}; border: 1px solid #ced4da; "
                f"border-radius: 6px; }}"
            )
            card.setMinimumWidth(130)
            card_layout = QVBoxLayout()
            card_layout.setContentsMargins(8, 8, 8, 8)
            card_layout.setSpacing(4)

            name_lbl = QLabel(name)
            name_lbl.setAlignment(Qt.AlignCenter)
            name_lbl.setStyleSheet("font-size: 9pt; color: #495057;")
            name_lbl.setWordWrap(True)
            card_layout.addWidget(name_lbl)

            status_lbl = QLabel("Off")
            status_lbl.setAlignment(Qt.AlignCenter)
            status_lbl.setStyleSheet("font-size: 13pt; font-weight: bold; color: #6c757d;")
            card_layout.addWidget(status_lbl)

            card.setLayout(card_layout)
            lamp_grid.addWidget(card, 1, col)

            # Store card frame and status label for real-time updates
            self.dm1_lamp_labels[key] = {
                'card':        card,
                'status_lbl':  status_lbl,
                'on_color':    on_color,
                'off_color':   off_color,
            }

        lamp_frame.setLayout(lamp_grid)
        outer_layout.addWidget(lamp_frame)

        # --- DTC Status Label ---
        self.dm1_status_label = QLabel("Waiting for DM1 data…")
        self.dm1_status_label.setAlignment(Qt.AlignCenter)
        self.dm1_status_label.setStyleSheet(
            "color: #6c757d; font-size: 10pt; padding: 4px;"
        )
        outer_layout.addWidget(self.dm1_status_label)

        # --- Active DTC Table ---
        dtc_label = QLabel("Active Diagnostic Trouble Codes (DTCs)")
        dtc_label.setStyleSheet("font-size: 11pt; font-weight: bold; color: #343a40;")
        outer_layout.addWidget(dtc_label)

        self.dm1_dtc_table = QTableWidget()
        self.dm1_dtc_table.setColumnCount(4)
        self.dm1_dtc_table.setHorizontalHeaderLabels(['Source (SA)', 'SPN', 'FMI', 'FMI Description'])
        self.dm1_dtc_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.dm1_dtc_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.dm1_dtc_table.setAlternatingRowColors(True)
        self.dm1_dtc_table.setStyleSheet("font-family: monospace; font-size: 10pt;")

        hdr = self.dm1_dtc_table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Source
        hdr.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # SPN
        hdr.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # FMI
        hdr.setSectionResizeMode(3, QHeaderView.Stretch)           # Description

        outer_layout.addWidget(self.dm1_dtc_table)

        # Footer note
        if self.connected:
            note_text = "DM1 fault codes update in real-time from PGN 0xFECA"
        else:
            note_text = "⚠️ Offline mode — no live data available."
        note_label = QLabel(note_text)
        note_label.setAlignment(Qt.AlignCenter)
        note_label.setStyleSheet("color: #6c757d; font-size: 9pt; padding: 4px;")
        outer_layout.addWidget(note_label)

        tab.setLayout(outer_layout)
        return tab

    def _rebuild_dm1_display(self) -> None:
        """
        Rebuild the DM1 tab UI from all per-source data stored in dm1_data_by_source.

        Aggregates lamp statuses (worst-case across all sources) and collects DTCs
        from every source address, adding a 'Source (SA)' column so the user can
        see at a glance which ECU each DTC came from.
        """
        from PyQt5.QtWidgets import QTableWidgetItem

        # Lamp priority order: Off < Fast Flash < Slow Flash < On
        # Unknown values get -1 so they never override a known status.
        _LAMP_PRIORITY = {'Off': 0, 'Fast Flash': 1, 'Slow Flash': 2, 'On': 3}

        # --- Aggregate lamp status (worst-case across all sources) ---
        agg_lamps: Dict[str, str] = {
            'red_stop':       'Off',
            'amber_warning':  'Off',
            'protect':        'Off',
            'aftertreatment': 'Off',
        }
        for decoded in self.dm1_data_by_source.values():
            for key, status in decoded.get('lamps', {}).items():
                if key in agg_lamps and _LAMP_PRIORITY.get(status, -1) > _LAMP_PRIORITY.get(agg_lamps[key], 0):
                    agg_lamps[key] = status

        for key, widgets in self.dm1_lamp_labels.items():
            status_str = agg_lamps.get(key, 'Off')
            is_active = status_str != 'Off'
            bg_color = widgets['on_color'] if is_active else widgets['off_color']
            text_color = '#ffffff' if is_active else '#6c757d'
            widgets['card'].setStyleSheet(
                f"QFrame {{ background-color: {bg_color}; border: 1px solid #ced4da; "
                f"border-radius: 6px; }}"
            )
            widgets['status_lbl'].setText(status_str)
            widgets['status_lbl'].setStyleSheet(
                f"font-size: 13pt; font-weight: bold; color: {text_color};"
            )

        # --- Rebuild DTC table from all sources ---
        self.dm1_dtc_table.setRowCount(0)

        all_dtcs = []  # list of (sa_hex, dtc_dict)
        for sa, decoded in sorted(self.dm1_data_by_source.items()):
            for dtc in decoded.get('dtcs', []):
                all_dtcs.append((f"0x{sa:02X}", dtc))

        if not all_dtcs:
            self.dm1_status_label.setText("✅ No active fault codes")
            self.dm1_status_label.setStyleSheet(
                "color: #28a745; font-size: 10pt; font-weight: bold; padding: 4px;"
            )
        else:
            count = len(all_dtcs)
            src_count = len(self.dm1_data_by_source)
            self.dm1_status_label.setText(
                f"🔴 {count} active fault code{'s' if count != 1 else ''} "
                f"from {src_count} source{'s' if src_count != 1 else ''}"
            )
            self.dm1_status_label.setStyleSheet(
                "color: #dc3545; font-size: 10pt; font-weight: bold; padding: 4px;"
            )
            for sa_hex, dtc in all_dtcs:
                row = self.dm1_dtc_table.rowCount()
                self.dm1_dtc_table.insertRow(row)
                self.dm1_dtc_table.setItem(row, 0, QTableWidgetItem(sa_hex))
                self.dm1_dtc_table.setItem(row, 1, QTableWidgetItem(str(dtc['spn'])))
                self.dm1_dtc_table.setItem(row, 2, QTableWidgetItem(str(dtc['fmi'])))
                self.dm1_dtc_table.setItem(row, 3, QTableWidgetItem(dtc['fmi_desc']))


    def _create_filter_panel(self) -> QWidget:
        """Create CAN ID filter panel with search bar and checkboxes."""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("CAN ID Filter")
        title.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(title)

        # Search bar above checkboxes
        self.filter_search_box = QLineEdit()
        self.filter_search_box.setPlaceholderText("Search CAN ID…")
        self.filter_search_box.setClearButtonEnabled(True)
        self.filter_search_box.textChanged.connect(self._on_filter_search_changed)
        layout.addWidget(self.filter_search_box)
        
        # Scrollable area for checkboxes
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumWidth(250)
        scroll_area.setMinimumWidth(200)
        
        self.filter_container = QWidget()
        self.filter_layout = QVBoxLayout()
        self.filter_layout.setAlignment(Qt.AlignTop)
        self.filter_container.setLayout(self.filter_layout)
        
        scroll_area.setWidget(self.filter_container)
        layout.addWidget(scroll_area)
        
        # Select/Deselect buttons
        button_layout = QHBoxLayout()
        
        select_all_btn = QPushButton("Select All")
        select_all_btn.clicked.connect(self._select_all_filters)
        button_layout.addWidget(select_all_btn)
        
        deselect_all_btn = QPushButton("Deselect All")
        deselect_all_btn.clicked.connect(self._deselect_all_filters)
        button_layout.addWidget(deselect_all_btn)
        
        layout.addLayout(button_layout)
        panel.setLayout(layout)
        return panel

    def _create_log_table_panel(self) -> QWidget:
        """Create the log table panel."""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # Table widget for log display
        self.log_table = QTableWidget()
        self.log_table.setColumnCount(4)
        self.log_table.setHorizontalHeaderLabels(['CAN ID', 'Data', 'Timestamp', 'Cycle Time (ms)'])
        
        # Configure table appearance
        self.log_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.log_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.log_table.setAlternatingRowColors(True)
        self.log_table.setStyleSheet("font-family: monospace; font-size: 12pt;")
        
        # Set column widths
        header = self.log_table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # CAN ID
        header.setSectionResizeMode(1, QHeaderView.Stretch)            # Data
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Timestamp
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Cycle Time

        # Allow clicking CAN ID column header to sort
        header.setSortIndicatorShown(True)
        header.setSortIndicator(0, Qt.AscendingOrder)
        header.sectionClicked.connect(self._on_header_clicked)
        
        layout.addWidget(self.log_table)
        panel.setLayout(layout)
        return panel

    def _setup_signals(self):
        """Setup Qt signal connections."""
        self.pcan_interface.message_received.connect(self._on_message_received)
        self.pcan_interface.error_occurred.connect(self._on_error)

    def _add_can_id_to_filter(self, can_id: int):
        """Add a new CAN ID to the filter panel."""
        if can_id in self.active_can_ids:
            return  # Already exists
        
        # Create checkbox
        checkbox = QCheckBox(f"0x{can_id:03X} (0)")
        checkbox.setChecked(True)  # Default: show all
        checkbox.stateChanged.connect(lambda state, cid=can_id: self._on_filter_changed(cid, state))
        
        # Store reference
        self.active_can_ids[can_id] = {
            'checkbox': checkbox,
            'count': 0
        }
        self.filtered_can_ids.add(can_id)  # Add to visible set
        
        # Add to UI
        self.filter_layout.addWidget(checkbox)

    def _update_can_id_count(self, can_id: int):
        """Update message count for a CAN ID in the filter."""
        if can_id in self.active_can_ids:
            self.active_can_ids[can_id]['count'] += 1
            count = self.active_can_ids[can_id]['count']
            checkbox = self.active_can_ids[can_id]['checkbox']
            checkbox.setText(f"0x{can_id:03X} ({count})")

    def _on_filter_changed(self, can_id: int, state: int):
        """Handle checkbox state change."""
        if state == Qt.Checked:
            self.filtered_can_ids.add(can_id)
        else:
            self.filtered_can_ids.discard(can_id)
        
        # Rebuild table with filtered IDs
        self._rebuild_filtered_table()

    def _rebuild_filtered_table(self):
        """
        Rebuild table showing only checked CAN IDs.
        
        Note: This iterates through display_messages (max 1000 entries) which is
        acceptable for the use case. Filter changes are infrequent user actions,
        and the operation completes quickly with blockSignals() optimization.
        """
        # Block signals for performance
        self.log_table.blockSignals(True)

        vbar = self.log_table.verticalScrollBar()
        saved_scroll = vbar.value() if self.override_mode else None

        try:
            # Clear table
            self.log_table.setRowCount(0)
            
            if self.override_mode:
                self._populate_table_override_mode()
            else:
                self._populate_table_append_mode()
        
        finally:
            self.log_table.blockSignals(False)
        
        if self.override_mode:
            vbar.setValue(saved_scroll)
        else:
            self.log_table.scrollToBottom()

    def _populate_table_override_mode(self):
        """Populate table in override mode - one row per CAN ID."""
        self.override_row_map.clear()
        latest_messages = {}
        
        # Get latest message for each CAN ID by iterating backwards
        # This finds the most recent message efficiently
        for msg_data in reversed(self.display_messages):
            can_id = msg_data['can_id']
            if can_id in self.filtered_can_ids and can_id not in latest_messages:
                latest_messages[can_id] = msg_data
                # Optimization: stop early if we've found all filtered IDs
                if len(latest_messages) == len(self.filtered_can_ids):
                    break
        
        # Add rows sorted by CAN ID
        for can_id in sorted(latest_messages.keys()):
            row = self.log_table.rowCount()
            self.override_row_map[can_id] = row
            self._add_row_to_table(latest_messages[can_id])

    def _populate_table_append_mode(self):
        """Populate table in append mode - all messages chronologically."""
        for msg_data in self.display_messages:
            if msg_data['can_id'] in self.filtered_can_ids:
                self._add_row_to_table(msg_data)

    def _on_override_mode_changed(self, state):
        """Handle override mode checkbox change."""
        self.override_mode = (state == Qt.Checked)
        
        # Rebuild table in new mode
        if self.override_mode:
            self._switch_to_override_mode()
        else:
            self._switch_to_append_mode()

    def _switch_to_override_mode(self):
        """Switch table to override mode - one row per CAN ID."""
        self.log_table.blockSignals(True)
        try:
            # Clear table
            self.log_table.setRowCount(0)
            self._populate_table_override_mode()
        finally:
            self.log_table.blockSignals(False)

    def _switch_to_append_mode(self):
        """Switch table to append mode - all messages chronologically."""
        self.log_table.blockSignals(True)
        try:
            # Clear table
            self.log_table.setRowCount(0)
            self.override_row_map.clear()
            self._populate_table_append_mode()
        finally:
            self.log_table.blockSignals(False)
        
        self.log_table.scrollToBottom()

    def _update_row(self, row: int, msg_data: Dict[str, Any]):
        """Update an existing row with new message data (for override mode)."""
        # Validate row exists
        if row >= self.log_table.rowCount():
            return
        
        # Note: CAN ID doesn't change in override mode, so we skip updating column 0
        
        # Update Data column
        data_item = self.log_table.item(row, 1)
        if data_item is not None:
            data_str = " ".join(f"{b:02X}" for b in msg_data['data'])
            data_item.setText(data_str)
        
        # Update Timestamp column
        timestamp_item = self.log_table.item(row, 2)
        if timestamp_item is not None:
            timestamp_str = msg_data['timestamp'].strftime("%H:%M:%S.%f")[:-3]
            timestamp_item.setText(timestamp_str)
        
        # Update Cycle Time column
        cycle_time_item = self.log_table.item(row, 3)
        if cycle_time_item is not None:
            cycle_time = msg_data.get('cycle_time')
            if cycle_time is not None:
                cycle_time_str = f"{cycle_time:.1f}"
            else:
                cycle_time_str = "-"
            cycle_time_item.setText(cycle_time_str)

    def _add_row_to_table(self, msg_data: Dict[str, Any]):
        """Add a single row to the table."""
        row = self.log_table.rowCount()
        self.log_table.insertRow(row)
        
        # CAN ID
        can_id = msg_data['can_id']
        can_id_item = QTableWidgetItem(f"0x{can_id:03X}")
        self.log_table.setItem(row, 0, can_id_item)
        
        # Data
        data_str = " ".join(f"{b:02X}" for b in msg_data['data'])
        data_item = QTableWidgetItem(data_str)
        self.log_table.setItem(row, 1, data_item)
        
        # Timestamp
        timestamp_str = msg_data['timestamp'].strftime("%H:%M:%S.%f")[:-3]
        timestamp_item = QTableWidgetItem(timestamp_str)
        self.log_table.setItem(row, 2, timestamp_item)
        
        # Cycle Time
        cycle_time = msg_data.get('cycle_time')
        if cycle_time is not None:
            cycle_time_str = f"{cycle_time:.1f}"
        else:
            cycle_time_str = "-"
        cycle_time_item = QTableWidgetItem(cycle_time_str)
        self.log_table.setItem(row, 3, cycle_time_item)

    def _select_all_filters(self):
        """Check all CAN ID filter checkboxes."""
        for can_id, data in self.active_can_ids.items():
            data['checkbox'].setChecked(True)

    def _deselect_all_filters(self):
        """Uncheck all CAN ID filter checkboxes."""
        for can_id, data in self.active_can_ids.items():
            data['checkbox'].setChecked(False)

    def _on_filter_search_changed(self, text: str):
        """
        Show only filter checkboxes whose CAN ID contains the search text.

        Args:
            text: Current text in the search box
        """
        query = text.strip().lower()
        for can_id, data in self.active_can_ids.items():
            checkbox = data['checkbox']
            # Compare against the same format shown in the UI (e.g. "0x1A3" → "0x1a3")
            visible = not query or query in f"0x{can_id:03X}".lower()
            checkbox.setVisible(visible)

    def _on_header_clicked(self, column: int):
        """
        Sort the CAN Bus Log table by CAN ID when column 0 header is clicked.

        Repeated clicks toggle between ascending and descending order.

        Args:
            column: Index of the clicked header section
        """
        if column != 0:
            return

        self._sort_ascending = not self._sort_ascending
        self._sort_by_can_id(self._sort_ascending)

    def _sort_by_can_id(self, ascending: bool):
        """
        Sort visible table rows by CAN ID value.

        Rebuilds override_row_map when in override mode so subsequent
        real-time updates target the correct rows.

        Args:
            ascending: True for ascending order, False for descending
        """
        self.log_table.blockSignals(True)
        try:
            # Collect every row as a plain tuple of strings
            rows = []
            for i in range(self.log_table.rowCount()):
                row_data = tuple(
                    self.log_table.item(i, col).text()
                    if self.log_table.item(i, col) else ""
                    for col in range(self.log_table.columnCount())
                )
                rows.append(row_data)

            # Sort by numeric CAN ID value (column 0 is e.g. "0x1A3")
            def _can_id_key(row_tuple):
                try:
                    return int(row_tuple[0], 16)
                except (ValueError, TypeError):
                    return 0

            rows.sort(key=_can_id_key, reverse=not ascending)

            # Rewrite table with sorted rows
            self.log_table.setRowCount(0)
            for row_data in rows:
                row_idx = self.log_table.rowCount()
                self.log_table.insertRow(row_idx)
                for col, cell_text in enumerate(row_data):
                    self.log_table.setItem(row_idx, col, QTableWidgetItem(cell_text))

            # Keep override_row_map consistent with new row positions
            if self.override_mode:
                self.override_row_map.clear()
                for i in range(self.log_table.rowCount()):
                    item = self.log_table.item(i, 0)
                    if item:
                        try:
                            can_id = int(item.text(), 16)
                            self.override_row_map[can_id] = i
                        except (ValueError, TypeError):
                            pass

            # Update sort indicator arrow
            header = self.log_table.horizontalHeader()
            header.setSortIndicator(0, Qt.AscendingOrder if ascending else Qt.DescendingOrder)

        finally:
            self.log_table.blockSignals(False)

    def _connect_to_can(self):
        """Connect to CAN bus and start receiving (if connected)."""
        if self._is_offline_mode():
            print("Running in offline mode - no CAN connection")
            return
            
        if self.pcan_interface.connect(channel=self.channel, baudrate=self.baudrate):
            self.pcan_interface.start_receiving()
            print(f"Connected to CAN bus on {self.channel} at {self.baudrate} bps")
        else:
            print(f"ERROR: Failed to connect to CAN bus on {self.channel}")
            # Show warning but don't block - allow user to continue in offline mode
            QMessageBox.warning(
                self,
                "Connection Failed",
                f"Failed to connect to CAN bus on {self.channel}.\n"
                "Running in offline mode."
            )
            self._set_offline_mode()

    def _is_offline_mode(self) -> bool:
        """
        Check if running in offline mode.

        Returns:
            True if offline, False if connected
        """
        return not self.connected or not self.channel or not self.baudrate

    def _set_offline_mode(self):
        """Set the monitoring screen to offline mode."""
        self.connected = False
        self.connection_status_widget.set_connected(False)

    @pyqtSlot(object)
    def _on_message_received(self, message):
        """
        Handle received CAN message.

        Args:
            message: CAN message object
        """
        can_id = message.arbitration_id

        # Use the hardware receive timestamp from the CAN message for accurate
        # cycle time calculation.  python-can sets message.timestamp to the
        # time the frame was received at the hardware/driver level, so it is
        # not affected by Python event-loop scheduling delays.
        try:
            current_time = datetime.fromtimestamp(message.timestamp)
        except (AttributeError, OSError, ValueError):
            current_time = datetime.now()

        # Calculate cycle time (time since last message with the same CAN ID)
        cycle_time = None
        if can_id in self.last_message_time:
            last_time = self.last_message_time[can_id]
            cycle_time = (current_time - last_time).total_seconds() * 1000  # milliseconds

        # Update last message time for this CAN ID
        self.last_message_time[can_id] = current_time
        
        # Create message data dictionary
        msg_data = {
            'timestamp': current_time,
            'can_id': can_id,
            'data': bytes(message.data),
            'cycle_time': cycle_time
        }
        
        # Add to logging buffer if active
        if self.is_logging:
            self.log_buffer.append(msg_data)
        
        # Add to pending display queue (will be processed by timer)
        self.pending_display_messages.append(msg_data)
        
        # Limit pending queue size to prevent memory issues
        if len(self.pending_display_messages) > self.max_pending_messages:
            # If threshold exceeded, process immediately to prevent backup
            self._batch_update_table()
        
        # Check signal matches (lightweight operation, can stay here)
        for signal_name, signal_config in self.signal_matchers.items():
            # Get the CAN ID this signal is monitoring
            signal_can_id = signal_config.get('can_id')
            
            # Check if message is relevant to this signal based on protocol
            protocol = signal_config.get('protocol', None)
            is_relevant = False
            
            if protocol == 'j1939':
                # For J1939, compare PGNs (ignore priority and source address)
                received_pgn = SignalMatcher._extract_pgn(message.arbitration_id)
                # Use cached PGN if available, otherwise extract it
                config_pgn = signal_config.get('_cached_pgn')
                if config_pgn is None:
                    config_pgn = SignalMatcher._extract_pgn(signal_can_id)
                is_relevant = (received_pgn == config_pgn)
            else:
                # Standard CAN - exact CAN ID match
                is_relevant = (message.arbitration_id == signal_can_id)
            
            # Only process messages that match this signal's CAN ID or PGN
            if is_relevant:
                # This message is relevant to this signal - check if data matches
                is_match = SignalMatcher.match_signal(
                    signal_config,
                    message.arbitration_id,
                    list(message.data)
                )
                
                # Update LED only if status changed
                if signal_name in self.signal_widgets:
                    last_status = self.signal_last_status.get(signal_name, False)
                    
                    if is_match != last_status:
                        self.signal_widgets[signal_name].update_status(is_match)
                        self.signal_last_status[signal_name] = is_match
            # If message CAN ID doesn't match this signal's CAN ID, don't change LED state
            # This keeps the LED latched at its previous state

        # Decode PGN live data if decoder is active
        if self.pgn_decoder:
            decoded = self.pgn_decoder.decode(message.arbitration_id, list(message.data))
            for lbl, (value, unit) in decoded.items():
                if lbl in self.live_value_labels:
                    fmt = self.pgn_decoder.get_format(lbl)
                    display_text = fmt.format(value) + f" {unit}"
                    self.live_value_labels[lbl].setText(display_text)

        # Decode DM1 fault codes if tab is enabled
        if self.dm1_enabled:
            received_pgn = (message.arbitration_id >> 8) & 0x3FFFF
            if received_pgn == DM1_PGN:
                source_addr = message.arbitration_id & 0xFF
                dm1_data = decode_dm1(list(message.data))
                self.dm1_data_by_source[source_addr] = dm1_data
                self._rebuild_dm1_display()

    @pyqtSlot(str)
    def _on_error(self, error_message: str):
        """
        Handle error from PCAN interface.

        Args:
            error_message: Error message
        """
        # Display error in status bar or as a popup
        print(f"ERROR: {error_message}")

    def _batch_update_table(self):
        """
        Batch update table with pending messages.
        Called by timer at 60 FPS for smooth, efficient updates.
        """
        # If display is paused, don't update table (but keep accumulating messages)
        if self.display_paused:
            return
        
        # If no pending messages, nothing to do
        if not self.pending_display_messages:
            return
        
        # Get all pending messages and clear queue
        messages_to_add = self.pending_display_messages.copy()
        self.pending_display_messages.clear()
        
        # Add to display buffer
        self.display_messages.extend(messages_to_add)
        
        # Trim display buffer to max size
        if len(self.display_messages) > self.max_display_messages:
            overflow = len(self.display_messages) - self.max_display_messages
            self.display_messages = self.display_messages[overflow:]
            
            # If we removed messages from buffer, rebuild entire table
            self._rebuild_table()
            return
        
        # Block signals during batch update for performance
        self.log_table.blockSignals(True)

        # In override mode, keep the user's current scroll position static.
        # Qt can move the viewport when rows are inserted/updated, so we
        # capture the position before processing and restore it afterwards.
        vbar = self.log_table.verticalScrollBar()
        saved_scroll = vbar.value() if self.override_mode else None

        try:
            # Process each message
            for msg_data in messages_to_add:
                can_id = msg_data['can_id']
                
                # Check if this is a new CAN ID and add to filter
                # O(1) lookup since active_can_ids is a dict
                if can_id not in self.active_can_ids:
                    self._add_can_id_to_filter(can_id)
                
                # Update count for this CAN ID
                self._update_can_id_count(can_id)
                
                # Only add to visible table if CAN ID is in filtered set
                # O(1) lookup since filtered_can_ids is a set
                if can_id in self.filtered_can_ids:
                    if self.override_mode:
                        # OVERRIDE MODE: Update existing row or add new row
                        if can_id in self.override_row_map:
                            # Update existing row
                            row = self.override_row_map[can_id]
                            self._update_row(row, msg_data)
                        else:
                            # Add new row for this CAN ID
                            row = self.log_table.rowCount()
                            self.override_row_map[can_id] = row
                            self._add_row_to_table(msg_data)
                    else:
                        # APPEND MODE: Always add new row at bottom
                        self._add_row_to_table(msg_data)
        
        finally:
            # Re-enable signals
            self.log_table.blockSignals(False)

        # Restore scroll position in override mode so the user's view stays static.
        # In append mode, auto-scroll to the latest message.
        if self.override_mode:
            vbar.setValue(saved_scroll)
        else:
            self.log_table.scrollToBottom()

    def _pause_display(self):
        """Pause the display updates (messages still captured in background)."""
        self.display_paused = True
        
        # Update buttons
        self.pause_display_button.setEnabled(False)
        self.resume_display_button.setEnabled(True)
        
        # Update button text to show paused state
        self.pause_display_button.setText("⏸ Display Paused")
        
        print("Display paused - messages still being captured")

    def _resume_display(self):
        """Resume the display updates and catch up with buffered messages."""
        self.display_paused = False
        
        # Update buttons
        self.pause_display_button.setEnabled(True)
        self.resume_display_button.setEnabled(False)
        
        # Reset button text
        self.pause_display_button.setText("⏸ Pause Display")
        
        # Immediately process any pending messages to catch up
        if self.pending_display_messages:
            self._batch_update_table()
        
        print("Display resumed")

    def _rebuild_table(self):
        """
        Rebuild entire table from display buffer.
        Called when buffer is trimmed or cleared.
        """
        # Block signals for performance
        self.log_table.blockSignals(True)

        vbar = self.log_table.verticalScrollBar()
        saved_scroll = vbar.value() if self.override_mode else None

        try:
            # Clear table
            self.log_table.setRowCount(0)
            
            if self.override_mode:
                self._populate_table_override_mode()
            else:
                self._populate_table_append_mode()
        
        finally:
            self.log_table.blockSignals(False)
        
        if self.override_mode:
            vbar.setValue(saved_scroll)
        else:
            self.log_table.scrollToBottom()

    def _start_logging(self):
        """Start logging CAN messages to buffer."""
        self.is_logging = True
        self.log_buffer.clear()
        
        # Update UI (no colors)
        self.start_log_button.setEnabled(False)
        self.stop_log_button.setEnabled(True)
        self.log_status_label.setText("Logging: ACTIVE")
        self.log_status_label.setStyleSheet("padding: 5px; color: red; font-weight: bold;")
        
        print("Started logging CAN messages")

    def _stop_logging(self):
        """Stop logging and save to CSV."""
        self.is_logging = False
        
        # Update UI
        self.start_log_button.setEnabled(True)
        self.stop_log_button.setEnabled(False)
        self.log_status_label.setText("Logging: Inactive")
        self.log_status_label.setStyleSheet("padding: 5px;")
        
        print(f"Stopped logging. Captured {len(self.log_buffer)} messages")
        
        # Open save dialog immediately
        self._save_log_to_csv()
    
    def _save_log_to_csv(self):
        """Save logged messages to CSV file in SavvyCAN-compatible format."""
        from PyQt5.QtWidgets import QMessageBox
        
        if not self.log_buffer:
            QMessageBox.information(self, "No Data", "No logged messages to save.")
            return
        
        # Open file dialog with timestamp in default filename
        default_filename = f"can_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save CAN Bus Log",
            default_filename,
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if not filename:
            return
        
        try:
            # Use the first message timestamp as the log epoch
            start_time = self.log_buffer[0]['timestamp']

            # utf-8 (no BOM) is required for SavvyCAN compatibility;
            # a BOM would corrupt the first column header during import.
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                # SavvyCAN format header
                writer.writerow([
                    'Time Stamp', 'ID', 'Extended', 'Dir', 'Bus', 'LEN',
                    'D1', 'D2', 'D3', 'D4', 'D5', 'D6', 'D7', 'D8'
                ])

                for msg_data in self.log_buffer:
                    # Elapsed time in microseconds from the first logged message
                    delta_us = int(
                        (msg_data['timestamp'] - start_time).total_seconds() * 1_000_000
                    )

                    can_id = msg_data['can_id']
                    # Extended frame if CAN ID exceeds 11-bit standard range
                    is_extended = can_id > 0x7FF
                    can_id_str = f"{can_id:X}"  # uppercase hex, no "0x" prefix

                    data = msg_data['data']
                    data_len = len(data)
                    # Individual byte columns, empty string for unused slots
                    byte_cols = [f"{b:02X}" for b in data] + [''] * (8 - data_len)

                    writer.writerow([
                        delta_us,
                        can_id_str,
                        'True' if is_extended else 'False',
                        'Rx',
                        '0',
                        data_len,
                        *byte_cols
                    ])
            
            QMessageBox.information(
                self, 
                "Success", 
                f"Saved {len(self.log_buffer)} messages to:\n{filename}"
            )
            
            # Clear log buffer after successful save
            self.log_buffer.clear()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save log:\n{str(e)}")
    
    def _on_back_clicked(self):
        """Handle back button click."""
        # Resume display if paused
        if self.display_paused:
            self.display_paused = False
        
        # Stop display timer
        if self.display_update_timer.isActive():
            self.display_update_timer.stop()
        # Stop logging if active
        if self.is_logging:
            self.is_logging = False
        # Disconnect from CAN bus before going back
        self.pcan_interface.disconnect()
        # Emit signal to navigate back
        self.back_to_config.emit()

    def closeEvent(self, event):
        """
        Handle window close event.

        Args:
            event: Close event
        """
        # Resume display if paused
        if self.display_paused:
            self.display_paused = False
        
        # Stop display timer
        if self.display_update_timer.isActive():
            self.display_update_timer.stop()
        # Stop logging if active
        if self.is_logging:
            self.is_logging = False
        # Disconnect from CAN bus
        self.pcan_interface.disconnect()
        event.accept()

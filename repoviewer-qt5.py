#!/usr/bin/env python3
"""
YUM Repository Browser - Desktop GUI Application
Requires: PyQt5  →  dnf install python3-qt5
"""

import sys
import os
import gzip
import configparser
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QSplitter,
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTreeWidget, QTreeWidgetItem, QTextEdit,
    QFileDialog, QFrame, QHeaderView, QComboBox,
    QProgressBar, QMessageBox, QAction, QToolBar,
    QStatusBar, QAbstractItemView, QSizePolicy,
    QGroupBox, QScrollArea, QTabWidget, QListWidget,
    QListWidgetItem, QMenu, QToolButton, QShortcut
)
from PyQt5.QtCore import (
    Qt, QThread, pyqtSignal, QSortFilterProxyModel,
    QTimer, QUrl, QMimeData, QSize
)
from PyQt5.QtGui import (
    QFont, QColor, QPalette, QIcon, QPixmap,
    QDesktopServices, QClipboard, QKeySequence,
    QDragEnterEvent, QDropEvent, QBrush
)


# ─── Constants ───────────────────────────────────────────────────────────────

REPOMD_NS = "http://linux.duke.edu/metadata/repo"
COMMON_NS = "http://linux.duke.edu/metadata/common"

DARK_STYLE = """
QMainWindow, QWidget {
    background-color: #0d1117;
    color: #e6edf3;
    font-family: "DejaVu Sans", "Liberation Sans", sans-serif;
    font-size: 12px;
}

QSplitter::handle {
    background-color: #21262d;
    width: 2px;
    height: 2px;
}

/* ── Toolbar ── */
QToolBar {
    background-color: #161b22;
    border-bottom: 1px solid #21262d;
    padding: 4px 8px;
    spacing: 6px;
}
QToolBar QToolButton {
    background: transparent;
    border: 1px solid transparent;
    border-radius: 6px;
    padding: 5px 10px;
    color: #8b949e;
    font-size: 12px;
}
QToolBar QToolButton:hover {
    background-color: #21262d;
    border-color: #30363d;
    color: #e6edf3;
}
QToolBar QToolButton:pressed {
    background-color: #1c2128;
}

/* ── Status bar ── */
QStatusBar {
    background-color: #161b22;
    border-top: 1px solid #21262d;
    color: #8b949e;
    font-size: 11px;
    padding: 2px 8px;
}

/* ── Group boxes ── */
QGroupBox {
    border: 1px solid #21262d;
    border-radius: 6px;
    margin-top: 10px;
    padding-top: 8px;
    font-size: 11px;
    color: #8b949e;
    font-weight: bold;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
}

/* ── Repo list ── */
QListWidget {
    background-color: #161b22;
    border: 1px solid #21262d;
    border-radius: 6px;
    outline: none;
    padding: 4px;
}
QListWidget::item {
    border-radius: 4px;
    padding: 8px 10px;
    margin: 1px 0;
    color: #c9d1d9;
}
QListWidget::item:hover {
    background-color: #21262d;
}
QListWidget::item:selected {
    background-color: #1f3d27;
    color: #3fb950;
    border: 1px solid #2ea043;
}

/* ── Package tree ── */
QTreeWidget {
    background-color: #0d1117;
    alternate-background-color: #161b22;
    border: 1px solid #21262d;
    border-radius: 6px;
    outline: none;
    gridline-color: #21262d;
}
QTreeWidget::item {
    padding: 5px 4px;
    border: none;
}
QTreeWidget::item:hover {
    background-color: #1c2128;
}
QTreeWidget::item:selected {
    background-color: #1f3d27;
    color: #3fb950;
}
QHeaderView::section {
    background-color: #161b22;
    border: none;
    border-right: 1px solid #21262d;
    border-bottom: 1px solid #21262d;
    padding: 6px 10px;
    font-family: "DejaVu Sans Mono", monospace;
    font-size: 11px;
    font-weight: bold;
    color: #8b949e;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}
QHeaderView::section:hover {
    background-color: #21262d;
    color: #e6edf3;
}

/* ── Search & filter ── */
QLineEdit {
    background-color: #161b22;
    border: 1px solid #21262d;
    border-radius: 6px;
    padding: 6px 10px;
    color: #e6edf3;
    selection-background-color: #2ea043;
    font-family: "DejaVu Sans Mono", monospace;
    font-size: 12px;
}
QLineEdit:focus {
    border-color: #3fb950;
    background-color: #0d1117;
}
QLineEdit::placeholder {
    color: #484f58;
}

QComboBox {
    background-color: #161b22;
    border: 1px solid #21262d;
    border-radius: 6px;
    padding: 6px 10px;
    color: #c9d1d9;
    min-width: 110px;
}
QComboBox:focus { border-color: #3fb950; }
QComboBox::drop-down {
    border: none;
    width: 20px;
}
QComboBox QAbstractItemView {
    background-color: #161b22;
    border: 1px solid #30363d;
    selection-background-color: #1f3d27;
    color: #c9d1d9;
}

/* ── Text / detail pane ── */
QTextEdit {
    background-color: #161b22;
    border: 1px solid #21262d;
    border-radius: 6px;
    color: #c9d1d9;
    font-family: "DejaVu Sans Mono", monospace;
    font-size: 12px;
    padding: 8px;
    line-height: 1.5;
}

/* ── Buttons ── */
QPushButton {
    background-color: #21262d;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 6px 14px;
    color: #c9d1d9;
    font-size: 12px;
}
QPushButton:hover {
    background-color: #30363d;
    color: #e6edf3;
}
QPushButton:pressed {
    background-color: #1c2128;
}
QPushButton#btn_primary {
    background-color: #238636;
    border-color: #2ea043;
    color: #ffffff;
    font-weight: bold;
}
QPushButton#btn_primary:hover {
    background-color: #2ea043;
}
QPushButton#btn_primary:pressed {
    background-color: #1a6e2d;
}
QPushButton#btn_danger {
    background-color: #8b0000;
    border-color: #c00;
    color: #ffa0a0;
}

/* ── Progress bar ── */
QProgressBar {
    background-color: #21262d;
    border: none;
    border-radius: 3px;
    height: 4px;
    text-align: center;
    color: transparent;
}
QProgressBar::chunk {
    background-color: #3fb950;
    border-radius: 3px;
}

/* ── Tab widget ── */
QTabWidget::pane {
    border: 1px solid #21262d;
    border-radius: 6px;
    top: -1px;
}
QTabBar::tab {
    background-color: #0d1117;
    border: 1px solid #21262d;
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    padding: 6px 14px;
    color: #8b949e;
    font-size: 11px;
    margin-right: 2px;
}
QTabBar::tab:selected {
    background-color: #161b22;
    color: #e6edf3;
    border-color: #30363d;
}
QTabBar::tab:hover { color: #c9d1d9; }

/* ── Scrollbars ── */
QScrollBar:vertical {
    background: transparent;
    width: 8px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #30363d;
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover { background: #484f58; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }

QScrollBar:horizontal {
    background: transparent;
    height: 8px;
}
QScrollBar::handle:horizontal {
    background: #30363d;
    border-radius: 4px;
    min-width: 30px;
}
QScrollBar::handle:horizontal:hover { background: #484f58; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }

/* ── Frames / separators ── */
QFrame[frameShape="4"], QFrame[frameShape="5"] {
    color: #21262d;
}

/* ── Tooltips ── */
QToolTip {
    background-color: #1c2128;
    border: 1px solid #30363d;
    color: #c9d1d9;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 11px;
}

/* ── Menu ── */
QMenu {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 4px;
}
QMenu::item {
    padding: 6px 20px 6px 12px;
    border-radius: 4px;
    color: #c9d1d9;
}
QMenu::item:selected {
    background-color: #21262d;
    color: #e6edf3;
}
QMenu::separator {
    height: 1px;
    background: #21262d;
    margin: 4px 8px;
}
"""

MONO = QFont("DejaVu Sans Mono, Liberation Mono, Courier New", 11)
MONO_SM = QFont("DejaVu Sans Mono, Liberation Mono, Courier New", 10)
SANS = QFont("DejaVu Sans, Liberation Sans, Sans-serif", 11)


# ─── Background worker ────────────────────────────────────────────────────────

class FetchWorker(QThread):
    progress = pyqtSignal(str)          # status message
    finished = pyqtSignal(list, str)    # packages, error

    def __init__(self, repo_id, baseurl):
        super().__init__()
        self.repo_id = repo_id
        self.baseurl = baseurl.rstrip("/")

    def run(self):
        try:
            packages, error = self._fetch()
            self.finished.emit(packages, error or "")
        except Exception as e:
            self.finished.emit([], str(e))

    def _fetch_url(self, url, timeout=20):
        req = urllib.request.Request(
            url, headers={"User-Agent": "YumRepoBrowser/1.0"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read()

    def _fetch(self):
        self.progress.emit("Fetching repomd.xml…")
        repomd_url = f"{self.baseurl}/repodata/repomd.xml"
        try:
            repomd_data = self._fetch_url(repomd_url)
        except Exception as e:
            return [], f"Cannot reach repository: {e}"

        # Parse repomd.xml
        try:
            root = ET.fromstring(repomd_data)
        except ET.ParseError as e:
            return [], f"Failed to parse repomd.xml: {e}"

        primary_href = None
        for data_elem in root.findall(f"{{{REPOMD_NS}}}data"):
            if data_elem.get("type") == "primary":
                loc = data_elem.find(f"{{{REPOMD_NS}}}location")
                if loc is not None:
                    primary_href = loc.get("href")
                break

        if not primary_href:
            return [], "No primary metadata found in repomd.xml"

        self.progress.emit("Downloading package metadata…")
        primary_url = f"{self.baseurl}/{primary_href}"
        try:
            raw = self._fetch_url(primary_url)
            if primary_href.endswith(".gz"):
                raw = gzip.decompress(raw)
        except Exception as e:
            return [], f"Failed to fetch primary.xml: {e}"

        self.progress.emit("Parsing packages…")
        try:
            root = ET.fromstring(raw)
        except ET.ParseError as e:
            return [], f"Failed to parse primary.xml: {e}"

        packages = []
        for pkg in root.findall(f"{{{COMMON_NS}}}package"):
            if pkg.get("type") != "rpm":
                continue

            name    = pkg.findtext(f"{{{COMMON_NS}}}name", "")
            arch    = pkg.findtext(f"{{{COMMON_NS}}}arch", "")
            summary = pkg.findtext(f"{{{COMMON_NS}}}summary", "")
            desc    = (pkg.findtext(f"{{{COMMON_NS}}}description", "") or "").strip()
            proj_url= pkg.findtext(f"{{{COMMON_NS}}}url", "")
            packager= pkg.findtext(f"{{{COMMON_NS}}}packager", "")

            ver_el = pkg.find(f"{{{COMMON_NS}}}version")
            version = epoch = release = ""
            if ver_el is not None:
                version = ver_el.get("ver", "")
                release = ver_el.get("rel", "")
                epoch   = ver_el.get("epoch", "0")

            loc_el = pkg.find(f"{{{COMMON_NS}}}location")
            href = loc_el.get("href", "") if loc_el is not None else ""
            download_url = f"{self.baseurl}/{href}" if href else ""
            filename = href.split("/")[-1] if href else ""

            size_el = pkg.find(f"{{{COMMON_NS}}}size")
            size_str = ""
            if size_el is not None:
                try:
                    b = int(size_el.get("package", 0))
                    size_str = f"{b/1_048_576:.1f} MB" if b >= 1_048_576 else f"{b/1024:.0f} KB"
                except ValueError:
                    pass

            packages.append({
                "name":         name,
                "arch":         arch,
                "version":      version,
                "release":      release,
                "epoch":        epoch,
                "ver_full":     f"{version}-{release}",
                "summary":      summary,
                "description":  desc,
                "url":          proj_url,
                "download_url": download_url,
                "filename":     filename,
                "size":         size_str,
                "packager":     packager,
            })

        packages.sort(key=lambda p: p["name"].lower())
        return packages, None


# ─── Repo sidebar item ────────────────────────────────────────────────────────

class RepoListItem(QListWidgetItem):
    def __init__(self, repo: dict):
        super().__init__()
        self.repo = repo
        self.packages = []
        self.error = ""
        self.state = "idle"   # idle | fetching | done | error
        self._update_display()

    def _update_display(self):
        name = self.repo.get("name", self.repo["id"])
        count = f"  [{len(self.packages)} pkgs]" if self.state == "done" else ""
        icon  = {"idle": "○", "fetching": "◌", "done": "●", "error": "✕"}.get(self.state, "○")
        self.setText(f"{icon}  {name}{count}")
        self.setToolTip(self.repo.get("baseurl", ""))

    def set_state(self, state, packages=None, error=""):
        self.state = state
        if packages is not None:
            self.packages = packages
        self.error = error
        self._update_display()


# ─── Main Window ──────────────────────────────────────────────────────────────

class YumBrowserWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YUM Repository Browser")
        self.resize(1280, 800)
        self.setMinimumSize(900, 600)

        self.repos: dict[str, dict] = {}
        self._workers: dict[str, FetchWorker] = {}
        self._all_packages: list[dict] = []
        self._current_repo_item: RepoListItem | None = None

        self._build_ui()
        self._apply_style()
        self.setAcceptDrops(True)
        self.status("Ready — open a .repo file to begin")

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        # ── Toolbar ──
        tb = QToolBar("Main", self)
        tb.setIconSize(QSize(16, 16))
        tb.setMovable(False)
        self.addToolBar(tb)

        self._btn_open = QToolButton()
        self._btn_open.setText("📂  Open .repo")
        self._btn_open.setToolTip("Open a .repo file  (Ctrl+O)")
        self._btn_open.clicked.connect(self.open_repo_file)
        tb.addWidget(self._btn_open)

        tb.addSeparator()

        self._btn_fetch_all = QToolButton()
        self._btn_fetch_all.setText("⬇  Fetch All")
        self._btn_fetch_all.setToolTip("Fetch packages for all repos")
        self._btn_fetch_all.clicked.connect(self.fetch_all)
        self._btn_fetch_all.setEnabled(False)
        tb.addWidget(self._btn_fetch_all)

        self._btn_clear = QToolButton()
        self._btn_clear.setText("✕  Clear")
        self._btn_clear.setToolTip("Clear all repos")
        self._btn_clear.clicked.connect(self.clear_all)
        tb.addWidget(self._btn_clear)

        tb.addSeparator()

        # arch filter
        lbl = QLabel("  Arch: ")
        lbl.setStyleSheet("color: #8b949e; font-size: 11px;")
        tb.addWidget(lbl)
        self._arch_filter = QComboBox()
        self._arch_filter.addItems(["All", "x86_64", "aarch64", "noarch", "i686", "src"])
        self._arch_filter.currentTextChanged.connect(self._apply_filter)
        tb.addWidget(self._arch_filter)

        # spacer
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        tb.addWidget(spacer)

        # search
        self._search = QLineEdit()
        self._search.setPlaceholderText("🔍  Search packages…")
        self._search.setFixedWidth(280)
        self._search.textChanged.connect(self._apply_filter)
        tb.addWidget(self._search)
        tb.addWidget(QLabel("  "))

        # ── Status bar ──
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._progress = QProgressBar()
        self._progress.setRange(0, 0)
        self._progress.setFixedWidth(160)
        self._progress.setFixedHeight(6)
        self._progress.hide()
        self._status_bar.addPermanentWidget(self._progress)

        # ── Central splitter ──
        splitter = QSplitter(Qt.Horizontal)
        self.setCentralWidget(splitter)

        # Left panel
        left = QWidget()
        left.setFixedWidth(260)
        left.setMinimumWidth(200)
        lv = QVBoxLayout(left)
        lv.setContentsMargins(10, 10, 10, 10)
        lv.setSpacing(8)

        grp = QGroupBox("Repositories")
        gv = QVBoxLayout(grp)
        gv.setContentsMargins(6, 12, 6, 6)
        gv.setSpacing(6)

        self._repo_list = QListWidget()
        self._repo_list.setAlternatingRowColors(False)
        self._repo_list.currentItemChanged.connect(self._on_repo_selected)
        self._repo_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self._repo_list.customContextMenuRequested.connect(self._repo_context_menu)
        gv.addWidget(self._repo_list)

        row = QHBoxLayout()
        self._btn_fetch = QPushButton("⬇  Fetch Packages")
        self._btn_fetch.setObjectName("btn_primary")
        self._btn_fetch.setEnabled(False)
        self._btn_fetch.clicked.connect(self._fetch_current)
        row.addWidget(self._btn_fetch)
        gv.addLayout(row)

        lv.addWidget(grp)

        # Repo info box
        self._repo_info = QTextEdit()
        self._repo_info.setReadOnly(True)
        self._repo_info.setFixedHeight(120)
        self._repo_info.setPlaceholderText("Select a repo to see details…")
        lv.addWidget(self._repo_info)

        splitter.addWidget(left)

        # Right panel
        right = QWidget()
        rv = QVBoxLayout(right)
        rv.setContentsMargins(0, 10, 10, 10)
        rv.setSpacing(8)

        # Package count label
        self._pkg_label = QLabel("No packages loaded")
        self._pkg_label.setStyleSheet("color: #8b949e; font-size: 11px; padding-left: 4px;")
        rv.addWidget(self._pkg_label)

        # Package tree
        self._pkg_tree = QTreeWidget()
        self._pkg_tree.setRootIsDecorated(False)
        self._pkg_tree.setAlternatingRowColors(True)
        self._pkg_tree.setSelectionMode(QAbstractItemView.SingleSelection)
        self._pkg_tree.setSortingEnabled(True)
        self._pkg_tree.setColumnCount(5)
        self._pkg_tree.setHeaderLabels(["Package", "Version", "Arch", "Size", "Summary"])
        hdr = self._pkg_tree.header()
        hdr.setSectionResizeMode(0, QHeaderView.Interactive)
        hdr.setSectionResizeMode(1, QHeaderView.Interactive)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(4, QHeaderView.Stretch)
        self._pkg_tree.setColumnWidth(0, 240)
        self._pkg_tree.setColumnWidth(1, 150)
        self._pkg_tree.currentItemChanged.connect(self._on_pkg_selected)
        self._pkg_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self._pkg_tree.customContextMenuRequested.connect(self._pkg_context_menu)
        rv.addWidget(self._pkg_tree)

        # Detail pane tabs
        tabs = QTabWidget()
        tabs.setFixedHeight(200)

        # Description tab
        self._desc_view = QTextEdit()
        self._desc_view.setReadOnly(True)
        self._desc_view.setPlaceholderText("Select a package to see its description…")
        tabs.addTab(self._desc_view, "Description")

        # Download tab
        dl_widget = QWidget()
        dl_layout = QVBoxLayout(dl_widget)
        dl_layout.setContentsMargins(8, 8, 8, 8)
        dl_layout.setSpacing(8)

        url_row = QHBoxLayout()
        self._url_field = QLineEdit()
        self._url_field.setReadOnly(True)
        self._url_field.setPlaceholderText("Download URL appears here…")
        self._url_field.setFont(MONO_SM)
        url_row.addWidget(self._url_field)

        self._btn_copy_url = QPushButton("Copy URL")
        self._btn_copy_url.setFixedWidth(90)
        self._btn_copy_url.clicked.connect(self._copy_url)
        url_row.addWidget(self._btn_copy_url)

        self._btn_open_url = QPushButton("Open in Browser")
        self._btn_open_url.setFixedWidth(120)
        self._btn_open_url.clicked.connect(self._open_url)
        url_row.addWidget(self._btn_open_url)
        dl_layout.addLayout(url_row)

        # wget / dnf commands
        self._cmd_view = QTextEdit()
        self._cmd_view.setReadOnly(True)
        self._cmd_view.setFont(MONO_SM)
        self._cmd_view.setFixedHeight(80)
        dl_layout.addWidget(self._cmd_view)

        tabs.addTab(dl_widget, "Download")

        # Metadata tab
        self._meta_view = QTextEdit()
        self._meta_view.setReadOnly(True)
        self._meta_view.setFont(MONO_SM)
        tabs.addTab(self._meta_view, "Metadata")

        rv.addWidget(tabs)
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        # Keyboard shortcuts
        QShortcut(QKeySequence("Ctrl+O"), self, self.open_repo_file)
        QShortcut(QKeySequence("Ctrl+F"), self, lambda: self._search.setFocus())
        QShortcut(QKeySequence("Escape"), self, lambda: self._search.clear())

    def _apply_style(self):
        self.setStyleSheet(DARK_STYLE)
        # Monospace for tree
        self._pkg_tree.setFont(MONO_SM)
        self._repo_list.setFont(MONO_SM)

    # ── Drag & drop ───────────────────────────────────────────────────────────

    def dragEnterEvent(self, e: QDragEnterEvent):
        if e.mimeData().hasUrls():
            urls = e.mimeData().urls()
            if any(u.toLocalFile().endswith(".repo") for u in urls):
                e.acceptProposedAction()

    def dropEvent(self, e: QDropEvent):
        for url in e.mimeData().urls():
            path = url.toLocalFile()
            if path.endswith(".repo"):
                self._load_repo_file(path)

    # ── File handling ─────────────────────────────────────────────────────────

    def open_repo_file(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Open .repo File", os.path.expanduser("~"),
            "Repo Files (*.repo);;All Files (*)"
        )
        for path in paths:
            self._load_repo_file(path)

    def _load_repo_file(self, path: str):
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except OSError as e:
            QMessageBox.critical(self, "Error", f"Cannot read file:\n{e}")
            return

        cfg = configparser.ConfigParser()
        cfg.read_string(content)

        added = 0
        for section in cfg.sections():
            if section in self.repos:
                continue
            repo = {
                "id":        section,
                "name":      cfg.get(section, "name",      fallback=section),
                "baseurl":   cfg.get(section, "baseurl",   fallback="").strip(),
                "mirrorlist":cfg.get(section, "mirrorlist",fallback="").strip(),
                "enabled":   cfg.get(section, "enabled",   fallback="1"),
                "gpgcheck":  cfg.get(section, "gpgcheck",  fallback="0"),
                "gpgkey":    cfg.get(section, "gpgkey",    fallback=""),
            }
            self.repos[section] = repo
            item = RepoListItem(repo)
            self._repo_list.addItem(item)
            added += 1

        if added:
            self._btn_fetch_all.setEnabled(True)
            self.status(f"Loaded {added} repo(s) from {os.path.basename(path)}")
        else:
            self.status("No new repos found in file")

    # ── Repo selection ────────────────────────────────────────────────────────

    def _on_repo_selected(self, current, _):
        if not isinstance(current, RepoListItem):
            self._btn_fetch.setEnabled(False)
            return

        self._current_repo_item = current
        self._btn_fetch.setEnabled(True)
        repo = current.repo

        # Info box
        lines = []
        lines.append(f"ID:       {repo['id']}")
        lines.append(f"Name:     {repo['name']}")
        lines.append(f"BaseURL:  {repo.get('baseurl') or '(mirrorlist)'}")
        if repo.get("mirrorlist"):
            lines.append(f"Mirror:   {repo['mirrorlist']}")
        lines.append(f"Enabled:  {repo.get('enabled','?')}")
        lines.append(f"GPGCheck: {repo.get('gpgcheck','?')}")
        self._repo_info.setText("\n".join(lines))

        # Show cached packages if any
        self._populate_tree(current.packages)
        if current.error:
            self.status(f"Error: {current.error}", error=True)
        elif current.state == "done":
            self.status(f"{len(current.packages)} packages in {repo['name']}")
        else:
            self.status(f"Repo selected: {repo['name']}")

    def _repo_context_menu(self, pos):
        item = self._repo_list.itemAt(pos)
        if not isinstance(item, RepoListItem):
            return
        menu = QMenu(self)
        menu.addAction("⬇  Fetch Packages", lambda: self._fetch_repo(item))
        menu.addAction("📋  Copy Base URL", lambda: QApplication.clipboard().setText(item.repo.get("baseurl", "")))
        menu.addSeparator()
        menu.addAction("✕  Remove", lambda: self._remove_repo(item))
        menu.exec_(self._repo_list.mapToGlobal(pos))

    def _remove_repo(self, item: RepoListItem):
        rid = item.repo["id"]
        self.repos.pop(rid, None)
        row = self._repo_list.row(item)
        self._repo_list.takeItem(row)
        if not self.repos:
            self._btn_fetch_all.setEnabled(False)
        self._pkg_tree.clear()
        self.status("Repo removed")

    # ── Fetching ──────────────────────────────────────────────────────────────

    def _fetch_current(self):
        if self._current_repo_item:
            self._fetch_repo(self._current_repo_item)

    def fetch_all(self):
        for i in range(self._repo_list.count()):
            item = self._repo_list.item(i)
            if isinstance(item, RepoListItem) and item.state in ("idle", "error"):
                self._fetch_repo(item)

    def _fetch_repo(self, item: RepoListItem):
        rid = item.repo["id"]
        baseurl = item.repo.get("baseurl", "")
        if not baseurl:
            QMessageBox.warning(self, "No Base URL",
                f"Repo '{rid}' has no baseurl configured.")
            return
        if rid in self._workers and self._workers[rid].isRunning():
            return

        item.set_state("fetching")
        self._progress.show()
        self.status(f"Fetching {item.repo['name']}…")

        worker = FetchWorker(rid, baseurl)
        worker.progress.connect(lambda msg: self.status(msg))
        worker.finished.connect(lambda pkgs, err, i=item, r=rid: self._on_fetch_done(i, r, pkgs, err))
        self._workers[rid] = worker
        worker.start()

    def _on_fetch_done(self, item: RepoListItem, rid: str, packages: list, error: str):
        self._workers.pop(rid, None)

        if error:
            item.set_state("error", error=error)
            self.status(f"Error fetching {item.repo['name']}: {error}", error=True)
        else:
            item.set_state("done", packages=packages)
            self.status(f"Loaded {len(packages)} packages from {item.repo['name']}")

        # Hide spinner if no more workers
        if not any(w.isRunning() for w in self._workers.values()):
            self._progress.hide()

        # Refresh tree if this is the selected repo
        if item is self._current_repo_item:
            self._populate_tree(packages)

    # ── Package tree ──────────────────────────────────────────────────────────

    def _populate_tree(self, packages: list):
        self._all_packages = packages
        self._pkg_tree.clear()
        self._clear_detail()
        self._apply_filter()

    def _apply_filter(self):
        query = self._search.text().lower().strip()
        arch_filter = self._arch_filter.currentText()

        self._pkg_tree.clear()
        count = 0

        for pkg in self._all_packages:
            if arch_filter != "All" and pkg["arch"] != arch_filter:
                continue
            if query and not (
                query in pkg["name"].lower() or
                query in pkg["summary"].lower() or
                query in pkg["description"].lower()
            ):
                continue

            item = QTreeWidgetItem([
                pkg["name"],
                pkg["ver_full"],
                pkg["arch"],
                pkg["size"],
                pkg["summary"],
            ])
            item.setData(0, Qt.UserRole, pkg)
            item.setFont(0, MONO_SM)
            item.setFont(1, MONO_SM)

            # Arch colour
            arch_colors = {
                "x86_64":  "#79c0ff",
                "aarch64": "#bc8cff",
                "noarch":  "#e3b341",
                "i686":    "#ffa657",
                "src":     "#8b949e",
            }
            color = arch_colors.get(pkg["arch"], "#8b949e")
            item.setForeground(2, QBrush(QColor(color)))

            self._pkg_tree.addTopLevelItem(item)
            count += 1

        total = len(self._all_packages)
        if query or arch_filter != "All":
            self._pkg_label.setText(f"Showing {count} of {total} packages")
        else:
            self._pkg_label.setText(f"{total} packages" if total else "No packages loaded")

    def _on_pkg_selected(self, current, _):
        if current is None:
            self._clear_detail()
            return
        pkg = current.data(0, Qt.UserRole)
        if not pkg:
            return
        self._show_detail(pkg)

    def _show_detail(self, pkg: dict):
        # Description
        self._desc_view.setText(pkg["description"] or pkg["summary"] or "(no description)")

        # Download tab
        url = pkg["download_url"]
        self._url_field.setText(url)
        cmds = []
        if url:
            cmds.append(f"# Download with wget:")
            cmds.append(f"wget '{url}'")
            cmds.append("")
            cmds.append(f"# Install directly with dnf:")
            cmds.append(f"dnf install '{url}'")
        self._cmd_view.setText("\n".join(cmds))

        # Metadata
        meta_lines = [
            f"Name:        {pkg['name']}",
            f"Version:     {pkg['ver_full']}",
            f"Arch:        {pkg['arch']}",
            f"Epoch:       {pkg['epoch']}",
            f"Size:        {pkg['size']}",
            f"Filename:    {pkg['filename']}",
            f"Packager:    {pkg['packager']}",
            f"Project URL: {pkg['url']}",
            f"",
            f"Download URL:",
            f"  {pkg['download_url']}",
        ]
        self._meta_view.setText("\n".join(meta_lines))

    def _clear_detail(self):
        self._desc_view.clear()
        self._url_field.clear()
        self._cmd_view.clear()
        self._meta_view.clear()

    def _pkg_context_menu(self, pos):
        item = self._pkg_tree.itemAt(pos)
        if not item:
            return
        pkg = item.data(0, Qt.UserRole)
        if not pkg:
            return
        menu = QMenu(self)
        menu.addAction("📋  Copy Download URL",
                       lambda: QApplication.clipboard().setText(pkg["download_url"]))
        menu.addAction("📋  Copy Package Name",
                       lambda: QApplication.clipboard().setText(pkg["name"]))
        menu.addAction("🌐  Open URL in Browser",
                       lambda: QDesktopServices.openUrl(QUrl(pkg["download_url"])))
        if pkg["url"]:
            menu.addAction("🌐  Open Project URL",
                           lambda: QDesktopServices.openUrl(QUrl(pkg["url"])))
        menu.exec_(self._pkg_tree.mapToGlobal(pos))

    # ── Actions ───────────────────────────────────────────────────────────────

    def _copy_url(self):
        url = self._url_field.text()
        if url:
            QApplication.clipboard().setText(url)
            self.status("URL copied to clipboard")

    def _open_url(self):
        url = self._url_field.text()
        if url:
            QDesktopServices.openUrl(QUrl(url))

    def clear_all(self):
        if self.repos and QMessageBox.question(
            self, "Clear All", "Remove all loaded repos?",
            QMessageBox.Yes | QMessageBox.No
        ) != QMessageBox.Yes:
            return
        self._repo_list.clear()
        self._pkg_tree.clear()
        self.repos.clear()
        self._workers.clear()
        self._all_packages.clear()
        self._current_repo_item = None
        self._repo_info.clear()
        self._clear_detail()
        self._btn_fetch.setEnabled(False)
        self._btn_fetch_all.setEnabled(False)
        self._pkg_label.setText("No packages loaded")
        self._progress.hide()
        self.status("Cleared")

    # ── Utilities ─────────────────────────────────────────────────────────────

    def status(self, msg: str, error: bool = False):
        color = "#f85149" if error else "#8b949e"
        self._status_bar.setStyleSheet(f"color: {color};")
        self._status_bar.showMessage(msg)


# ─── Entry point ──────────────────────────────────────────────────────────────

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("YUM Repository Browser")
    app.setOrganizationName("YumBrowser")

    # High DPI
    app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    win = YumBrowserWindow()
    win.show()

    # Open files passed as CLI args
    for arg in sys.argv[1:]:
        if arg.endswith(".repo") and os.path.isfile(arg):
            win._load_repo_file(arg)

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()


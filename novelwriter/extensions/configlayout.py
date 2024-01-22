"""
novelWriter – Custom Widget: Config Layout
==========================================

File History:
Created: 2020-05-03 [0.4.5] NConfigLayout, NColourLabel
Created: 2023-05-23 [2.1b1] NSimpleLayout
Created: 2024-01-08 [2.3b1] NScrollableForm

This file is a part of novelWriter
Copyright 2018–2024, Veronica Berglyd Olsen

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""
from __future__ import annotations

from PyQt5.QtGui import QColor, QPalette
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QAbstractButton, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QScrollArea, QSizePolicy,
    QVBoxLayout, QWidget
)

from novelwriter import CONFIG

FONT_SCALE = 0.9
RIGHT_TOP = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop
LEFT_TOP = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop


class NScrollableForm(QScrollArea):
    """Extension: Scrollable Form Widget

    A custom widget that creates a form within a scrollable area.
    """

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent=parent)
        self._helpCol = QColor(0, 0, 0)
        self._fontScale = FONT_SCALE
        self._first = True

        self._sections: dict[int, QLabel] = {}
        self._editable: dict[str, NColourLabel] = {}
        self._index: dict[str, QWidget] = {}

        self._layout = QVBoxLayout()
        self._layout.setSpacing(CONFIG.pxInt(12))

        self._widget = QWidget(self)
        self._widget.setLayout(self._layout)

        self.setWidget(self._widget)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        return

    ##
    #  Properties
    ##

    @property
    def labels(self) -> list[str]:
        return list(self._index.keys())

    ##
    #  Setters
    ##

    def setHelpTextStyle(self, color: QColor, scale: float = FONT_SCALE) -> None:
        """Set the text color for the help text."""
        self._helpCol = color
        self._fontScale = scale
        return

    def setHelpText(self, key: str, text: str) -> None:
        """Set the text for the help label."""
        if qHelp := self._editable.get(key):
            qHelp.setText(text)
        return

    ##
    #  Methods
    ##

    def scrollToSection(self, identifier: int) -> None:
        """Scroll to the requested section identifier."""
        if identifier in self._sections:
            yPos = self._sections[identifier].pos().y() - CONFIG.pxInt(8)
            self.verticalScrollBar().setValue(yPos)
        return

    def scrollToLabel(self, label: str) -> None:
        """Scroll to the requested label."""
        if label in self._index:
            yPos = self._index[label].pos().y() - CONFIG.pxInt(8)
            self.verticalScrollBar().setValue(yPos)
        return

    def addGroupLabel(self, label: str, identifier: int) -> None:
        """Add a text label to separate groups of settings."""
        hM = CONFIG.pxInt(4)
        qLabel = QLabel(f"<b>{label}</b>", self)
        qLabel.setContentsMargins(0, hM, 0, hM)
        if not self._first:
            self._layout.addSpacing(5*hM)
        self._layout.addWidget(qLabel)
        self._sections[identifier] = qLabel
        self._first = False
        return

    def addRow(self, label: str, widget: QWidget, helpText: str = "", unit: str | None = None,
               button: QWidget | None = None, editable: str | None = None) -> None:
        """Add a label and a widget as a new row of the form."""
        row = QHBoxLayout()
        row.setSpacing(CONFIG.pxInt(4))

        mPx = CONFIG.pxInt(12)
        qLabel = QLabel(label, self)
        qLabel.setIndent(mPx)
        qLabel.setBuddy(widget)

        if helpText:
            qHelp = NColourLabel(str(helpText), self._helpCol, scale=self._fontScale, wrap=True)
            qHelp.setIndent(mPx)
            labelBox = QVBoxLayout()
            labelBox.addWidget(qLabel)
            labelBox.addWidget(qHelp)
            labelBox.setSpacing(0)
            labelBox.addStretch(1)
            row.addLayout(labelBox)
            if editable:
                self._editable[editable] = qHelp
        else:
            row.addWidget(qLabel)

        row.addSpacing(mPx)
        row.addWidget(widget)

        if isinstance(unit, str):
            row.addWidget(QLabel(unit, self))
        elif isinstance(button, QAbstractButton):
            row.addWidget(button)

        self._layout.addLayout(row)
        self._index[label.strip()] = widget
        self._first = False

        return

    def finalise(self) -> None:
        """Finalise the layout when the form is built."""
        self._layout.addSpacing(CONFIG.pxInt(20))
        self._layout.addStretch(1)
        return

# END Class NScrollableForm


class NConfigLayout(QGridLayout):

    def __init__(self) -> None:
        super().__init__()

        self._nextRow = 0
        self._helpCol = QColor(0, 0, 0)
        self._fontScale = FONT_SCALE
        self._itemMap = {}

        wSp = CONFIG.pxInt(8)
        self.setHorizontalSpacing(wSp)
        self.setVerticalSpacing(wSp)
        self.setColumnStretch(0, 1)

        return

    ##
    #  Getters and Setters
    ##

    def setHelpTextStyle(self, color: QColor, scale: float = FONT_SCALE) -> None:
        """Set the text color for the help text."""
        self._helpCol = color if isinstance(color, QColor) else QColor(*color)
        self._fontScale = scale
        return

    def setHelpText(self, row: int, text: str) -> None:
        """Set the text for the help label."""
        if row in self._itemMap:
            qHelp = self._itemMap[row][1]
            if isinstance(qHelp, NColourLabel):
                qHelp.setText(text)
        return

    ##
    #  Class Methods
    ##

    def addGroupLabel(self, label: str) -> None:
        """Add a text label to separate groups of settings."""
        hM = CONFIG.pxInt(4)
        qLabel = QLabel("<b>%s</b>" % label)
        qLabel.setContentsMargins(0, hM, 0, hM)
        self.addWidget(qLabel, self._nextRow, 0, 1, 2, Qt.AlignLeft)
        self.setRowStretch(self._nextRow, 0)
        self.setRowStretch(self._nextRow + 1, 1)
        self._nextRow += 1
        return

    def addRow(self, label: str, widget: QWidget, helpText: str | None = None,
               unit: str | None = None, button: QWidget | None = None) -> int:
        """Add a label and a widget as a new row of the grid."""
        wSp = CONFIG.pxInt(8)
        qLabel = QLabel(label)
        qLabel.setIndent(wSp)
        qLabel.setBuddy(widget)

        qHelp = None
        if helpText is not None:
            qHelp = NColourLabel(str(helpText), self._helpCol, scale=self._fontScale, wrap=True)
            qHelp.setIndent(wSp)
            labelBox = QVBoxLayout()
            labelBox.addWidget(qLabel)
            labelBox.addWidget(qHelp)
            labelBox.setSpacing(0)
            labelBox.addStretch(1)
            self.addLayout(labelBox, self._nextRow, 0, 1, 1, LEFT_TOP)
        else:
            self.addWidget(qLabel, self._nextRow, 0, 1, 1, LEFT_TOP)

        if isinstance(unit, str):
            controlBox = QHBoxLayout()
            controlBox.addWidget(widget, 0, Qt.AlignVCenter)
            controlBox.addWidget(QLabel(unit), 0, Qt.AlignVCenter)
            controlBox.setSpacing(wSp)
            self.addLayout(controlBox, self._nextRow, 1, 1, 1, RIGHT_TOP)

        elif isinstance(button, QAbstractButton):
            controlBox = QHBoxLayout()
            controlBox.addWidget(widget, 0, Qt.AlignVCenter)
            controlBox.addWidget(button, 0, Qt.AlignVCenter)
            controlBox.setSpacing(wSp)
            self.addLayout(controlBox, self._nextRow, 1, 1, 1, RIGHT_TOP)

        else:
            if isinstance(widget, QLineEdit):
                qLayout = QHBoxLayout()
                qLayout.addWidget(widget)
                self.addLayout(qLayout, self._nextRow, 1, 1, 1, RIGHT_TOP)
            else:
                self.addWidget(widget, self._nextRow, 1, 1, 1, RIGHT_TOP)

        self.setRowStretch(self._nextRow, 0)
        self.setRowStretch(self._nextRow+1, 1)

        self._itemMap[self._nextRow] = (qLabel, qHelp, widget)
        self._nextRow += 1

        return self._nextRow - 1

# END Class NConfigLayout


class NSimpleLayout(QGridLayout):
    """Similar to NConfigLayout, but only has a label + widget two
    column layout.
    """

    def __init__(self, stretcColumn: int = 0) -> None:
        super().__init__()
        self._nextRow = 0

        wSp = CONFIG.pxInt(8)
        self.setHorizontalSpacing(wSp)
        self.setVerticalSpacing(wSp)
        self.setColumnStretch(stretcColumn, 1)

        return

    ##
    #  Methods
    ##

    def addGroupLabel(self, label: str) -> None:
        """Add a text label to separate groups of settings."""
        hM = CONFIG.pxInt(4)
        qLabel = QLabel("<b>%s</b>" % label)
        qLabel.setContentsMargins(0, hM, 0, hM)
        self.addWidget(qLabel, self._nextRow, 0, 1, 2, Qt.AlignLeft)
        self.setRowStretch(self._nextRow, 0)
        self.setRowStretch(self._nextRow + 1, 1)
        self._nextRow += 1
        return

    def addRow(self, label: str, widget: QWidget) -> None:
        """Add a label and a widget as a new row of the grid."""
        wSp = CONFIG.pxInt(8)
        qLabel = QLabel(label)
        qLabel.setIndent(wSp)
        self.addWidget(qLabel, self._nextRow, 0, 1, 1, LEFT_TOP)

        if isinstance(widget, QLineEdit):
            qLayout = QHBoxLayout()
            qLayout.addWidget(widget)
            self.addLayout(qLayout, self._nextRow, 1, 1, 1, RIGHT_TOP)
        else:
            self.addWidget(widget, self._nextRow, 1, 1, 1, RIGHT_TOP)

        qLabel.setBuddy(widget)

        self.setRowStretch(self._nextRow, 0)
        self.setRowStretch(self._nextRow+1, 1)
        self._nextRow += 1

        return

# END Class NSimpleLayout


class NColourLabel(QLabel):
    """Extension: A Coloured Label

    A custom widget that draws a label in a specific colour, and
    optionally at a specific size, and word wrapped.
    """

    def __init__(self, text: str, color: QColor, parent: QWidget | None = None,
                 scale: float = FONT_SCALE, wrap: bool = False) -> None:
        super().__init__(text, parent=parent)

        lblCol = self.palette()
        lblCol.setColor(QPalette.WindowText, color)
        self.setPalette(lblCol)

        lblFont = self.font()
        lblFont.setPointSizeF(scale*lblFont.pointSizeF())
        self.setFont(lblFont)

        if wrap:
            self.setWordWrap(True)
            self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        return

# END Class NColourLabel

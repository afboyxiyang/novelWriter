"""
novelWriter – GUI Doc Merge Dialog
==================================

File History:
Created:   2020-01-23 [0.4.3]  GuiDocMerge
Rewritten: 2022-10-06 [2.0rc1] GuiDocMerge

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

import logging

from PyQt5.QtGui import QCloseEvent
from PyQt5.QtCore import Qt, QSize, pyqtSlot
from PyQt5.QtWidgets import (
    QAbstractItemView, QDialog, QDialogButtonBox, QGridLayout, QLabel,
    QListWidget, QListWidgetItem, QVBoxLayout, QWidget
)

from novelwriter import CONFIG, SHARED
from novelwriter.extensions.switch import NSwitch
from novelwriter.extensions.configlayout import NColourLabel

logger = logging.getLogger(__name__)


class GuiDocMerge(QDialog):

    D_HANDLE = Qt.ItemDataRole.UserRole

    def __init__(self, parent: QWidget, sHandle: str, itemList: list[str]) -> None:
        super().__init__(parent=parent)

        logger.debug("Create: GuiDocMerge")
        self.setObjectName("GuiDocMerge")
        self.setWindowTitle(self.tr("Merge Documents"))

        self._data = {}

        self.headLabel = QLabel("<b>{0}</b>".format(self.tr("Documents to Merge")))
        self.helpLabel = NColourLabel(
            self.tr("Drag and drop items to change the order, or uncheck to exclude."),
            SHARED.theme.helpText, parent=self, wrap=True
        )

        iPx = SHARED.theme.baseIconSize
        hSp = CONFIG.pxInt(12)
        vSp = CONFIG.pxInt(8)
        bSp = CONFIG.pxInt(12)

        self.listBox = QListWidget()
        self.listBox.setIconSize(QSize(iPx, iPx))
        self.listBox.setMinimumWidth(CONFIG.pxInt(400))
        self.listBox.setMinimumHeight(CONFIG.pxInt(180))
        self.listBox.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.listBox.setSelectionMode(QAbstractItemView.SingleSelection)
        self.listBox.setDragDropMode(QAbstractItemView.InternalMove)

        # Merge Options
        self.trashLabel = QLabel(self.tr("Move merged items to Trash"))
        self.trashSwitch = NSwitch(width=2*iPx, height=iPx)

        self.optBox = QGridLayout()
        self.optBox.addWidget(self.trashLabel,  0, 0)
        self.optBox.addWidget(self.trashSwitch, 0, 1)
        self.optBox.setHorizontalSpacing(hSp)
        self.optBox.setColumnStretch(2, 1)

        # Buttons
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.resetButton = self.buttonBox.addButton(QDialogButtonBox.Reset)
        self.resetButton.clicked.connect(self._resetList)

        # Assemble
        self.outerBox = QVBoxLayout()
        self.outerBox.setSpacing(0)
        self.outerBox.addWidget(self.headLabel)
        self.outerBox.addWidget(self.helpLabel)
        self.outerBox.addSpacing(vSp)
        self.outerBox.addWidget(self.listBox)
        self.outerBox.addSpacing(vSp)
        self.outerBox.addLayout(self.optBox)
        self.outerBox.addSpacing(bSp)
        self.outerBox.addWidget(self.buttonBox)
        self.setLayout(self.outerBox)

        # Load Content
        self._loadContent(sHandle, itemList)

        logger.debug("Ready: GuiDocMerge")

        return

    def __del__(self) -> None:  # pragma: no cover
        logger.debug("Delete: GuiDocMerge")
        return

    def getData(self) -> dict:
        """Return the user's choices."""
        finalItems = []
        for i in range(self.listBox.count()):
            item = self.listBox.item(i)
            if item is not None and item.checkState() == Qt.Checked:
                finalItems.append(item.data(self.D_HANDLE))

        self._data["moveToTrash"] = self.trashSwitch.isChecked()
        self._data["finalItems"] = finalItems

        return self._data

    ##
    #  Events
    ##

    def closeEvent(self, event: QCloseEvent) -> None:
        """Capture the close event and perform cleanup."""
        event.accept()
        self.deleteLater()
        return

    ##
    #  Private Slots
    ##

    @pyqtSlot()
    def _resetList(self) -> None:
        """Reset the content of the list box to its original state."""
        logger.debug("Resetting list box content")
        sHandle = self._data.get("sHandle", None)
        itemList = self._data.get("origItems", [])
        self._loadContent(sHandle, itemList)
        return

    ##
    #  Internal Functions
    ##

    def _loadContent(self, sHandle: str, itemList: list[str]) -> None:
        """Load content from a given list of items."""
        self._data = {}
        self._data["sHandle"] = sHandle
        self._data["origItems"] = itemList

        self.listBox.clear()
        for tHandle in itemList:
            nwItem = SHARED.project.tree[tHandle]
            if nwItem is None or not nwItem.isFileType():
                continue

            itemIcon = SHARED.theme.getItemIcon(
                nwItem.itemType, nwItem.itemClass, nwItem.itemLayout, nwItem.mainHeading
            )

            newItem = QListWidgetItem()
            newItem.setIcon(itemIcon)
            newItem.setText(nwItem.itemName)
            newItem.setData(self.D_HANDLE, tHandle)
            newItem.setCheckState(Qt.Checked)

            self.listBox.addItem(newItem)

        return

# END Class GuiDocMerge

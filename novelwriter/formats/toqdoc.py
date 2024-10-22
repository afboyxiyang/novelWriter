"""
novelWriter – QTextDocument Converter
=====================================

File History:
Created: 2024-05-21 [2.5b1] ToQTextDocument

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

from pathlib import Path

from PyQt5.QtCore import QMarginsF, QSizeF
from PyQt5.QtGui import (
    QFont, QFontMetricsF, QPageSize, QTextBlockFormat, QTextCharFormat,
    QTextCursor, QTextDocument
)
from PyQt5.QtPrintSupport import QPrinter

from novelwriter.constants import nwHeadFmt, nwStyles, nwUnicode
from novelwriter.core.project import NWProject
from novelwriter.formats.shared import BlockFmt, BlockTyp, T_Formats, TextFmt
from novelwriter.formats.tokenizer import Tokenizer
from novelwriter.types import (
    QtAlignAbsolute, QtAlignCenter, QtAlignJustify, QtAlignLeft, QtAlignRight,
    QtPageBreakAfter, QtPageBreakBefore, QtTransparent, QtVAlignNormal,
    QtVAlignSub, QtVAlignSuper
)

logger = logging.getLogger(__name__)

T_TextStyle = tuple[QTextBlockFormat, QTextCharFormat]


def newBlock(cursor: QTextCursor, bFmt: QTextBlockFormat) -> None:
    if cursor.position() > 0:
        cursor.insertBlock(bFmt)
    else:
        cursor.setBlockFormat(bFmt)


class ToQTextDocument(Tokenizer):
    """Core: QTextDocument Writer

    Extend the Tokenizer class to generate a QTextDocument output. This
    is intended for usage in the document viewer and build tool preview.
    """

    def __init__(self, project: NWProject) -> None:
        super().__init__(project)
        self._document = QTextDocument()
        self._document.setUndoRedoEnabled(False)
        self._document.setDocumentMargin(0)

        self._styles: dict[int, T_TextStyle] = {}
        self._usedNotes: dict[str, int] = {}

        self._init = False
        self._bold = QFont.Weight.Bold
        self._normal = QFont.Weight.Normal

        self._pageSize = QPageSize(QPageSize.PageSizeId.A4)
        self._pageMargins = QMarginsF(20.0, 20.0, 20.0, 20.0)

        return

    ##
    #  Properties
    ##

    @property
    def document(self) -> QTextDocument:
        """Return the document."""
        return self._document

    ##
    #  Setters
    ##

    def setPageLayout(
        self, width: float, height: float, top: float, bottom: float, left: float, right: float
    ) -> None:
        """Set the document page size and margins in millimetres."""
        self._pageSize = QPageSize(QSizeF(width, height), QPageSize.Unit.Millimeter)
        self._pageMargins = QMarginsF(left, top, right, bottom)
        return

    ##
    #  Class Methods
    ##

    def initDocument(self) -> None:
        """Initialise all computed values of the document."""
        super().initDocument()

        self._document.setUndoRedoEnabled(False)
        self._document.blockSignals(True)
        self._document.clear()
        self._document.setDefaultFont(self._textFont)

        qMetric = QFontMetricsF(self._textFont)
        mPx = qMetric.ascent()  # 1 em in pixels
        fPt = self._textFont.pointSizeF()

        # Scaled Sizes
        # ============

        self._mHead = {
            BlockTyp.TITLE: (mPx * self._marginTitle[0], mPx * self._marginTitle[1]),
            BlockTyp.HEAD1: (mPx * self._marginHead1[0], mPx * self._marginHead1[1]),
            BlockTyp.HEAD2: (mPx * self._marginHead2[0], mPx * self._marginHead2[1]),
            BlockTyp.HEAD3: (mPx * self._marginHead3[0], mPx * self._marginHead3[1]),
            BlockTyp.HEAD4: (mPx * self._marginHead4[0], mPx * self._marginHead4[1]),
        }

        hScale = self._scaleHeads
        self._sHead = {
            BlockTyp.TITLE: (nwStyles.H_SIZES.get(0, 1.0) * fPt) if hScale else fPt,
            BlockTyp.HEAD1: (nwStyles.H_SIZES.get(1, 1.0) * fPt) if hScale else fPt,
            BlockTyp.HEAD2: (nwStyles.H_SIZES.get(2, 1.0) * fPt) if hScale else fPt,
            BlockTyp.HEAD3: (nwStyles.H_SIZES.get(3, 1.0) * fPt) if hScale else fPt,
            BlockTyp.HEAD4: (nwStyles.H_SIZES.get(4, 1.0) * fPt) if hScale else fPt,
        }

        self._mText = (mPx * self._marginText[0], mPx * self._marginText[1])
        self._mMeta = (mPx * self._marginMeta[0], mPx * self._marginMeta[1])
        self._mSep  = (mPx * self._marginSep[0], mPx * self._marginSep[1])

        self._mIndent = mPx * 2.0
        self._tIndent = mPx * self._firstWidth

        # Text Formats
        # ============

        self._blockFmt = QTextBlockFormat()
        self._blockFmt.setTopMargin(self._mText[0])
        self._blockFmt.setBottomMargin(self._mText[1])
        self._blockFmt.setAlignment(QtAlignAbsolute)
        self._blockFmt.setLineHeight(
            100*self._lineHeight, QTextBlockFormat.LineHeightTypes.ProportionalHeight
        )

        self._charFmt = QTextCharFormat()
        self._charFmt.setBackground(QtTransparent)
        self._charFmt.setForeground(self._theme.text)

        self._init = True

        return

    def doConvert(self) -> None:
        """Write text tokens into the document."""
        if not self._init:
            return

        self._document.blockSignals(True)
        cursor = QTextCursor(self._document)
        cursor.movePosition(QTextCursor.MoveOperation.End)

        for tType, nHead, tText, tFormat, tStyle in self._blocks:

            # Styles
            bFmt = QTextBlockFormat(self._blockFmt)
            if tType in (BlockTyp.COMMENT, BlockTyp.KEYWORD):
                bFmt.setTopMargin(self._mMeta[0])
                bFmt.setBottomMargin(self._mMeta[1])
            elif tType == BlockTyp.SEP:
                bFmt.setTopMargin(self._mSep[0])
                bFmt.setBottomMargin(self._mSep[1])

            if tStyle is not None:
                if tStyle & BlockFmt.LEFT:
                    bFmt.setAlignment(QtAlignLeft)
                elif tStyle & BlockFmt.RIGHT:
                    bFmt.setAlignment(QtAlignRight)
                elif tStyle & BlockFmt.CENTRE:
                    bFmt.setAlignment(QtAlignCenter)
                elif tStyle & BlockFmt.JUSTIFY:
                    bFmt.setAlignment(QtAlignJustify)

                if tStyle & BlockFmt.PBB:
                    bFmt.setPageBreakPolicy(QtPageBreakBefore)
                if tStyle & BlockFmt.PBA:
                    bFmt.setPageBreakPolicy(QtPageBreakAfter)

                if tStyle & BlockFmt.Z_BTMMRG:
                    bFmt.setBottomMargin(0.0)
                if tStyle & BlockFmt.Z_TOPMRG:
                    bFmt.setTopMargin(0.0)

                if tStyle & BlockFmt.IND_L:
                    bFmt.setLeftMargin(self._mIndent)
                if tStyle & BlockFmt.IND_R:
                    bFmt.setRightMargin(self._mIndent)
                if tStyle & BlockFmt.IND_T:
                    bFmt.setTextIndent(self._tIndent)

            if tType in (BlockTyp.TEXT, BlockTyp.COMMENT, BlockTyp.KEYWORD):
                newBlock(cursor, bFmt)
                self._insertFragments(tText, tFormat, cursor, self._charFmt)

            elif tType in self.L_HEADINGS:
                bFmt, cFmt = self._genHeadStyle(tType, nHead, bFmt)
                newBlock(cursor, bFmt)
                cursor.insertText(tText.replace(nwHeadFmt.BR, "\n"), cFmt)

            elif tType == BlockTyp.SEP:
                newBlock(cursor, bFmt)
                cursor.insertText(tText, self._charFmt)

            elif tType == BlockTyp.SKIP:
                newBlock(cursor, bFmt)
                cursor.insertText(nwUnicode.U_NBSP, self._charFmt)

        self._document.blockSignals(False)

        return

    def saveDocument(self, path: Path) -> None:
        """Save the document to a PDF file."""
        m = self._pageMargins

        printer = QPrinter(QPrinter.PrinterMode.PrinterResolution)
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setPageSize(self._pageSize)
        printer.setPageMargins(m.left(), m.top(), m.right(), m.bottom(), QPrinter.Unit.Millimeter)
        printer.setOutputFileName(str(path))

        self._document.setPageSize(self._pageSize.size(QPageSize.Unit.Point))
        self._document.print(printer)

        return

    def appendFootnotes(self) -> None:
        """Append the footnotes in the buffer."""
        if self._usedNotes:
            self._document.blockSignals(True)

            cursor = QTextCursor(self._document)
            cursor.movePosition(QTextCursor.MoveOperation.End)

            bFmt, cFmt = self._genHeadStyle(BlockTyp.HEAD4, -1, self._blockFmt)
            newBlock(cursor, bFmt)
            cursor.insertText(self._localLookup("Footnotes"), cFmt)

            for key, index in self._usedNotes.items():
                if content := self._footnotes.get(key):
                    cFmt = QTextCharFormat(self._charFmt)
                    cFmt.setForeground(self._theme.code)
                    cFmt.setAnchor(True)
                    cFmt.setAnchorNames([f"footnote_{index}"])
                    newBlock(cursor, self._blockFmt)
                    cursor.insertText(f"{index}. ", cFmt)
                    self._insertFragments(*content, cursor, self._charFmt)

            self._document.blockSignals(False)

        return

    ##
    #  Internal Functions
    ##

    def _insertFragments(
        self, text: str, tFmt: T_Formats, cursor: QTextCursor, dFmt: QTextCharFormat
    ) -> None:
        """Apply formatting tags to text."""
        cFmt = QTextCharFormat(dFmt)
        start = 0
        temp = text.replace("\n", nwUnicode.U_LSEP)
        for pos, fmt, data in tFmt:

            # Insert buffer with previous format
            cursor.insertText(temp[start:pos], cFmt)

            # Construct next format
            if fmt == TextFmt.B_B:
                cFmt.setFontWeight(self._bold)
            elif fmt == TextFmt.B_E:
                cFmt.setFontWeight(self._normal)
            elif fmt == TextFmt.I_B:
                cFmt.setFontItalic(True)
            elif fmt == TextFmt.I_E:
                cFmt.setFontItalic(False)
            elif fmt == TextFmt.D_B:
                cFmt.setFontStrikeOut(True)
            elif fmt == TextFmt.D_E:
                cFmt.setFontStrikeOut(False)
            elif fmt == TextFmt.U_B:
                cFmt.setFontUnderline(True)
            elif fmt == TextFmt.U_E:
                cFmt.setFontUnderline(False)
            elif fmt == TextFmt.M_B:
                cFmt.setBackground(self._theme.highlight)
            elif fmt == TextFmt.M_E:
                cFmt.setBackground(QtTransparent)
            elif fmt == TextFmt.SUP_B:
                cFmt.setVerticalAlignment(QtVAlignSuper)
            elif fmt == TextFmt.SUP_E:
                cFmt.setVerticalAlignment(QtVAlignNormal)
            elif fmt == TextFmt.SUB_B:
                cFmt.setVerticalAlignment(QtVAlignSub)
            elif fmt == TextFmt.SUB_E:
                cFmt.setVerticalAlignment(QtVAlignNormal)
            elif fmt == TextFmt.COL_B:
                if color := self._classes.get(data):
                    cFmt.setForeground(color)
            elif fmt == TextFmt.COL_E:
                cFmt.setForeground(self._theme.text)
            elif fmt == TextFmt.ANM_B:
                cFmt.setAnchor(True)
                cFmt.setAnchorNames([data])
            elif fmt == TextFmt.ANM_E:
                cFmt.setAnchor(False)
            elif fmt == TextFmt.HRF_B:
                cFmt.setFontUnderline(True)
                cFmt.setAnchor(True)
                cFmt.setAnchorHref(data)
            elif fmt == TextFmt.HRF_E:
                cFmt.setFontUnderline(False)
                cFmt.setAnchor(False)
            elif fmt == TextFmt.FNOTE:
                xFmt = QTextCharFormat(self._charFmt)
                xFmt.setForeground(self._theme.code)
                xFmt.setVerticalAlignment(QtVAlignSuper)
                if data in self._footnotes:
                    index = len(self._usedNotes) + 1
                    self._usedNotes[data] = index
                    xFmt.setAnchor(True)
                    xFmt.setAnchorHref(f"#footnote_{index}")
                    xFmt.setFontUnderline(True)
                    cursor.insertText(f"[{index}]", xFmt)
                else:
                    cursor.insertText("[ERR]", cFmt)

            # Move pos for next pass
            start = pos

        # Insert whatever is left in the buffer
        cursor.insertText(temp[start:], cFmt)

        return

    def _genHeadStyle(self, hType: BlockTyp, nHead: int, rFmt: QTextBlockFormat) -> T_TextStyle:
        """Generate a heading style set."""
        mTop, mBottom = self._mHead.get(hType, (0.0, 0.0))

        bFmt = QTextBlockFormat(rFmt)
        bFmt.setTopMargin(mTop)
        bFmt.setBottomMargin(mBottom)

        self._cTitle = QTextCharFormat(self._charFmt)
        self._cTitle.setFontWeight(self._bold if self._boldHeads else self._normal)

        hCol = self._colorHeads and hType != BlockTyp.TITLE
        cFmt = QTextCharFormat(self._charFmt)
        cFmt.setForeground(self._theme.head if hCol else self._theme.text)
        cFmt.setFontWeight(self._bold if self._boldHeads else self._normal)
        cFmt.setFontPointSize(self._sHead.get(hType, 1.0))
        if nHead >= 0:
            cFmt.setAnchorNames([f"{self._handle}:T{nHead:04d}"])
            cFmt.setAnchor(True)

        return bFmt, cFmt
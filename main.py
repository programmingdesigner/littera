"""
Littera note-taking app

Author: programmingdesigner
Website: github.com/programmingdesigner/littera
Last modified: august 2022
"""

import os
import itertools
import webbrowser

import wx
import wx.richtext as rt
import wx.html as html
import wx.adv
import markdown
from xhtml2pdf import pisa


wildcard = "Markdown (*.md)|*.md|" \
           "Text (*.txt)|*.txt|"   \
           "All (*.*)|*.*"         \



class findDlg(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent, title="Find", size=(300, 140))

        self.parent = parent

        panel = wx.Panel(self)

        vBox = wx.BoxSizer(wx.VERTICAL)
        hBox = wx.BoxSizer(wx.HORIZONTAL)
        btnBox = wx.BoxSizer(wx.HORIZONTAL)

        label = wx.StaticText(panel, label="Search for")
        self.textEntry = wx.TextCtrl(panel)

        hBox.Add(label, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=10)
        hBox.Add(self.textEntry, proportion=1)

        vBox.Add(hBox, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=16)
        vBox.Add((-1, 10))

        findBtn = wx.Button(panel, wx.ID_OK, label="Find", size=(75, 25))
        findNextBtn = wx.Button(
            panel, label="Find Next", size=(75, 25))
        findBtn.SetDefault()

        btnBox.Add(findBtn)
        btnBox.Add(findNextBtn, flag=wx.LEFT | wx.BOTTOM)

        vBox.Add(btnBox, flag=wx.ALIGN_RIGHT | wx.RIGHT, border=16)

        panel.SetSizer(vBox)

        self.Bind(wx.EVT_CLOSE, self.onClose)
        findBtn.Bind(wx.EVT_BUTTON, self.parent.onFind)
        findNextBtn.Bind(wx.EVT_BUTTON, self.onFindNext)

        self.Centre()

    def onClose(self, e):
        self.Destroy()
        self.parent.findDlg = None
        self.parent.statusbar.SetStatusText("")
        print("findDlg destroyed")

    def onFindNext(self, e):
        self.parent.textCtrl.SetInsertionPoint(next(self.parent.iterators))
        self.parent.textCtrl.ScrollIntoView(
            self.parent.textCtrl.GetInsertionPoint(), 13)
        self.parent.textCtrl.Update()
        self.parent.textCtrl.Refresh()
        self.parent.textCtrl.SetFocus()


class textEditor(wx.Frame):
    def __init__(self, filename="untitled"):
        super(textEditor, self).__init__(
            None, size=(960, 540))

        # Properties
        self.dirname = "."
        self.filename = filename
        self.modify = False

        self.pos = 0
        self.size = 0

        self.appname = "Littera"
        self.appversion = "v1.0b"

        icon = wx.Icon("favicon.ico", type=wx.BITMAP_TYPE_ICO)

        self.findDlg = None

        # Fonts
        wx.Font.AddPrivateFont("fonts/sans/NotoSans-Regular.ttf")
        font = wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL,
                       underline=False, faceName="Noto Sans", encoding=wx.FONTENCODING_DEFAULT)
        labels = wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL,
                         underline=False, faceName="Noto Sans", encoding=wx.FONTENCODING_DEFAULT)

        # Ui
        self.splitter = wx.SplitterWindow(
            self, style=wx.SP_NO_XP_THEME)
        self.splitter.SetBackgroundColour("#F4F9F9")
        lPanel = wx.Panel(self.splitter)
        rPanel = wx.Panel(self.splitter)

        lPanel.SetBackgroundColour("#F4F9F9")
        rPanel.SetBackgroundColour("#FFFFFF")

        self.splitter.SplitVertically(lPanel, rPanel, -1)
        self.splitter.SetMinimumPaneSize(460)

        lSizer = wx.BoxSizer(wx.VERTICAL)
        rSizer = wx.BoxSizer(wx.VERTICAL)

        # Ui -- lPanel
        lLabel = wx.StaticText(lPanel, label="Text Editor")
        lLabel.SetFont(labels)
        lLabel.SetForegroundColour("#9598A1")

        # Ui -- textCtrl
        self.textCtrl = rt.RichTextCtrl(lPanel, -1, style=rt.RE_MULTILINE | wx.TE_RICH2 |
                                        wx.TE_NO_VSCROLL | wx.TE_WORDWRAP | wx.TE_AUTO_URL | wx.TE_PROCESS_TAB | wx.BORDER_NONE)
        self.textCtrl.SetEditable(True)

        textAttr = rt.RichTextAttr()
        textAttr.SetFont(font)
        textAttr.SetTextColour("#3C4245")
        textAttr.SetLineSpacing(12)
        textAttr.SetLeftIndent(60)
        textAttr.SetRightIndent(80)

        self.textCtrl.SetBasicStyle(textAttr)
        self.textCtrl.SetBackgroundColour("#F4F9F9")

        self.mdExtensions = ['tables', 'sane_lists', 'fenced_code', 'smarty']

        # Ui -- rPanel
        rLabel = wx.StaticText(rPanel, label="HTML Preview")
        rLabel.SetFont(labels)
        rLabel.SetForegroundColour("#9598A1")

        # Ui -- htmlPrev
        self.htmlPrev = html.HtmlWindow(rPanel)
        self.htmlPrev.SetStandardFonts(16, "Noto Sans")

        # Ui -- Config
        lSizer.Add(lLabel, flag=wx.LEFT | wx.TOP, border=24)
        lSizer.Add((-1, 20))
        lSizer.Add(self.textCtrl, proportion=1, flag=wx.EXPAND)
        lPanel.SetSizer(lSizer)

        rSizer.Add(rLabel, flag=wx.LEFT | wx.TOP, border=24)
        rSizer.Add((-1, 20))
        rSizer.Add(self.htmlPrev, proportion=1, flag=wx.EXPAND)
        rPanel.SetSizer(rSizer)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.splitter, 1, flag=wx.EXPAND)
        self.SetSizer(sizer)

        self.SetIcon(icon)
        self.Centre()

        # Functions
        self.setTitle()
        self.createMenu()
        self.setStatusBar()
        self.bindEvents()
        self.assignHotkeys()

    def setTitle(self):
        super(textEditor, self).SetTitle(self.filename + " - " + self.appname)

    def createMenu(self):
        menuBar = wx.MenuBar()

        fileMenu = wx.Menu()
        editMenu = wx.Menu()
        viewMenu = wx.Menu()
        helpMenu = wx.Menu()

        self.fileMenu_new = fileMenu.Append(
            wx.ID_NEW, "&New\tCtrl+N")
        self.fileMenu_open = fileMenu.Append(
            wx.ID_OPEN, "&Open\tCtrl+O")
        fileMenu.AppendSeparator()
        self.fileMenu_save = fileMenu.Append(
            wx.ID_SAVE, "&Save\tCtrl+S")
        self.fileMenu_saveAs = fileMenu.Append(
            wx.ID_SAVEAS, "&Save As\tCtrl+Shift+S")
        fileMenu.AppendSeparator()
        self.fileMenu_exportPdf = fileMenu.Append(
            wx.ID_ANY, "&Export as PDF (.pdf)\tCtrl+Shift+E")
        fileMenu.AppendSeparator()
        self.fileMenu_quit = fileMenu.Append(
            wx.ID_EXIT, "&Quit\tCtrl+Q")

        self.editMenu_find = editMenu.Append(
            wx.ID_FIND, "&Find\tCtrl+F")

        self.viewMenu_prev = viewMenu.AppendCheckItem(
            wx.ID_ANY, "Show HTML Preview")
        viewMenu.Check(self.viewMenu_prev.GetId(), True)

        self.helpMenu_reference = helpMenu.Append(
            wx.ID_ANY, "&Reference\tCtrl+R")
        self.helpMenu_credits = helpMenu.Append(
            wx.ID_ANY, "&Credits")
        self.helpMenu_license = helpMenu.Append(
            wx.ID_ANY, "&License")
        helpMenu.AppendSeparator()
        self.helpMenu_website = helpMenu.Append(
            wx.ID_ANY, "&Website")
        self.helpMenu_about = helpMenu.Append(
            wx.ID_ABOUT, "&About")

        menuBar.Append(fileMenu, "File")
        menuBar.Append(editMenu, "Edit")
        menuBar.Append(viewMenu, "View")
        menuBar.Append(helpMenu, "Help")

        self.SetMenuBar(menuBar)

    def setStatusBar(self):
        self.statusbar = self.CreateStatusBar(style=wx.STB_DEFAULT_STYLE)

        self.statusbar.SetFieldsCount(number=3, widths=[-1, 140, 30])
        self.statusbar.SetStatusText(self.appversion, 2)

        self.SetStatusBar(self.statusbar)

    def bindEvents(self):
        self.Bind(wx.EVT_MENU, self.onNew, self.fileMenu_new)
        self.Bind(wx.EVT_MENU, self.onOpen, self.fileMenu_open)
        self.Bind(wx.EVT_MENU, self.onSave, self.fileMenu_save)
        self.Bind(wx.EVT_MENU, self.onSaveAs, self.fileMenu_saveAs)
        self.Bind(wx.EVT_MENU, self.onQuit, self.fileMenu_quit)
        self.Bind(wx.EVT_MENU, self.onExport, self.fileMenu_exportPdf)

        self.Bind(wx.EVT_MENU, self.togglePrev, self.viewMenu_prev)

        self.Bind(wx.EVT_MENU, self.onCredits, self.helpMenu_credits)
        self.Bind(wx.EVT_MENU, self.onReference, self.helpMenu_reference)
        self.Bind(wx.EVT_MENU, self.onWebsite, self.helpMenu_website)
        self.Bind(wx.EVT_MENU, self.onLicense, self.helpMenu_license)
        self.Bind(wx.EVT_MENU, self.onAbout, self.helpMenu_about)

        self.Bind(wx.EVT_FIND, self.onFindDlg)
        self.Bind(wx.EVT_MENU, self.onFindDlg, self.editMenu_find)

        self.htmlPrev.Bind(html.EVT_HTML_LINK_CLICKED, self.onURL)

        self.textCtrl.Bind(wx.EVT_LEFT_UP, self.onCursorPos)

    def assignHotkeys(self):
        accelEntries = [wx.AcceleratorEntry() for i in range(7)]

        accelEntries[0].Set(wx.ACCEL_CTRL, ord('N'), wx.ID_NEW)
        accelEntries[1].Set(wx.ACCEL_CTRL, ord('O'), wx.ID_OPEN)
        accelEntries[2].Set(wx.ACCEL_CTRL, ord('S'), wx.ID_SAVE)
        accelEntries[3].Set(wx.ACCEL_CTRL | wx.ACCEL_SHIFT,
                            ord('S'), wx.ID_SAVEAS)
        accelEntries[4].Set(wx.ACCEL_CTRL, ord('Q'), wx.ID_EXIT)
        accelEntries[5].Set(wx.ACCEL_CTRL, ord('F'), wx.ID_FIND)
        accelEntries[6].Set(wx.ACCEL_CTRL, ord(
            'R'), self.helpMenu_reference.GetId())

        accelTable = wx.AcceleratorTable(accelEntries)
        self.SetAcceleratorTable(accelTable)

    def md2html(self):
        md = self.textCtrl.GetValue()
        html = markdown.markdown(
            md, extensions=self.mdExtensions)
        self.htmlPrev.SetPage(html)

    def onNew(self, e):
        self.textCtrl.SetValue("")
        self.textCtrl.SetEditable(True)
        print("read-only mode deactivated")
        self.filename = "untitled"
        self.setTitle()

    def onFileDlg(self):
        return dict(message="Choose a file", defaultDir=self.dirname)

    def askFilename(self, **fileDlgOptions):
        dlg = wx.FileDialog(self, **fileDlgOptions)

        if dlg.ShowModal() == wx.ID_OK:
            userFilename = True
            self.filename = dlg.GetFilename()
            self.dirname = dlg.GetDirectory()

            self.setTitle()
        else:
            userFilename = False
        dlg.Destroy()
        print("fileDlg destroyed")

        return userFilename

    def onOpen(self, e):
        if self.askFilename(style=wx.FD_OPEN, **self.onFileDlg(), wildcard=wildcard):
            file = open(os.path.join(self.dirname, self.filename),
                        "r", encoding="utf-8")
            self.textCtrl.SetValue(file.read())
            file.close()
            self.md2html()
            print("read-only mode deactivated")
            self.textCtrl.SetEditable(True)

    def onSave(self, e):
        with open(os.path.join(self.dirname, self.filename), "w", encoding="utf-8") as file:
            file.write(self.textCtrl.GetValue())
            self.md2html()

    def onSaveAs(self, e):
        if self.askFilename(defaultFile=self.filename, style=wx.FD_SAVE, **self.onFileDlg(), wildcard=wildcard):
            self.onSave(e)

    def onExport(self, e):
        if self.askFilename(defaultDir=self.dirname, defaultFile=self.filename, style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT, wildcard="PDF (*.pdf)|*.pdf"):

            content = markdown.markdown(
                self.textCtrl.GetValue(), extensions=self.mdExtensions)
            output = self.filename

            with open("options/pdf_options.html", "r", encoding="utf-8") as options:
                source = options.read() + content + \
                    "<pdf:nextpage/><div><pdf:toc/></div><div><pdf:spacer height=""20pt""><hr><p>Made with <span style=""font-weight:bold;"">Littera Text Editor</span></p></div>" + "</body></html>"

            def html2pdf(source, output):
                with open(os.path.join(self.dirname, output), "w+b") as file:
                    pdf = pisa.CreatePDF(
                        source, dest=file)
                    return pdf.err
            self.statusbar.SetStatusText("Exporting file...")

            html2pdf(source, output)
        self.statusbar.SetStatusText("")

    def onFindDlg(self, e):
        if self.findDlg == None:
            print("findDlg opened")

            self.findDlg = findDlg(self)
            self.findDlg.Show()

    def onFind(self, e):
        word = self.findDlg.textEntry.GetValue().lower()
        content = self.textCtrl.GetValue().lower()

        index = 0

        if word in content:
            count = content.count(word)
            results = []

            while index < len(content):
                index = content.find(word, index)

                if index == -1:
                    break
                index += 1
                results.append((index-1))

            self.iterators = itertools.cycle(results)

            i = 0

            for i in results:
                self.textCtrl.SetInsertionPoint(next(self.iterators))
                self.textCtrl.ScrollIntoView(
                    self.textCtrl.GetInsertionPoint(), 13)
                self.textCtrl.Update()
                self.textCtrl.Refresh()
                self.textCtrl.SetFocus()
            self.statusbar.SetStatusText(
                "Found " + str(count) + " instance(s) of " + word)
            print(word, "found", str(count), "times at", str(results))
        else:
            print(word, "not found")

    def togglePrev(self, e):
        if self.viewMenu_prev.IsChecked():
            self.splitter.SetMinimumPaneSize(460)
            self.statusbar.SetStatusText("HTML Preview shown")
            print("HTML Preview shown")
        else:
            self.splitter.SetMinimumPaneSize(1)
            self.statusbar.SetStatusText("HTML Preview hidden")
            print("HTML Preview hidden")

    def onURL(self, e):
        link = e.GetLinkInfo()
        webbrowser.open_new_tab(link.GetHref())
        return

    def onReadOnly(self, filename):
        with open(filename, "r", encoding="utf-8") as file:
            self.textCtrl.SetValue(file.read())
            self.md2html()
            self.textCtrl.SetEditable(False)
            print("read-only mode activated")

    def onCredits(self, e):
        self.onReadOnly("docs/credits.md")

    def onReference(self, e):
        self.onReadOnly("docs/reference.md")

    def onWebsite(self, e):
        webbrowser.open_new_tab("https://programmingdesigner.github.io/")

    def onLicense(self, e):
        webbrowser.open_new_tab(
            "https://github.com/programmingdesigner/littera/blob/main/LICENSE")

    def onAbout(self, e):
        info = wx.adv.AboutDialogInfo()
        info.SetName(self.appname)
        info.SetVersion(self.appversion)
        with open("docs/description.txt", "r", encoding="utf-8") as file:
            info.SetDescription(file.read())
        info.SetCopyright("(c) 2022 programmingdesigner")
        wx.adv.AboutBox(info)

    def onCursorPos(self, e):
        text = "Cursor Position: " + str(self.textCtrl.GetInsertionPoint())
        self.statusbar.SetStatusText(text, 1)
        e.Skip()

    def onQuit(self, e):
        self.Destroy()


def main():
    app = wx.App()
    frame = textEditor()
    frame.Show()
    app.MainLoop()
    pisa.showLogging()


if __name__ == "__main__":
    main()

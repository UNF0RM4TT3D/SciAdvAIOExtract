import sys, os, tomllib, threading
from PySide6.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox, QDialog
from PySide6.QtCore import Slot, QTimer

from ui_mainwindow import Ui_MainWindow
from ui_progressdialog import Ui_ProgressDialog

from extractor import Extractor

class Profiles:
    def __init__(self):
        self.__getprof()
        self.__valid = False
        pass

    def __getprof(self): #gets available profile configs and populates _profile variable with them
        self._profiles = []
        ignore = []
        fsdir = os.path.join(os.path.dirname(sys.argv[0]), "profiles")
        self._files = os.listdir(fsdir)
        for dex, i in enumerate(self._files):
            try:
                with open(os.path.join(fsdir, i), "rb") as p:
                    self._profiles.append(tomllib.load(p))
            except:
                print("Could not open " + i, file=sys.stderr)
                ignore.append(dex)
        for i in ignore:
            self._files.pop(i)

    def __keyerror(self, key, index):
        print("Ignoring '" + str(self._files[index]) + "', not a valid profile. Key '" + key + "' not found in profile", file=sys.stderr)

    def list(self): #lists names of profiles
        names = []
        ignore = []
        for dex, i in enumerate(self._profiles):
            if "name" in i.keys():
                names.append(i["name"])
            else:
                self.__keyerror("name", dex)
                ignore.append(dex)
        for i in ignore:
            self._profiles.pop(i)

        if names == []:
            return ["No valid profiles found in profile folder"]
        return names

    def select(self, index = 0): #selects and TODO: validates the profile
        print("Selecting" + str(self._profiles[index]), file=sys.stderr)
        self.__selected = self._profiles[index]

    @property
    def name(self):
        return self.__selected["name"]

    @property
    def description(self):
        if "description" in self.__selected.keys():
            return self.__selected["description"]
        return ""

    @property
    def filetype(self):
        return self.__selected["filetype"]

    @property
    def pfiletype(self): #TODO: determine if needed
        if "pfiletype" in self.__selected.keys():
            return self.__selected["pfiletype"]
        return ""

    @property
    def path(self):
        if sys.platform == 'win32':
            return os.path.join("C:\\Program Files (x86)\\Steam\\steamapps\\common", self.__selected["path"])
        if sys.platform == 'linux':
            return os.path.join(os.path.expanduser("~/.steam/root/steamapps/common"), self.__selected["path"])
        print("WARNING: Running on an unsupported platform" + sys.platform + "premade paths are not supported and some extractors might not work", file=sys.stderr)
        return ""

    @property
    def sprites(self):
        if "sprites" in self.__selected.keys():
            return self.__selected["sprites"]
        return []

    @property
    def processor(self):
        if "processor" in self.__selected.keys():
            return self.__selected["processor"]
        return ""

    @property
    def mkey(self):
        if "mkey" in self.__selected.keys():
            return self.__selected["mkey"]
        return ""
    @mkey.setter
    def mkey(self, key):
        self.__selected["mkey"] = key

class ProgressDialog(QDialog):
    def __init__(self, parent, ext):
        self.ext = ext
        super().__init__(parent)
        self._ui = Ui_ProgressDialog()
        self._ui.setupUi(self)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(500)
        self._ui.label.setText(self.ext.status)
        self._ui.progressBar.setMaximum(self.ext.total)
        self._ui.progressBar.setValue(self.ext.progress)
        self._cursor = self._ui.textEdit.textCursor()

    @Slot()
    def update(self): #called frequently to update the log window and progress bar
        #with self.ext.lock:
        log = self.ext.out.getvalue() # somehow make stringIO thread safe??
        self._ui.label.setText(self.ext.status)
        self._ui.progressBar.setMaximum(self.ext.total)
        self._ui.progressBar.setValue(self.ext.progress)
        if self._ui.textEdit.toPlainText() != log: #only update when text has changed to reduce flicker
            self._ui.textEdit.setPlainText(log)
            self._ui.textEdit.moveCursor(self._cursor.MoveOperation.End)
            self._ui.textEdit.ensureCursorVisible()
        if self.ext.done:
            self._ui.progressBar.setValue(self.ext.progress)#race condition
            self._ui.textEdit.setMarkdown(self._ui.textEdit.toMarkdown() + "\n# FINISHED!\nYou can now close this window\n")
            self._ui.textEdit.moveCursor(self._cursor.MoveOperation.End) #Move log to end
            self._ui.textEdit.ensureCursorVisible()
            self.timer.stop()

    @Slot()
    def on_pushButton_clicked(self):
        #with self.ext.lock:
        self.ext.stop()

    def closeEvent(self, event):
        if self.ext.stopped:
            super(ProgressDialog, self).closeEvent(event)
        else:
            event.ignore()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._profile = Profiles()
        self._ui = Ui_MainWindow()
        self._ui.setupUi(self)
        self.__populateui()

    def __populateui(self):
        profs = self._profile.list()
        for dex, i in enumerate(profs):
            self._ui.profileComboBox.insertItem(dex, i)

    @Slot()
    def on_fileListWidget_itemSelectionChanged(self):
        items = self._ui.fileListWidget.selectedItems()
        if any([True for x in items if x.text() in self._profile.sprites]): # check for having a selected a sprite file
            self._ui.convertCheckBox.setDisabled(False)
            return
        self._ui.convertCheckBox.setDisabled(True)
        self._ui.convertCheckBox.setChecked(False)
        self._ui.keepConvCheckBox.setDisabled(True)
        self._ui.keepConvCheckBox.setChecked(False)

    @Slot(bool)
    def on_convertCheckBox_toggled(self, checked):
        if checked:
            self._ui.keepConvCheckBox.setDisabled(False)
        else:
            self._ui.keepConvCheckBox.setDisabled(True)
            self._ui.keepConvCheckBox.setChecked(False)

    @Slot(int)
    def on_profileComboBox_currentIndexChanged(self, index:int):
        self._profile.select(index)
        self._ui.pathLineEdit.setText(self._profile.path)
        self._ui.descText.setMarkdown(self._profile.description)
        self._ui.descText.update()

    @Slot(str)
    def on_pathLineEdit_textChanged(self, path:str):
        files = []
        if os.path.isdir(path):
            files = os.listdir(path) #get available files for extraction
            files = [f for f in files if f.endswith(self._profile.filetype)]
        self._ui.fileListWidget.clear()
        for dex, i in enumerate(files):
            self._ui.fileListWidget.insertItem(dex, i)

    @Slot()
    def on_browseButton_2_clicked(self):
        path = QFileDialog.getExistingDirectory(self)
        self._ui.pathLineEdit_2.setText(path)

    @Slot()
    def on_browseButton_clicked(self):
        path = QFileDialog.getExistingDirectory(self)
        self._ui.pathLineEdit.setText(path)

    @Slot()
    def on_extractButton_clicked(self):
        items = self._ui.fileListWidget.selectedItems()
        if len(items) == 0:
            QMessageBox.critical(self, "Invalid configuration", "There are no files selected for processing, not proceeding")
            return
        if not os.path.isdir(self._ui.pathLineEdit_2.text()):
            QMessageBox.critical(self, "Invalid configuration", "The selected extract location doesn't exist")
            return
        """if not self._profile.valid:
            QMessageBox.critical(self, "Invalid configuration", "The selected profile doesn't seem to be valid.\nCheck console output for more details.")
            return """
        ext = Extractor(self._profile)
        if ext.dl != "":
            answer = QMessageBox.question(self, "Additional components needed", f"Due to licensing issues, an additional download is necessary to extract this filetype.\n{ext.dldet}\nDo you wish to continue?")
            if answer == QMessageBox.StandardButton.No:
                return
            ext.download()
        if self._ui.convertCheckBox.isChecked():
            ext.convert = True
            if self._ui.keepConvCheckBox.isChecked():
                ext.delconv = False
        if len(os.listdir(self._ui.pathLineEdit_2.text())) != 0:
            QMessageBox.critical(self, "Invalid configuration", "The selected extract location isn't empty")
            return
        t = threading.Thread(target=ext.extract, args=(self._ui.pathLineEdit.text(), [x.text() for x in items], self._ui.pathLineEdit_2.text()))
        t.start()
        progress = ProgressDialog(self, ext)
        progress.update()
        progress.exec()
        t.join()
        del progress

if __name__ == '__main__':
    os.chdir(os.path.dirname(sys.argv[0]))
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

from fbs_runtime.application_context.PySide2 import ApplicationContext
import sys
from PySide2.QtWidgets import *
from PySide2.QtCore import QDir, Qt, QProcess, QThread, QRunnable, Slot, Signal, QObject, QThreadPool
import concurrent.futures
from firstpass import *
from multiprocessing import Process, Queue
from contextlib import redirect_stdout
import io

class MyEmitter(QObject):
    # setting up custom signal
    done = Signal(tuple)


class StringEmitter(QObject):
    done = Signal(str)


class MyWorker(QRunnable):
    def __init__(self, infile, hmp):
        super(MyWorker, self).__init__()
        self.infile = infile
        self.hmp = hmp
        self.emitter = MyEmitter()
        self.wkbk = None
        self.xl_file = None

    def run(self):
        f = io.StringIO()
        with redirect_stdout(f):
            self.wkbk, self.xl_file = AddDescriptions(self.infile, self.hmp)
        s = f.getvalue()
        msg = (str(s), self.wkbk, self.xl_file)
        self.emitter.done.emit(msg)


class WriterWorker(QRunnable):
    def __init__(self, outfile, wkbk, xl_file):
        super(WriterWorker, self).__init__()
        self.outfile = outfile
        self.wkbk = wkbk
        self.xl_file = xl_file
        self.emitter = StringEmitter()

    def run(self):
        f = io.StringIO()
        with redirect_stdout(f):
            print(self.outfile)
            write_out(self.outfile, self.wkbk, self.xl_file)
        s = f.getvalue()
        self.emitter.done.emit(str(s))


class DialogApp(QWidget):
    def __init__(self):
        super().__init__()
        self.resize(800, 400)

        self.input_filename = ''
        self.xl_file = None
        self.wkbk = None
        self.out_filename = ''

        self.pool = QThreadPool()

        ####
        ## Widget defs
        self.choose_spreadsheet_button = QPushButton('Choose Metabolite Excel File (.xlsx)')
        self.choose_spreadsheet_button.clicked.connect(self.get_excel)

        self.input_hmp = QLineEdit()
        self.input_hmp.setText('HMP ID')
        #self.input_hmp.setAlignment(Qt.AlignTop)

        self.text = QLabel("Exact name of HMP ID column (include spaces):")
        #self.text.setAlignment(Qt.AlignTop)

        self.outputstream = QTextEdit()
        self.outputstream.setReadOnly(True)

        self.begin_processing = QPushButton("Begin Processing")
        self.begin_processing.clicked.connect(self.process_wkbk)
        #self.begin_processing.clicked.connect(self.launch_threadpool)

        self.save_dialog = QFileDialog(self)
        self.save_dialog.setFileMode(QFileDialog.AnyFile)

        self.save_output = QPushButton("Save Processed File")
        self.save_output.clicked.connect(self.save_output_dialog)

        ####
        ## Add widgets 
        layout = QGridLayout()

        layout.addWidget(self.choose_spreadsheet_button, 0, 0, 1, -1, Qt.AlignTop)

        layout.addWidget(self.text, 1, 0, 1, -1)
        layout.addWidget(self.input_hmp, 2, 1, 1, -1)

        layout.addWidget(self.outputstream, 3, 0, 1, -1)
        layout.addWidget(self.begin_processing, 4, 0)
        layout.addWidget(self.save_output, 4, 1)
        self.setLayout(layout)


    @Slot(tuple)
    def on_worker_done(self, message):
        # modify the UI
        print("updating UI")
        self.wkbk = message[1]
        self.xl_file = message[2]
        self.outputstream.append(f"{message[0]}")    


    @Slot(str)
    def on_writer_done(self, message):
        self.outputstream.append(f"{message}")            


    def get_excel(self):
        self.input_filename, _ = QFileDialog.getOpenFileName(self, 
                                                   'Open Excel File (.xlsx)',
                                                   r"<Default dir>",
                                                   "Excel 2010-2013 Format (*.xlsx)")


    def process_wkbk(self):
        self.outputstream.append("Starting...\nPlease wait until additional output is printed.")
        worker = MyWorker(self.input_filename, self.input_hmp.text())
        worker.emitter.done.connect(self.on_worker_done)
        self.pool.start(worker)


    def save_output_dialog(self):
        self.out_filename, _ = self.save_dialog.getSaveFileName(self,
                                                            'Save As',
                                                            r"<Default dir>",
                                                            "Excel 2010-2013 Format (*.xlsx)")
        worker = WriterWorker(self.out_filename, self.wkbk, self.xl_file)
        worker.emitter.done.connect(self.on_writer_done)
        self.pool.start(worker)
        

if __name__ == '__main__':
    appctxt = ApplicationContext()

    demo = DialogApp()
    demo.show()

    exit_code = appctxt.app.exec_()
    sys.exit(exit_code)
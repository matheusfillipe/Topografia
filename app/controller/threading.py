#####TODO make threading work
from qgis._core import QgsApplication
from qgis._core import QgsTask


def nongui(fun):
#    """Decorator running the function in non-gui thread while
#    processing the gui events."""
#    from multiprocessing.pool import ThreadPool
#    from PyQt5.QtWidgets import QApplication
#
#    def wrap(*args, **kwargs):
#        pool = ThreadPool(processes=1)
#        asynchronous = pool.apply_async(fun, args, kwargs)
#        while not asynchronous.ready():
#            asynchronous.wait(0.01)
#            QApplication.processEvents()
#        return asynchronous.get()
#
    return fun#wrap



#def nongui(func):
#    """Decorator running the function in non-gui thread while
#    processing the gui events."""
#    from qgis._core import QgsTask, QgsApplication, QgsMessageLog, Qgis
#    MESSAGE_CATEGORY = 'Topografia'
#
#    def workdone(exception, result=None):
#        if exception is None:
#            if result is None:
#                QgsMessageLog.logMessage('Completed with no exception and no result '\
#                                '(probably manually canceled by the user)',
#                                MESSAGE_CATEGORY, Qgis.Warning)
#            return result
#
#        else:
#            QgsMessageLog.logMessage("Exception: {}".format(exception),
#                                 MESSAGE_CATEGORY, Qgis.Critical)
#            raise exception
#
#    def wrap(*args, **kwargs):
#        task=QgsTask.fromFunction(u'Topografia Task', wrap,
#                             onfinished=workdone)
#        QgsApplication.taskManager().addTask(task)
#
#    return wrap
#
from PyQt5.QtWidgets import *
import time

class TestTask(QgsTask):
    """Here we subclass QgsTask"""
    def __init__(self, desc,iface):
        QgsTask.__init__(self, desc)
        self.iface=iface

    def run(self):
        """This function is where you do the 'heavy lifting' or implement
        the task which you want to run in a background thread. This function
        must return True or False and should only interact with the main thread
        via signals"""
        for i in range (21):
            time.sleep(0.5)
            val = i * 5
            #report progress which can be received by the main thread
            self.setProgress(val)
            #check to see if the task has been cancelled
            if self.isCanceled():
                return False
        return True

    def finished(self, result):
        """This function is called automatically when the task is completed and is
        called from the main thread so it is safe to interact with the GUI etc here"""
        if result is False:
            self.iface.messageBar().pushMessage('Task was cancelled')
        else:
            self.iface.messageBar().pushMessage('Task Complete')

class My_Dialog(QDialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.resize(500, 350)
        self.lbl_info = QLabel('Info:', self)
        self.lbl_info.move(100, 50)
        self.edit_info = QLineEdit(self)
        self.edit_info.move(200, 50)
        lbl_prog = QLabel('Task Progress: ', self)
        lbl_prog.move(100, 210)
        self.prog = QProgressBar(self)
        self.prog.resize(200, 30)
        self.prog.move(200, 200)
        btn_OK = QPushButton('OK', self)
        btn_OK.move(300, 300)
        btn_OK.clicked.connect(self.newTask)
        btn_close = QPushButton('Close',self)
        btn_close.move(400, 300)
        btn_close.clicked.connect(self.close_win)
        btn_cancel = QPushButton('Cancel Task', self)
        btn_cancel.move(50, 300)
        btn_cancel.clicked.connect(self.cancelTask)


    def newTask(self):
        """Create a task and add it to the Task Manager"""
        self.task = TestTask('Custom Task')
        #connect to signals from the background threads to perform gui operations
        #such as updating the progress bar
        self.task.begun.connect(lambda: self.edit_info.setText('Working...'))
        self.task.progressChanged.connect(lambda: self.prog.setValue(self.task.progress()))
        self.task.taskCompleted.connect(lambda: self.edit_info.setText('Task Complete'))
        self.task.taskTerminated.connect(self.TaskCancelled)
        QgsApplication.taskManager().addTask(self.task)

    def cancelTask(self):
        self.task.cancel()

    def TaskCancelled(self):
        self.prog.setValue(0)
        self.edit_info.setText('Task Cancelled')

    def close_win(self):
        My_Dialog.close(self)



from __future__ import print_function
import os
import sys
import Queue
import plac_core
from Tkinter import Tk
from ScrolledText import ScrolledText
from plac_ext import Monitor, TerminatedProcess


class TkMonitor(Monitor):
    """
    An interface over a dictionary {taskno: scrolledtext widget}, with
    methods add_listener, del_listener, notify_listener and start/stop.
    """
    def __init__(self, name, queue=None):
        Monitor.__init__(self, name, queue)
        self.widgets = {}

    @plac_core.annotations(taskno=('task number', 'positional', None, int))
    def add_listener(self, taskno):
        "There is a ScrolledText for each task"
        st = ScrolledText(self.root, height=5)
        st.insert('end', 'Output of task %d\n' % taskno)
        st.pack()
        self.widgets[taskno] = st

    @plac_core.annotations(taskno=('task number', 'positional', None, int))
    def del_listener(self, taskno):
        del self.widgets[taskno]

    @plac_core.annotations(taskno=('task number', 'positional', None, int))
    def notify_listener(self, taskno, msg):
        w = self.widgets[taskno]
        w.insert('end', msg + '\n')
        w.update()

    def start(self):
        'Start the mainloop'
        self.root = Tk()
        self.root.title(self.name)
        self.root.wm_protocol("WM_DELETE_WINDOW", self.stop)
        self.root.after(0, self.read_queue)
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            print('Process %d killed by CTRL-C' % os.getpid(), file=sys.stderr)
        except TerminatedProcess:
            pass

    def stop(self):
        self.root.quit()

    def read_queue(self):
        try:
            cmd_args = self.queue.get_nowait()
        except Queue.Empty:
            pass
        else:
            getattr(self, cmd_args[0])(*cmd_args[1:])
        self.root.after(100, self.read_queue)

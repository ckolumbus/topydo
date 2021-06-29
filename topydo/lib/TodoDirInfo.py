import os, re
from datetime import datetime
from topydo.lib import TodoFile

class TodoDirInfo:
    def __init__(self, dir, todofile_fmt="todo_{}.txt"):
        self.date_regex_str = r"(?P<date>[0-9]{4}-(1[0-2]|0[1-9])-[0-3][0-9])"
        self.date_fmt   = r"%Y-%m-%d"
        self.todofile_fmt = todofile_fmt

        self.todofile_re = re.compile(("^"+self.todofile_fmt+"$").format(self.date_regex_str))
        self.dir = dir

    def get_filename_for_date(self, p_date):
        return p_date.strftime(self.todofile_fmt.format(self.date_fmt))

    def get_fullpath_for_date(self, p_date):
        return os.path.join(self.dir, self.get_filename_for_date(p_date))

    def write_todo_file(self, p_date, p_todolist):
        if p_todolist.dirty:
            f = self.get_fullpath_for_date(p_date)
            tf = TodoFile.TodoFile(f)
            tf.write(p_todolist.print_todos())
            p_todolist.dirty = False

    def __iter__(self):
        files = [f for f in os.listdir(self.dir) if self.todofile_re.match(f)]
        for f in files:
            res = self.todofile_re.match(f)
            d = datetime.strptime(res['date'], self.date_fmt).date()
            yield (d, os.path.join(self.dir, f))


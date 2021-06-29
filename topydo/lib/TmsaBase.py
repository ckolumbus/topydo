
from collections import defaultdict, namedtuple
from itertools import chain, repeat, count
from datetime import  date
from topydo.lib import TodoDirInfo, TodoList, TodoFile, Todo


TmsaListIterItem = namedtuple('TmsaListIterItem',['date','number','todo'])  
class TmsaTodo(Todo.Todo):
    def __init__(self, p_date:date, p_number, p_str):
        super().__init__(p_str)
        self.filedate = p_date
        self.number = p_number

    def file_date(self):
        return self.filedate

    def file_number(self):
        return self.number


class TmsaTodoList:
    def __init__(self, dirinfo: TodoDirInfo.TodoDirInfo):
        self.dirinfo = dirinfo
        self._todolist_dict = defaultdict(lambda : TodoList.TodoList([]))
        self.bump_date_fmt = "%Y-%m-%d"
        for (d,f) in self.dirinfo:
            self.add_from_file(d, f)

        self.todolist = TodoList.TodoList([])
        self.todolist.add_todos([TmsaTodo(i.date, i.number, i.todo.src) for i in self])

    def add_from_file(self, p_filedate, p_filename):
        tf = TodoFile.TodoFile(p_filename)
        todolist = TodoList.TodoList(tf.read())
        self._todolist_dict[p_filedate] = todolist

    def add(self, p_filedate, p_todolist):
        self._todolist_dict[p_filedate] = p_todolist

    def get(self, p_filedate):
        return self._todolist_dict[p_filedate]

    def write(self, p_date=None):
        if p_date and self._todolist_dict.has_key(p_date):
            self.dirinfo.write_todo_file(p_date, self._todolist_dict[p_date])
        else:
            for d in self._todolist_dict:
                self.dirinfo.write_todo_file(d, self._todolist_dict[d])

    def bumptodos(self, p_todolist, p_to_date = None, p_move=False):
        if not p_to_date:
            p_to_date = date.today()

        for tmsatodo in p_todolist:
            d = tmsatodo.file_date()

            # ignore moves to same date
            if p_to_date == d:
                continue

            id = tmsatodo.file_number()
            t = self._todolist_dict[d].todo(id)

            self._todolist_dict[p_to_date].add(t.src)

            # TODO: refactor this code together with duplicate code in `bump` below
            if p_move:
                # on 'move' just delete old entry
                self._todolist_dict[d].delete(t)
            else:
                # else document 'bump' date
                self._todolist_dict[d].append(t, "bumped:{}".format(p_to_date.strftime(self.bump_date_fmt)))
                self._todolist_dict[d].set_todo_completed(t, p_completion_date=d)

    def bump(self, p_to_date = None, p_from_date = None, p_reference_date = date.today(), p_move=False):
        if not p_to_date:
            p_to_date = date.today()
   
        if p_from_date:
            date_list = [ p_from_date ]
        else:
            date_list = [d for d in self._todolist_dict if d <  p_reference_date ]

        # remove target date from list
        try:
            date_list.remove(p_to_date)
        except:
            pass

        for d in date_list :
            active_todos = [todo for todo in self._todolist_dict[d].todos() if todo.is_active()]

            # first update target todolist
            for t in active_todos:
                self._todolist_dict[p_to_date].add(t.src)

            # the delete items, otherwise we are iterating over a changing list
            for t in active_todos:
                if p_move:
                    # on 'move' just delete old entry
                    self._todolist_dict[d].delete(t)
                else:
                    # else document 'bump' date
                    self._todolist_dict[d].append(t, "bumped:{}".format(p_to_date.strftime(self.bump_date_fmt)))
                    self._todolist_dict[d].set_todo_completed(t, p_completion_date=d)

    def __len__(self):
        c = [t.count() for t in self._todo_dictlist.values() ]
        return sum(c)

    def __iter__(self):
        return chain.from_iterable(
            #zip(repeat(l), self._todolist_dict[l], count(1)) for l in sorted(self._todolist_dict.keys()) 
            map(TmsaListIterItem, repeat(l), count(1), self._todolist_dict[l] ) for l in sorted(self._todolist_dict.keys()) 
        )

if __name__ == "__main__":

    todo_dir_info = TodoDirInfo.TodoDirInfo(r"C:\02-py\venvs\uttt-ckol\src\utt-gui\dev", "t{}.txt")
    [print (d,f) for (d,f) in todo_dir_info]
    todo_list_info = TmsaTodoList(todo_dir_info)
    #[ print(l[0], l[2], l[1].src) for l in todo_list_info if l[1].is_active()]
    [ print(l.date, l.number, l.todo.src) for l in todo_list_info if l.todo.is_active() ]

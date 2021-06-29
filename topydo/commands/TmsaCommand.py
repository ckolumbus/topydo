# Topydo - A todo.txt client written in Python.
# Copyright (C) 2014 - 2015 Bram Schoenmakers <bram@topydo.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from datetime import date,timedelta
from topydo.lib.Config import config
from topydo.lib.Utils import date_string_to_date

from topydo.lib.ExpressionCommand import ExpressionCommand
from topydo.lib.TodoListBase import InvalidTodoException
from topydo.lib.Command import InvalidCommandArgument
from topydo.lib.TodoList import TodoList
from topydo.lib.TmsaBase import TmsaTodoList
from topydo.lib.TodoDirInfo import TodoDirInfo

from topydo.commands.ListCommand import ListCommand

class TmsaCommand(ExpressionCommand):
    def __init__(self, p_args, p_todolist, #pragma: no branch
                 p_out=lambda a: None,
                 p_err=lambda a: None,
                 p_prompt=lambda a: None):
        super().__init__(
            p_args, p_todolist, p_out, p_err, p_prompt)

        try:
            self.subsubcommand = self.argument(0)
        except InvalidCommandArgument:
            self.subsubcommand = None

        self.format = config().list_format()
        self.sort_expression = config().sort_string()
        self.group_expression = config().group_string()

        # for 'multi' operations
        self.todos = []
        self.invalid_numbers = []

        tdi = TodoDirInfo(config().tododir(), config().todofile_fmt())
        self.tmsa_todo_list = TmsaTodoList(tdi)

    def _process_flags(self):
        pass

    def get_todos(self):
        """ Gets todo objects from supplied todo IDs. """
        if self.last_argument:
            numbers = self.args[:-1]
        else:
            numbers = self.args

        for number in numbers:
            try:
                todo = self.tmsa_todo_list.todolist.todo(number)
                if todo.is_active():
                    self.todos.append(todo)
                else:
                    self.invalid_numbers.append(number)
            except InvalidTodoException:
                self.invalid_numbers.append(number)

        return self.todos

    def _handle_passed(self):
        pass

    def _handle_bump(self):
        opts, args = self.getopt('t:m',p_skipargs=1)
        move_items = False
        to_date = None

        for opt, value in opts:
            if opt == '-m':
                move_items = True
            if opt == '-t':
                to_date = date_string_to_date(value)

        self.args = args
        todolist = self.get_todos()
        
        self.tmsa_todo_list.bumptodos(p_todolist=todolist, p_to_date=to_date, p_move=move_items)
        self.tmsa_todo_list.write(None)

    def _handle_bumpall(self):
        opts, args = self.getopt('t:f:m',p_skipargs=1)

        move_items = False
        from_date = None
        to_date = None

        for opt, value in opts:
            if opt == '-m':
                move_items = True
            if opt == '-t':
                to_date = date_string_to_date(value)
            if opt == '-f':
                from_date = date_string_to_date(value)

        self.tmsa_todo_list.bump(p_to_date=to_date, p_from_date=from_date, p_move=move_items)
        self.tmsa_todo_list.write(None)

    def _handle_backlog(self):
        """ Handles the backlog subsubcommand. """

        # TODO: refactor to use 'view' here (?)
        todolist =  TodoList([])
        todolist.add_todos([t for t in self.tmsa_todo_list.todolist if t.file_date() < date.today()])

        ls_cmd = ListCommand(self.args[1:], todolist , self.out, self.error, self.prompt)
        ls_cmd.execute()

    def _handle_upcoming(self):
        """ Handles the backlog subsubcommand. """

        # TODO: refactor to use 'view' here (?)
        todolist =  TodoList([])
        from_date = date.today()
        to_date = date.today() + timedelta(days=4)
        todolist.add_todos([t for t in self.tmsa_todo_list.todolist if t.file_date() > from_date and t.file_date() <= to_date])

        ls_cmd = ListCommand(self.args[1:], todolist , self.out, self.error, self.prompt)
        ls_cmd.execute()

    def _handle_ls(self):
        """ Handles the ls subsubcommand. """
        
        ls_cmd = ListCommand(self.args[1:], self.tmsa_todo_list.todolist, self.out, self.error, self.prompt)
        ls_cmd.execute()

    def execute(self):
        if not super().execute():
            return False

        self._process_flags()

        dispatch = {
            'ls':       self._handle_ls,
            'backlog':  self._handle_backlog,
            'upcoming': self._handle_upcoming,
            'bump':     self._handle_bump,
            'bumpall':  self._handle_bumpall,
        }

        if self.subsubcommand in dispatch:
            dispatch[self.subsubcommand]()
        else:
            self.error(self.usage())


    def usage(self):
        return """Synopsis:
  tmsa ls <any normal ls option>
  tmsa backlog 
  tmsa upcoming 
  tmsa bump [-m] [[to] <DATE>] <ID> [,<ID>, ...]
  tmsa bumpall [-m] [ -f <FROM_DATE>] [-t <TO_DATE>]
  """

    def help(self):
        return """\
Implements the "Time Management for System Admins" concept based on 
one todo file per day. 

* ls        : list all todos, takes same options as normal `ls` command
* backlog   : list all past todos
* upcoming  : list todos within the next few days
* bump      : bumps given list of active todo(s) to today or the given date
              the IDs are shown by the `ls` command
              with '-m' items are moved and no 'bumped' entry is created
* bumpall   : bumps all passed active todos to today or given date.
              with '-m' items are moved and no 'bumped' entry is created\
"""


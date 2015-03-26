# Topydo - A todo.txt client written in Python.
# Copyright (C) 2014 - 2015 Bram Schoenmakers <me@bramschoenmakers.nl>
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

from datetime import date, timedelta

from topydo.lib.Command import Command, InvalidCommandArgument
from topydo.lib.Config import config
from topydo.lib.PrettyPrinterFilter import PrettyPrinterNumbers
from topydo.lib.RelativeDate import relative_date_to_date
from topydo.lib.TodoListBase import InvalidTodoException
from topydo.lib.Utils import date_string_to_date

class PostponeCommand(Command):
    def __init__(self, p_args, p_todolist,
                 p_out=lambda a: None,
                 p_err=lambda a: None,
                 p_prompt=lambda a: None):
        super(PostponeCommand, self).__init__(
            p_args, p_todolist, p_out, p_err, p_prompt)

        self.move_start_date = False

    def _process_flags(self):
        opts, args = self.getopt('s')

        for opt, _ in opts:
            if opt == '-s':
                self.move_start_date = True

        self.args = args

    def execute(self):
        def _get_offset(p_todo):
            offset = p_todo.tag_value(
                config().tag_due(), date.today().isoformat())
            offset_date = date_string_to_date(offset)

            if offset_date < date.today():
                offset_date = date.today()

            return offset_date

        if not super(PostponeCommand, self).execute():
            return False

        self._process_flags()

        todos = []
        invalid_numbers = []

        for number in self.args[:-1]:
            try:
                todos.append(self.todolist.todo(number))
            except InvalidTodoException:
                invalid_numbers.append(number)

        if len(invalid_numbers) > 0 and len(todos) > 0:
            for number in invalid_numbers:
                self.error("Invalid todo number given: {}.".format(number))
        elif len(invalid_numbers) == 1 and len(todos) == 0:
            self.error("Invalid todo number given.")
        else:
            try:
                pattern = self.args[-1]
                self.printer.add_filter(PrettyPrinterNumbers(self.todolist))

                if len(todos) > 0:
                    for todo in todos:
                        offset = _get_offset(todo)
                        new_due = relative_date_to_date(pattern, offset)

                        if new_due:
                            if self.move_start_date and todo.has_tag(config().tag_start()):
                                length = todo.length()
                                new_start = new_due - timedelta(length)
                                todo.set_tag(config().tag_start(), new_start.isoformat())

                            todo.set_tag(config().tag_due(), new_due.isoformat())

                            self.todolist.set_dirty()
                            self.out(self.printer.print_todo(todo))
                        else:
                            self.error("Invalid date pattern given.")
                            break
                else:
                    self.error(self.usage())

            except (InvalidCommandArgument, IndexError):
                self.error(self.usage())

    def usage(self):
        return "Synopsis: postpone [-s] <NUMBER> [<NUMBER2> ...] <PATTERN>"

    def help(self):
        return """\
Postpone the todo item(s) with the given number(s) and the given pattern.

Postponing is done by adjusting the due date(s) of the todo(s), and if the -s flag is
given, the start date accordingly.

The pattern is a relative date, written in the format <COUNT><PERIOD> where
count is a number and <PERIOD> is either 'd', 'w', 'm' or 'y', which stands for
days, weeks, months and years respectively. Example: 'postpone 1 1w' postpones
todo number 1 for 1 week.
"""

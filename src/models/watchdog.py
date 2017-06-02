#!/usr/bin/python2
"""
Nautilus git pluging to show useful information under any
git directory

Author : Bilal Elmoussaoui (bil.elmoussaoui@gmail.com)
Website : https://github.com/bil-elmoussaoui/nautilus-git
Licence : GPL-3.0
nautilus-git is free software: you can redistribute it and/or
modify it under the terms of the GNU General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
nautilus-git is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
You should have received a copy of the GNU General Public License
along with nautilus-git. If not, see <http://www.gnu.org/licenses/>.
"""
from os import path, stat
from threading import Thread
from time import sleep

from gi.repository import GLib, GObject


class WatchDog(Thread, GObject.GObject):
    __gsignals__ = {
        'refresh': (GObject.SIGNAL_RUN_FIRST, None, ())
    }

    def __init__(self, git_path):
        Thread.__init__(self)
        GObject.GObject.__init__(self)
        self.daemon = True
        self.name = git_path
        self._to_watch = path.join(git_path, ".git", "HEAD")
        self.alive = path.exists(self._to_watch)
        self._modified_time = None
        self.start()

    def emit(self, *args):
        GLib.idle_add(GObject.GObject.emit, self, *args)

    def run(self):
        while self.alive:
            fstat = stat(self._to_watch)
            modified = fstat.st_mtime
            if modified and modified != self._modified_time:
                if self._modified_time is not None:
                    self.emit("refresh")
                self._modified_time = modified
            sleep(1)

    def kill(self):
        self.alive = False

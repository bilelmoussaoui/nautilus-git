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
from os import environ
from sys import path as sys_path
from gi import require_version
require_version("Gtk", "3.0")
from gi.repository import Gtk, Gio


sys_path.insert(0, environ["MODELS_DIR"])
sys_path.insert(0, environ["WIDGETS_DIR"])

from git import Git
from watchdog import WatchDog
from branch import BranchWidget
from compare import NautilusGitCompare


class NautilusLocation:
    """Location bar main widget."""

    def __init__(self, git_uri, window):
        self._window = window
        self._git = Git(git_uri)
        self._watchdog = WatchDog(self._git.dir)
        self._watchdog.connect("refresh", self._refresh)

        self._builder = Gtk.Builder()

        self._builder.add_from_resource('/com/nautilus/git/ui/location.ui')
        self._builder.connect_signals({
            "open_remote_clicked": self._open_remote_browser,
            "compare_commits_clicked": self._compare_commits,
            "popover_clicked": self._trigger_popover,
            "branch_clicked": self._update_branch
        })
        self._build_widgets()

    def _build_widgets(self):
        """Build needed widgets."""
        self._popover = self._builder.get_object("popover")
        repository = self._git.repository
        self._builder.get_object("branch").set_label(repository)
        remote_url = self._git.remote_url
        # Show the open remote button only if it's a url
        has_remote = False
        if remote_url.lower().startswith(("http://", "https://", "wwww")):
            self._builder.get_object("open_remote").show()
            has_remote = True

        files = self._git.get_modified()
        # Show the compare commits button only if there's any modification
        has_files = False
        if files:
            self._builder.get_object("compare_commits").show()
            has_files = True

        if not has_files and not has_remote:
            self._builder.get_object("more_button").set_sensitive(False)

        status = self._git.get_status()
        widgets = ["added", "modified", "removed"]
        for widget_name in widgets:
            files = status[widget_name]
            files.sort()
            widget = self._builder.get_object(widget_name)
            if files:
                widget.set_label(str(len(files)))
                box = self._builder.get_object(widget_name + "_content")
                for file_ in files:
                    file_label = Gtk.Label(file_)
                    file_label.set_halign(Gtk.Align.START)
                    file_label.show()
                    box.pack_start(file_label, False, False, 6)
            else:
                widget.hide()

    @property
    def main(self):
        return self._builder.get_object("main")

    def _update_branch(self, button):
        """Open the branch widget."""
        branch_ = BranchWidget(self._git, self._window)
        branch_.connect("refresh", self._refresh)

    def _refresh(self, event):
        action = self._window.lookup_action("reload")
        action.emit("activate", None)

    def _trigger_popover(self, popover):
        """Show/hide popover."""
        if popover.get_visible():
            popover.hide()
        else:
            popover.show()

    def _compare_commits(self, *args):
        """Compare commits widget creation."""
        NautilusGitCompare(self._git)
        self._popover.hide()

    def _open_remote_browser(self, *args):
        """Open the remote url on the default browser."""
        Gio.app_info_launch_default_for_uri(self._git.remote_url)
        self._popover.hide()

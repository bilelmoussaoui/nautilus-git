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
from os import environ, path

from gi import require_version
require_version("Gtk", "3.0")
from gi.repository import GObject, Gtk


class BranchWidget(GObject.GObject):
    __gsignals__ = {
        'refresh': (GObject.SIGNAL_RUN_FIRST, None, ())
    }

    def __init__(self, git_uri, window):
        GObject.GObject.__init__(self)
        self._git = git_uri

        self._builder = Gtk.Builder()
        self._builder.add_from_resource('/com/nautilus/git/ui/branch.ui')
        self._builder.connect_signals({
            "on_cancel": self._close_window,
            "on_apply": self._update_branch,
            "branch_changed": self._validate_branch_name
        })

        self._window = self._builder.get_object("window")
        self._window.set_transient_for(window)
        self._build_main_widget()
        self._window.show_all()

    def _build_main_widget(self):
        """Widgets builder."""
        headerbar = self._builder.get_object("headerbar")
        # Set the title of the headerbar
        headerbar.set_title(self._git.get_project_branch())

        branch_entry = self._builder.get_object("branch")

        # Get a list of availables branches
        branches = self._git.get_branch_list()
        # Get current branch
        current_branch = self._git.get_branch()

        # fill in the the branch entry
        branch_entry.set_entry_text_column(0)
        i = 0
        for branch in branches:
            if branch == current_branch:
                active_id = i
            branch_entry.append_text(branch)
            i += 1
        # Select the active one (current branch)
        branch_entry.set_active(active_id)
        branch_entry.grab_focus()

    def _validate_branch_name(self, entry):
        """Validate the entred branch name."""
        branch = entry.get_active_text().strip()
        apply_button = self._builder.get_object("applyButton")
        valid = True
        if branch == self._git.get_branch() or not branch:
            valid = False
        else:
            valid = self._git.check_branch_name(branch)

        apply_button.set_sensitive(valid)
        if valid:
            entry.get_style_context().remove_class("error")
        else:
            entry.get_style_context().add_class("error")

    def _update_branch(self, *args):
        """Update the branch."""
        branch = self._builder.get_object("branch").get_active_text().strip()
        self._git.update_branch(branch)
        self.emit("refresh")
        self._close_window()

    def _close_window(self, *args):
        """Close the window."""
        self._window.destroy()

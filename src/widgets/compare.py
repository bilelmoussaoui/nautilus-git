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
from gettext import gettext as _

from gi import require_version
require_version("Gtk", "3.0")
require_version("GtkSource", "3.0")
from gi.repository import Gio, GObject, Gtk, GtkSource


class NautilusGitCompare:
    """Nautilus diff window."""

    def __init__(self, git):
        GObject.type_register(GtkSource.View)
        self._git = git
        self._builder = Gtk.Builder()
        self._builder.add_from_resource('/com/nautilus/git/ui/compare.ui')
        self._builder.connect_signals({
            "file_changed": self._on_file_changed
        })

        self._window = self._builder.get_object("window")

        self._build_widgets()
        self._window.show_all()

    def _build_widgets(self):
        """Generate the headerbar."""
        header_bar = self._builder.get_object("headerbar")
        title = _("Comparing commits of {0}").format(
            self._git.get_project_name())

        header_bar.set_title(title)

        self._stats = self._builder.get_object("stats")

        # Build list of modified files
        self._source = self._builder.get_object("source")
        files = self._git.get_modified()
        files.sort()
        liststore = Gtk.ListStore(str)
        for filename in files:
            liststore.append([filename])

        combobox = self._builder.get_object("files")
        combobox.set_model(liststore)

        renderer_text = Gtk.CellRendererText()
        combobox.pack_start(renderer_text, True)
        combobox.add_attribute(renderer_text, "text", 0)

        combobox.set_active(0)
        # Load the buffer of the first file on the list
        self._set_buffer(files[0])

    def _on_file_changed(self, combobox):
        """File selection changed signal handler."""
        tree_iter = combobox.get_active_iter()
        if tree_iter:
            model = combobox.get_model()
            filename = model[tree_iter][0]
            self._set_buffer(filename)

    def _set_buffer(self, file_name):
        """Set the current content to the buffer of the file."""
        lang_manager = GtkSource.LanguageManager()
        language = lang_manager.guess_language(file_name, None)
        diff = self._git.get_diff(file_name)
        buff = GtkSource.Buffer()
        buff.set_highlight_syntax(True)
        buff.set_highlight_matching_brackets(True)
        buff.set_language(language)
        buff.props.text = diff
        self._source.set_buffer(buff)
        stat = self._git.get_stat(file_name)
        if stat:
            self._stats.set_text(stat)
            self._stats.show()

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
from os import environ
from sys import path as sys_path

from gi import require_version
require_version("Gtk", "3.0")
require_version("GtkSource", "3.0")
from gi.repository import Gio, GObject, Gtk, GtkSource, Gdk

sys_path.insert(0, environ["MODELS_DIR"])

from utils import get_diff


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
        title = _("Comparing commits of {}").format(self._git.project)

        header_bar.set_title(title)

        # Build list of modified files
        self._head = self._builder.get_object("head")
        self._origin = self._builder.get_object("origin")
        files = self._git.get_modified()
        files.sort()
        liststore = Gtk.ListStore(str)
        for filename in files:
            liststore.append([filename])

        combobox = self._builder.get_object("files")
        combobox.set_model(liststore)

        renderer_text = Gtk.CellRendererText()
        renderer_text.props.wrap_width = 30
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

        head, origin = self._git.diff(file_name)

        diff = get_diff(head, origin)

        head = self.get_buffer(head, language)
        origin = self.get_buffer(origin, language)

        current_line = 0
        for line in diff:
            code = line[2]
            if code == '- ':
                line_no = line[0]
                current_line = line_no
                self.add_tag('removed', head, line_no - 1, line_no)

            if code == '+ ':
                line_no = line[1]
                self.add_tag("added", origin, line_no - 1, line_no)


        self._head.set_buffer(head)
        self._origin.set_buffer(origin)

    @staticmethod
    def add_tag(tag, buffer, start_line, end_line):
        start = buffer.get_iter_at_line(start_line)
        end = buffer.get_iter_at_line(end_line)
        buffer.apply_tag_by_name(tag, start, end)

    @staticmethod
    def remove_tag(tag, buffer, start_line, end_line):
        start = buffer.get_iter_at_line(start_line)
        end = buffer.get_iter_at_line(end_line)
        buffer.remove_tag_by_name(tag, start, end)

    def get_buffer(self, content, language):
        buffer = GtkSource.Buffer()
        buffer.set_highlight_syntax(True)
        buffer.set_highlight_matching_brackets(True)
        buffer.set_language(language)
        buffer.props.text = "\n".join(content)

        added = Gtk.TextTag.new("added")
        added.props.background = self.hex_to_rgba("#D0FFA3")
        buffer.get_tag_table().add(added)

        changed = Gtk.TextTag.new("changed")
        changed.props.background = self.hex_to_rgba("#BDDDFF")
        buffer.get_tag_table().add(changed)

        removed = Gtk.TextTag.new("removed")
        removed.props.background = self.hex_to_rgba("#fE3000", 0.2)
        buffer.get_tag_table().add(removed)

        return buffer

    @staticmethod
    def hex_to_rgba(hex_color, opacity=0.4):
        color = Gdk.RGBA()
        color.parse(hex_color)
        color.alpha = opacity
        return color.to_string()

#!/usr/bin/python3
"""
Nautilus git pluging to show useful information under any
git directory

Author : Bilal Elmoussaoui (bil.elmoussaoui@gmail.com)
Version : 1.0
Website : https://github.com/bil-elmoussaoui/nautilus-git
Licence : GPL3
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
import gettext
from os import path
from urlparse import urlsplit
from subprocess import PIPE, Popen
from ConfigParser import ConfigParser, NoSectionError
from StringIO import StringIO
from gi import require_version
require_version("Gtk", "3.0")
require_version('Nautilus', '3.0')
require_version('GtkSource', '3.0')
from gi.repository import Gtk, Nautilus, GObject, Gio, GtkSource
_ = gettext.gettext
gettext.textdomain('nautilus-git')

GIT_FILES_STATUS = {
    "added" : {
        "icon" : "list-add-symbolic",
        "tooltip": _("Added files"),
        "properties": _("Added :")
    },
    "removed" : {
        "icon" : "list-remove-symbolic",
        "tooltip": _("Removed files"),
        "properties": _("Removed :")
    },
    "modified": {
        "icon" : "document-edit-symbolic",
        "tooltip": _("Modified files"),
        "properties": _("Modified :")
    }
}


def get_file_path(uri):
    """Return file path from an uri."""
    url = urlsplit(uri)
    if url.scheme.lower() == "file":
        return url.path
    return None

def is_git(folder_path):
    """Verify if the current folder_path is a git directory."""
    folder_path = get_file_path(folder_path)
    if folder_path:
        output = execute('git rev-parse --is-inside-work-tree', folder_path).lower()
        return output == "true"
    return None

def get_real_git_dir(directory):
    """Return the absolute path of the .git folder."""
    dirs = directory.split("/")
    current_path = ""
    for i in range(len(dirs) - 1, 0, -1):
        current_path = "/".join(dirs[0:i])
        git_folder = path.join(current_path, ".git")
        if path.exists(git_folder):
            return current_path
    return None

def execute(cmd, working_dir=None):
    """Execute a shell command."""
    if working_dir:
        command = Popen(cmd, shell=True, stdout=PIPE,
                        stderr=PIPE, cwd=working_dir)
    else:
        command = Popen(cmd, stdout=PIPE, stderr=PIPE)
    output = command.communicate()[0]
    return output.decode("utf-8").strip()


class Git:
    """Main Git class."""
    def __init__(self, uri):
        _uri = get_file_path(uri)
        uri = get_real_git_dir(_uri)
        if uri:
            self._dir = uri
        else:
            self._dir = _uri
    @property
    def dir(self):
        """Property: dir."""
        return self._dir

    def get_branch(self):
        """Return branch name."""
        return execute(r"git symbolic-ref HEAD | sed 's!refs\/heads\/!!'", self.dir)

    def get_project_name(self):
        """Return project name if found."""
        config_file = path.join(self.dir, ".git", "config")
        if path.exists(config_file):
            with open(config_file, 'r') as obj:
                content = obj.readlines()
            obj.close()
            lines = [line.strip() for line in content]
            try:
                cfg = ConfigParser()
                buf = StringIO("\n".join(lines))
                cfg.readfp(buf)
                url = cfg.get('remote "origin"', "url")
                return url.split("/")[-1].replace(".git", "")
            except (NoSectionError, KeyError):
                return None
        else:
            return None

    def get_status(self):
        """Return a dict with a count of added/modified/removed files."""
        modified = execute("git status | grep 'modified:'", self.dir)
        removed = execute("git status | grep 'deleted:'", self.dir)
        added = execute("git status | grep 'new file:'", self.dir)
        def get_only_files_path(array):
            array = array.strip()
            if array:
              def clean(file_path):
                  return file_path.split(':')[1].strip()
              if len(array) > 0 and array:
                  return list(map(clean, array.split("\n")))
            return []
        return {
            'added': get_only_files_path(added),
            'removed': get_only_files_path(removed),
            'modified': get_only_files_path(modified)
        }

    def get_modified(self):
        """Return a list of files that have been modified."""
        modified = execute("{ git diff --name-only ; git diff "
                           "--name-only --staged ; } | sort | uniq", self.dir)
        if modified:
            return modified.split("\n")
        return []

    def get_diff(self, filename):
        """Return the diff bettween the current file and HEAD."""
        diff = execute("git diff --unified=0 {0}".format(filename),
                       self.dir).split("\n")[4:]
        return "\n".join(diff)

    def get_remote_url(self):
        """Return remote url."""
        return execute("git config --get remote.origin.url", self.dir)

    def get_stat(self, filename):
        """Return file stat line added/removed."""
        stat = execute("git diff --stat {0}".format(filename), self.dir)
        if stat:
            return ", ".join(stat.split("\n")[1].split(",")[1:])
        return None

    def get_project_branch(self):
          branch = ""
          project_name = self.get_project_name()
          if project_name:
              branch += project_name + "/"
          branch += self.get_branch()
          return branch

    def check_branch_name(self, branch):
        return True

    def get_branch_list(self):
        b_list =  execute("git branch --list", self.dir).split("\n")
        def clean_branch_name(branch_name):
            return str(branch_name).lstrip("*").strip()
        return list(map(clean_branch_name, b_list))

    def update_branch(self, branch):
        branches = self.get_branch_list()
        if branch in branches:
            execute("git checkout {}".format(branch), self.dir)
        else:
            execute("git checkout -b {0}".format(branch), self.dir)


class NautilusPropertyPage(Gtk.Grid):
    """Property page main widget class."""
    def __init__(self, git):
        Gtk.Grid.__init__(self)
        self._git = git
        self.set_border_width(18)
        self.set_vexpand(True)
        self.set_row_spacing(6)
        self.set_column_spacing(18)
        self._build_widgets()
        self.show()

    def _build_widgets(self):
        """Build needed widgets."""
        branch = Gtk.Label(_('Branch:'))
        branch.set_halign(Gtk.Align.END)
        branch.show()

        self.attach(branch, 0, 0, 1, 1)

        branch_value = Gtk.Label()
        branch_value.set_text(self._git.get_branch())
        branch_value.set_halign(Gtk.Align.END)
        branch_value.show()

        self.attach(branch_value, 1, 0, 1, 1)
        status = self._git.get_status()
        i = 2
        for _status in status:
            if len(status[_status]) > 0:
                label = Gtk.Label()
                label.set_text(GIT_FILES_STATUS[_status]["properties"])
                label.set_halign(Gtk.Align.END)
                label.show()
                self.attach(label, 0, i, 1, 1)

                label_value = Gtk.Label()
                label_value.set_text(len(status[_status]))
                label_value.set_halign(Gtk.Align.END)
                label_value.show()
                self.attach(label_value, 1, i, 1, 1)
                i += 1

class NautilusLocation(Gtk.InfoBar):
    """Location bar main widget."""
    _popover = None
    _diff_button = None

    def __init__(self, git, window):
        Gtk.InfoBar.__init__(self)
        self._window = window
        self._git = git
        self.set_message_type(Gtk.MessageType.QUESTION)
        self.show()
        self._build_widgets()

    def _build_widgets(self):
        """Build needed widgets."""
        container = Gtk.Grid()
        container.set_row_spacing(6)
        container.set_column_spacing(6)
        container.set_valign(Gtk.Align.CENTER)
        container.show()

        icon = Gio.ThemedIcon(name="nautilus-git-symbolic")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.SMALL_TOOLBAR)
        image.show()
        container.attach(image, 0, 0, 1, 1)

        branch_button = Gtk.Button()
        branch_button.set_label(self._git.get_project_branch())
        branch_button.connect("clicked", self._update_branch)
        branch_button.show()
        container.attach(branch_button, 1, 0, 1, 1)
        self.get_content_area().add(container)

        status = self._git.get_status()
        container.attach(self._build_status_widget(status), 2, 0, 1, 1)

        button = Gtk.Button()
        button.set_label(_("More..."))
        button.show()
        self._generate_popover(button)
        button.connect("clicked", self._trigger_popover, self._popover)

        self.get_action_area().pack_end(button, False, False, 0)

    def _update_branch(self, button):
        commit = BranchWidget(self._git, self._window)

    def _build_status_widget(self, status):
        """Build a widget, contains a counter of modified/added/removed files."""
        i = 0
        grid = Gtk.Grid()
        grid.set_row_spacing(3)
        grid.set_column_spacing(3)
        grid.set_valign(Gtk.Align.CENTER)
        grid.show()
        for _status in status:
            if len(status[_status]) > 0:
                button = Gtk.Button()
                popover = self._create_status_popover(status[_status], _status)
                popover.set_relative_to(button)
                button.connect("clicked", self._trigger_popover, popover)
                icon = Gio.ThemedIcon(name=GIT_FILES_STATUS[_status]["icon"])
                image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.MENU)
                image.set_tooltip_text(GIT_FILES_STATUS[_status]["tooltip"])
                image.show()
                button.set_image(image)
                button.set_label(str(len(status[_status])))
                button.set_always_show_image(True)
                button.show()
                grid.attach(button, i, 0, 1, 1)
                i += 1
        return grid

    def _create_status_popover(self, files, status):
          popover = Gtk.Popover()
          popover.set_border_width(12)
          box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
          for _file in files:
                button = Gtk.Button()
                button.set_label(_file)
                if status != "removed":
                    button.connect("clicked", self._open_default_app, _file)
                button.get_style_context().add_class("flat")
                button.set_halign(Gtk.Align.START)
                button.show()
                box.add(button)
          box.show()
          popover.add(box)
          return popover

    def _open_default_app(self, button, _file):
        file_path = "file://" + path.join(self._git.dir, _file)
        Gio.app_info_launch_default_for_uri(file_path)


    def _trigger_popover(self, button, popover):
        """Show/hide popover."""
        if popover.get_visible():
            popover.hide()
        else:
           popover.show()

    def _generate_popover(self, widget):
        """Create the popover."""
        self._popover = Gtk.Popover()
        self._popover.set_border_width(12)
        self._popover.set_relative_to(widget)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.show()
        remote_button = Gtk.Button()
        remote_button.set_halign(Gtk.Align.START)
        remote_button.set_label(_("Open remote URL"))
        remote_button.get_style_context().add_class("flat")
        remote_url = self._git.get_remote_url()
        remote_button.connect("clicked", self._open_remote_browser, remote_url)
        if remote_url.lower().startswith(("http://", "https://", "wwww")):
            remote_button.show()
        box.add(remote_button)

        files = self._git.get_modified()

        self._diff_button = Gtk.Button()
        self._diff_button.set_halign(Gtk.Align.START)
        self._diff_button.get_style_context().add_class("flat")
        self._diff_button.set_label(_("Compare commits"))
        self._diff_button.connect("clicked", self._compare_commits)
        if len(files) > 0:
            self._diff_button.show()
            box.add(self._diff_button)

        self._popover.add(box)

    def _compare_commits(self, *args):
        """Compare commits widget creation."""
        widget = NautilusGitCompare(self._git)
        self._popover.hide()
        widget.show()


    def _open_remote_browser(self, button, remote_url):
        """Open the remote url on the default browser."""
        Gio.app_info_launch_default_for_uri(remote_url)
        self._popover.hide()


class NautilusGitCompare(Gtk.Window):
    """Nautilus diff window."""
    def __init__(self, git):
        self._git = git
        Gtk.Window.__init__(self)
        title = _("Comparing commits of {0}").format(self._git.get_project_name())
        self.set_title(title)
        self.set_default_size(600, 400)
        self._build_headerbar(title)
        GObject.type_register(GtkSource.View)
        self._build_main()
        self.show_all()

    def _build_headerbar(self, title):
        """Generate the headerbar."""
        self._hb = Gtk.HeaderBar()
        self._hb.set_show_close_button(True)
        self._hb.set_title(title)
        # Build list of modified files
        files = self._git.get_modified()
        files.sort()
        self._store = Gtk.ListStore(str)
        for filename in files:
            self._store.append([filename])
        self._files = Gtk.ComboBox.new_with_model(self._store)
        renderer_text = Gtk.CellRendererText()
        self._files.pack_start(renderer_text, True)
        self._files.add_attribute(renderer_text, "text", 0)
        self._files.set_active(0)
        self._files.connect("changed", self._on_file_changed)
        self._hb.pack_start(self._files)
        self.set_titlebar(self._hb)

    def _on_file_changed(self, combobox):
        """File selection changed signal handler."""
        tree_iter = combobox.get_active_iter()
        if tree_iter:
            model = combobox.get_model()
            _file = model[tree_iter][0]
            self.set_buffer(_file)

    def set_buffer(self, file_name):
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
            self._label.set_text(stat)
            self._label.show()

    def _build_main(self):
        """Build main widgets."""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)

        scrolled = Gtk.ScrolledWindow()
        self._source = GtkSource.View()
        scrolled.add_with_viewport(self._source)
        self._label = Gtk.Label()
        self._label.set_halign(Gtk.Align.START)
        self._label.props.margin = 6
        self._source.set_highlight_current_line(True)
        self._source.set_show_line_marks(True)
        self._source.set_background_pattern(GtkSource.BackgroundPatternType.GRID)
        self._source.set_draw_spaces(GtkSource.DrawSpacesFlags.TRAILING)

        _file = self._files.get_model()[0][0]
        self.set_buffer(_file)

        self._source.show()
        box.pack_start(self._label, False, False, 0)
        box.pack_start(scrolled, True, True, 0)
        box.show()
        self.add(box)


class BranchWidget(Gtk.Window):

    def __init__(self, git, window):
        self._git = git
        Gtk.Window.__init__(self, Gtk.WindowType.POPUP)
        # Header Bar
        self._build_headerbar()

        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_titlebar(self.hb)
        self.set_default_size(350, 100)
        self.set_transient_for(window)
        self.set_modal(True)
        self.set_resizable(False)
        self.set_border_width(18)
        self._build_main_widget()

        self.show_all()

    def _build_headerbar(self):
        self.hb = Gtk.HeaderBar()
        self.hb.set_title(self._git.get_project_branch())
        # self.hb.set_show_close_button(True)

        self.apply = Gtk.Button()
        self.apply.set_label(_("Apply"))
        self.apply.get_style_context().add_class("suggested-action")
        self.apply.connect("clicked", self.update_branch)
        self.apply.set_sensitive(False)
        self.apply.show()
        self.hb.pack_end(self.apply)

        self.cancel = Gtk.Button()
        self.cancel.set_label(_("Cancel"))
        self.cancel.connect("clicked", self.close_window)
        self.cancel.show()
        self.hb.pack_start(self.cancel)

    def _build_main_widget(self):
        grid = Gtk.Grid()
        branches = self._git.get_branch_list()
        current_branch = self._git.get_branch()
        self.branch_entry = Gtk.ComboBoxText.new_with_entry()
        self.branch_entry.set_entry_text_column(0)
        i = 0
        for branch in branches:
            if branch == current_branch:
                active_id = i
            self.branch_entry.append_text(branch)
            i += 1
        self.branch_entry.set_active(active_id)
        self.branch_entry.connect("changed", self._validate_branch_name)
        self.branch_entry.show()
        grid.set_halign(Gtk.Align.CENTER)
        grid.add(self.branch_entry)
        grid.show()
        self.add(grid)

    def _validate_branch_name(self, entry):
        branch = entry.get_active_text().strip()
        valid = True
        if branch == self._git.get_branch() or not branch:
            valid = False
        else:
            valid = self._git.check_branch_name(branch)

        self.apply.set_sensitive(valid)
        if valid:
            entry.get_style_context().remove_class("error")
        else:
            entry.get_style_context().add_class("error")


    def update_branch(self, *args):
        branch = self.branch_entry.get_active_text().strip()
        self._git.update_branch(branch)
        self.close_window()
        # Todo : refresh the window if possible?

    def close_window(self, *args):
        self.destroy()

class NautilusGitLocationWidget(GObject.GObject, Nautilus.LocationWidgetProvider):
    """Location widget extension."""
    def __init__(self):
        self.window = None
        self.uri = None

    def get_widget(self, uri, window):
        """Overwrite get_widget method."""
        self.uri = uri
        self.window = window
        if is_git(uri):
            git = Git(uri)
            widget = NautilusLocation(git, self.window)
            return widget
        else:
            return None


class NautilusGitColumnExtension(GObject.GObject, Nautilus.PropertyPageProvider):
    """Property widget extension."""
    def __init__(self):
        pass

    @staticmethod
    def get_property_pages(files):
        """Overwrite default method."""
        if len(files) != 1:
            return

        _file = files[0]
        if _file.is_directory():
            uri = _file.get_uri()
            if is_git(uri):
                git = Git(uri)
                property_label = Gtk.Label(_('Git'))
                property_label.show()

                nautilus_property = NautilusPropertyPage(git)

                return Nautilus.PropertyPage(name="NautilusPython::git",
                                             label=property_label,
                                             page=nautilus_property),

#!/usr/bin/python3
import gettext
from os import path
from urllib import unquote
from subprocess import PIPE, Popen
from ConfigParser import ConfigParser, NoSectionError
from StringIO import StringIO
from gi import require_version
require_version("Gtk", "3.0")
require_version('Nautilus', '3.0')
from gi.repository import Gtk, Nautilus, GObject, Gio
_ = gettext.gettext
gettext.textdomain('nautilus-git')

def get_file_path(uri):
    return unquote(uri[7:])


def is_git(folder_path):
    folder_path = get_file_path(folder_path)
    git_folder = path.join(folder_path, ".git")
    output = execute('git rev-parse --is-inside-work-tree', folder_path).lower()
    if path.exists(git_folder):
        return True
    elif output == "true":
        return True
    else:
        return False

def get_real_git_dir(directory):
    dirs = directory.split("/")
    current_path = ""
    for i in range(len(dirs) - 1, 0, -1): 
        current_path = "/".join(dirs[0:i])
        git_folder = path.join(current_path, ".git")
        if path.exists(git_folder):
            return current_path
            break
    return None

def execute(cmd, cd=None):
    if cd:
        p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE, cwd=cd)
    else:
        p = Popen(cmd, stdout=PIPE, stderr=PIPE)
    output = p.communicate()
    return output[0].decode("utf-8").strip()


class Git:

    def __init__(self, uri):
        _uri = get_file_path(uri)
        uri = get_real_git_dir(_uri)
        if uri:
            self._dir = uri
        else:
            self._dir = _uri
    @property
    def dir(self):
        return self._dir

    def get_branch(self):
        return execute('git rev-parse --abbrev-ref HEAD', self.dir)

    def get_project_name(self):
        file = path.join(self.dir, ".git", "config")
        if path.exists(file):
            with open(file, 'r') as obj:
                content = obj.readlines()
            obj.close()
            lines = [line.strip() for line in content]
            try:
                cfg = ConfigParser()
                buf = StringIO("\n".join(lines))
                cfg.readfp(buf)
                url = cfg.get('remote "origin"', "url")
                return url.split("/")[-1].replace(".git", "")
            except NoSectionError, KeyError:
                return None
        else:
            return None

    def get_status(self):
        modified = execute("git status | grep 'modified:' | wc -l", self.dir)
        removed = execute("git status | grep 'deleted:' | wc -l", self.dir)
        added = execute("git status | grep 'new file:' | wc -l", self.dir)
        return {
            'added': added,
            'removed': removed,
            'modified': modified
        }

    def get_remote_url(self):
        return execute("git config --get remote.origin.url", self.dir)


class NautilusPropertyPage(Gtk.Grid):

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
        branch = Gtk.Label(_('Branch:'))
        branch.set_halign(Gtk.Align.END)
        branch.show()

        self.attach(branch, 0, 0, 1, 1)

        branch_value = Gtk.Label()
        branch_value.set_text(self._git.get_branch())
        branch_value.set_halign(Gtk.Align.END)
        branch_value.show()

        self.attach(branch_value, 1, 0, 1, 1)

class NautilusLocation(Gtk.InfoBar):

    def __init__(self, git):
        Gtk.InfoBar.__init__(self)
        self._git = git
        self.set_message_type(Gtk.MessageType.QUESTION)
        self.show()
        self._build_widgets()

    def _build_widgets(self):
        container = Gtk.Grid()            
        container.set_row_spacing(6)  
        container.set_column_spacing(6)
        container.set_valign(Gtk.Align.CENTER)
        container.show()

        icon = Gio.ThemedIcon(name="nautilus-git-symbolic")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.SMALL_TOOLBAR)
        image.show()
        container.attach(image, 0, 0, 1, 1)

        label = Gtk.Label()
        project = self._git.get_project_name()
        branch = ""
        if project:
            branch = "{0}/".format(project)
        branch += self._git.get_branch()

        label.set_text(branch)
        label.show()
        container.attach(label, 1, 0, 1, 1)
        self.get_content_area().add(container)

        status = self._git.get_status()

        grid = self._build_status_widget(status)
        container.attach(grid, 2, 0, 1, 1)        
        remote_button = Gtk.Button()
        remote_button.set_label(_("Open remote URL in a browser"))

        remote_url = self._git.get_remote_url()
        remote_button.connect("clicked", self._open_remote_browser, remote_url)
        if remote_url.lower().startswith(("http://", "https://", "wwww")):
           remote_button.show()
        self.get_action_area().add(remote_button)

    def _build_status_widget(self, status):
        infos = {
            "added" : {
                "icon" : "list-add-symbolic"
            },
            "removed" : {
                "icon" : "list-remove-symbolic"
            },
            "modified": {
                "icon" : "document-edit-symbolic"
            }
        }
        i = 0
        grid = Gtk.Grid()
        grid.set_row_spacing(3)
        grid.set_column_spacing(3)
        grid.show()
        for st in status:
            if int(status[st]) > 0:
                icon = Gio.ThemedIcon(name=infos[st]["icon"])
                image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.MENU)
                image.show()
                label = Gtk.Label()
                label.set_text(status[st])
                label.show()
                grid.attach(image, i, 0, 1, 1)
                i += 1
                grid.attach(label, i, 0, 1, 1)
                i += 1
        return grid


    def _open_remote_browser(self, button, remote_url):
        Gio.app_info_launch_default_for_uri(remote_url)

class NautilusGitLocationWidget(GObject.GObject, Nautilus.LocationWidgetProvider):

    def __init__(self):
        self.window = None
        self.uri = None

    def get_widget(self, uri, window):
        self.uri = uri
        self.window = window
        if is_git(uri):
            git = Git(uri)
            widget = NautilusLocation(git)
            return widget
        else:
            return None


class NautilusGitColumnExtension(GObject.GObject, Nautilus.PropertyPageProvider):
    def __init__(self):
        pass
    
    def get_property_pages(self, files):
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
    
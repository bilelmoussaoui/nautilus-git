#!/usr/bin/python3

from gi import require_version
require_version("Gtk", "3.0")
require_version('Nautilus', '3.0')
from gi.repository import Gtk, Nautilus, GObject, Gio
from os import path
from urllib import unquote
from subprocess import PIPE, Popen
from ConfigParser import ConfigParser
from StringIO import StringIO

def get_file_path(uri):
    return unquote(uri[7:])


def is_git(folder_path):
    folder_path = get_file_path(folder_path)
    git_folder = path.join(folder_path, ".git")
    p = Popen('git rev-parse --is-inside-work-tree', shell=True, stdout=PIPE, stderr=PIPE, cwd=folder_path)
    output = p.communicate()
    output = output[0].decode("utf-8").strip().lower()
    if path.exists(git_folder):
        return True
    elif output == "true":
        return True
    else:
        return False

def execute(git):
    p = Popen(git.cmd, shell=True, stdout=PIPE, stderr=PIPE, cwd=git.dir)
    output = p.communicate()
    return output[0].decode("utf-8").strip()



class Git:

    def __init__(self, uri):
        self._dir = get_file_path(uri)
        self._cmd = ""

    @property
    def cmd(self):
        return self._cmd

    @property
    def dir(self):
        return self._dir

    def get_branch(self):
        self._cmd = 'git rev-parse --abbrev-ref HEAD'
        return execute(self)

    def get_project_name(self):
        file = path.join(self.dir, ".git", "config")
        if path.exists(file):
            with open(file, 'r') as obj:
                content = obj.readlines()
            obj.close()
            lines = [line.strip() for line in content]
            cfg = ConfigParser()
            buf = StringIO("\n".join(lines))
            cfg.readfp(buf)
            url = cfg.get('remote "origin"', "url")
            return url.split("/")[-1]
        else:
            return None

    def get_remote_url(self):
        self._cmd = "git config --get remote.origin.url"
        return execute(self)



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
        branch = Gtk.Label('Branch:')
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
        self.set_message_type(Gtk.MessageType.OTHER)
        self.show()
        self._build_widgets()

    def _build_widgets(self):
        container = Gtk.Grid()            
        container.set_row_spacing(6)  
        container.set_border_width(6)
        container.set_column_spacing(6)
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

        remote_button = Gtk.Button()
        remote_button.set_label("Open remote URL in a browser")

        remote_url = self._git.get_remote_url()
        remote_button.connect("clicked", self._open_remote_browser, remote_url)
        if remote_url.lower().startswith(("http://", "https://" , "wwww")):
           remote_button.show()
        self.get_action_area().add(remote_button)

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
                property_label = Gtk.Label('Git')
                property_label.show()
                
                nautilus_property = NautilusPropertyPage(git)
                
                return Nautilus.PropertyPage(name="NautilusPython::git",
                                             label=property_label, 
                                             page=nautilus_property),
    

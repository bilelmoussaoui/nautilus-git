from gi import require_version
require_version("Gtk", "3.0")
require_version('Nautilus', '3.0')
from gi.repository import Gtk, Nautilus, GObject, Gio
from os import path
from urllib import unquote
from subprocess import PIPE, Popen

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
        return "@{0}".format(execute(self))

class NautilusGit(GObject.GObject, Nautilus.LocationWidgetProvider):

    def __init__(self):
        self.window = None
        self.uri = None

    def get_widget(self, uri, window):
        self.uri = uri
        self.window = window
        if is_git(uri):
            git = Git(uri)
            container = Gtk.Grid()            
            container.set_row_spacing(6)  
            container.set_column_spacing(6)
            container.set_border_width(6)
            container.show()

            icon = Gio.ThemedIcon(name="gitg-symbolic")
            image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.SMALL_TOOLBAR)
            image.show()
            container.attach(image, 0, 0, 1, 1)

            label = Gtk.Label()
            label.set_text(git.get_branch())
            label.show()
            container.attach(label, 1, 0, 1, 1)
            return container
        else:
            return None


class ColumnExtension(GObject.GObject, Nautilus.PropertyPageProvider):
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
                
                container = Gtk.Grid()
                container.set_border_width(18)
                container.show()

                container.set_vexpand(True)
                container.set_row_spacing(6)
                container.set_column_spacing(18)

                branch = Gtk.Label('Branch:')
                branch.set_halign(Gtk.Align.END)
                branch.show()

                container.attach(branch, 0, 0, 1, 1)

                branch_value = Gtk.Label()
                branch_value.set_text(git.get_branch())
                branch_value.set_halign(Gtk.Align.END)
                branch_value.show()

                container.attach(branch_value, 1, 0, 1, 1)
                
                return Nautilus.PropertyPage(name="NautilusPython::git",
                                             label=property_label, 
                                             page=container),
    

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
from ConfigParser import ConfigParser, NoSectionError
from os import path
import pygit2
from StringIO import StringIO
from git_utils import uriparse
from zlib import decompress
from gi.repository import GObject
"""
TODO:
- Finish the migration to python git integration
- Move the watchdog from the gui to git
- Watch the whole .git folder for modifications instead of HEAD only.

"""


class Git(GObject.GObject):
    """Main Git class."""
    __gsignals__ = {
        'message': (GObject.SIGNAL_RUN_FIRST, None, (str, str))
    }

    def __init__(self, uri):
        GObject.GObject.__init__(self)
        dir_path = uriparse(uri)
        self._dir = pygit2.discover_repository(dir_path)
        self._repo = pygit2.init_repository(self._dir)
        self._branch = self.branch

    @property
    def dir(self):
        """Property: dir."""
        return self._dir

    @property
    def branch(self):
        head = self._repo.lookup_reference('HEAD').resolve().shorthand
        return head

    @branch.setter
    def branch(self, branch):
        if branch not in self.branches:
            commit = self._repo.head.get_object()
            branch = self._repo.branches.local.create(branch, commit)
        else:
            branch = self._repo.lookup_branch(branch)
        ref = self._repo.lookup_reference(branch.name)
        try:
            self._repo.checkout(ref)
            self._branch = branch
        except pygit2.GitError as error_msg:
            self.emit("message", str(error_msg).decode("utf-8"), "error")

    @property
    def branches(self):
        """Return a list of branches."""
        return self._repo.listall_branches()

    @property
    def remote_url(self):
        """Return remote url."""
        cfg = self._read_config_file()
        if cfg:
            remote_url = cfg.get('remote "origin"', "url")
            return remote_url
        return None

    @property
    def project(self):
        """Return project name if found."""
        cfg = self._read_config_file()
        if cfg:
            url = cfg.get('remote "origin"', "url")
            return url.split("/")[-1].replace(".git", "")
        return None

    @property
    def repository(self):
        """Return project name/branch."""
        repository = ""
        project_name = self.project
        if project_name:
            repository += project_name + "/"
        repository += self.branch
        return repository

    @property
    def commit_hex(self):
        return self._repo.head.get_object().hex

    def get_status(self):
        """Return a dict with a count of added/modified/removed files."""
        added = []
        removed = []
        modified = []
        for filepath, status in self._repo.status().items():
            if status == pygit2.GIT_STATUS_WT_MODIFIED:
                modified.append(filepath)
            elif status == pygit2.GIT_STATUS_WT_NEW:
                added.append(filepath)
            elif status == pygit2.GIT_STATUS_WT_DELETED:
                removed.append(filepath)
        return {"added": added, "modified": modified, "removed": removed}

    def get_modified(self):
        """Return a list of files that have been modified."""
        modified_files = []
        for filepath, status in self._repo.status().items():
            if status == pygit2.GIT_STATUS_WT_MODIFIED:
                modified_files.append(filepath)
        return modified_files

    def diff(self, filepath):
        # Origin content
        # For now pygit doesn't support per file diff
        idx_entry = None
        head, origin = "", ""
        for idx_entry in self._repo.index:
            if idx_entry.path == filepath:
                break
        if idx_entry:
            origin = open(path.join(self._repo.workdir, filepath), 'r').read().splitlines()
            head = self._read_object(idx_entry.hex)
        return head, origin

    @staticmethod
    def is_valid_branch(branch):
        """Check if a branch is valid or not."""
        return True

    def _read_config_file(self):
        config_file = path.join(self.dir, "config")
        if path.exists(config_file):
            with open(config_file, 'r') as obj:
                content = obj.readlines()
            obj.close()
            lines = [line.strip() for line in content]
            try:
                cfg = ConfigParser()
                buf = StringIO("\n".join(lines))
                cfg.readfp(buf)
                return cfg
            except (NoSectionError, KeyError):
                pass
        return None

    def _find_object(self, sha1):
        directory = path.join(self._repo.path, "objects",
                              sha1[:2], sha1[2:])
        if path.exists(directory):
            return directory
        return None

    def _read_object(self, sha1):
        obj = self._find_object(sha1)
        if obj:
            data = decompress(open(obj, 'rb').read())
            data = data[data.index(b'\x00') + 1:]
            return data.splitlines()
        return None

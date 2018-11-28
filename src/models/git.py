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

# Try Python2 imports
try:
    from StringIO import StringIO
    from ConfigParser import ConfigParser, NoSectionError

# Python3 imports
except ModuleNotFoundError:
    from io import StringIO
    from configparser import ConfigParser, NoSectionError


from os import environ, path
from sys import path as sys_path

sys_path.insert(0, environ["SRC_DIR"])
from utils import execute, get_file_path, get_real_git_dir


class Git:
    """Main Git class."""

    def __init__(self, uri):
        file_path = get_file_path(uri)
        git_dir = get_real_git_dir(file_path)
        if git_dir:
            self._dir = git_dir
        else:
            self._dir = file_path

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
                                 "--name-only --staged ; } | sort | uniq",
                                 self.dir)
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
        b_list = execute("git branch --list", self.dir).split("\n")

        def clean_branch_name(branch_name):
            return str(branch_name).lstrip("*").strip()
        return list(map(clean_branch_name, b_list))

    def update_branch(self, branch):
        branches = self.get_branch_list()
        if branch in branches:
            execute("git checkout {}".format(branch), self.dir)
        else:
            execute("git checkout -b {0}".format(branch), self.dir)

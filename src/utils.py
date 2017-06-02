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
from os import path
from subprocess import PIPE, Popen
from urlparse import urlsplit


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
        output = execute('git rev-parse --is-inside-work-tree',
                         folder_path).lower()
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

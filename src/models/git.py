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
from os import environ, path, listdir, walk
from StringIO import StringIO
from sys import path as sys_path
from zlib import decompress
from struct import pack, unpack
from binascii import hexlify
sys_path.insert(0, environ["SRC_DIR"])
from utils import execute, get_file_path, get_real_git_dir
"""
TODO:
- Finish the migration to python git integration
- Move the watchdog from the gui to git
- Watch the whole .git folder for modifications instead of HEAD only.

"""


class Git:
    """Main Git class."""

    def __init__(self, uri):
        file_path = get_file_path(uri)
        git_dir = get_real_git_dir(file_path)
        if git_dir:
            self._dir = git_dir
        else:
            self._dir = file_path
        self._branch = None

    @property
    def dir(self):
        """Property: dir."""
        return self._dir

    @property
    def branch(self):
        head = path.join(self.dir, ".git", "HEAD")
        with open(head, 'r') as head_obj:
            ref = head_obj.readline()
        self._branch = ref.split("/")[-1].strip()
        return self._branch

    @branch.setter
    def branch(self, branch):
        branches = self.branches
        head_file = path.join(self.dir, ".git", "HEAD")
        if branch not in branches:
            current_hash = self.hash
            refs_file = path.join(self.dir, ".git", "refs",
                                  "heads", branch)
            with open(refs_file, 'w') as refs_obj:
                refs_obj.write(current_hash)

        with open(head_file, 'r') as head_obj:
            head_content = head_obj.readlines()

        head_content = head_content[0].strip().split("/")
        head_content[-1] = branch
        head_content = "/".join(head_content)

        with open(head_file, 'w') as head_obj:
            head_obj.write(head_content)
        self._branch = branch

    @property
    def branches(self):
        """Return a list of branches."""
        refs_dir = path.join(self.dir, ".git", "refs", "heads")
        return sorted(listdir(refs_dir))

    @property
    def hash(self):
        """Return current hash."""
        refs_file = path.join(self.dir, ".git", "refs",
                              "heads", self.branch)
        with open(refs_file, 'r') as refs_obj:
            return refs_obj.read()
        return None

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
        modified = execute("git status | grep 'modified:' | sort | uniq",
                           self.dir)
        if modified:
            def clear(filename):
                return filename.replace("modified:", "").strip()
            files = list(map(clear, modified.split("\n")))
            return files
        return []

    def diff(self, filepath):
        # Origin content
        origin = open(path.join(self.dir, filepath),
                      'r').read().splitlines()
        sha1 = self._get_hash(filepath)
        head = self._read_object(sha1)
        return head, origin

    @staticmethod
    def is_valid_branch(branch):
        """Check if a branch is valid or not."""
        return True

    def _get_hash(self, filename):
        entries = self._read_index()
        return entries.get(path.join(self.dir, filename))

    def _read_index(self):
        index = path.join(self.dir, ".git", "index")
        data = open(index, 'rb').read()
        # Header contains 12-byte
        data_entries = data[12:-20]
        i = 0
        entries = {}
        while i + 62 < len(data_entries):
            fields_end = i + 62
            fields = unpack('!20sH', data_entries[i + 40:fields_end])
            sha1_hash = hexlify(fields[0]).decode("ascii")
            path_end = data_entries.index(b'\x00', fields_end)
            filepath = data_entries[fields_end:path_end]
            i += ((62 + len(filepath) + 8) // 8) * 8
            try:
                filepath = path.join(self.dir, filepath.decode())
                if path.exists(filepath):
                    entries[filepath] = sha1_hash
            except UnicodeDecodeError:
                break
        return entries

    def _find_object(self, sha1):
        directory = path.join(self.dir, ".git", "objects",
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

    def _read_config_file(self):
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
                return cfg
            except (NoSectionError, KeyError):
                pass
        return None

#!/usr/bin/env python3

import os
from os.path import join
import compileall
import subprocess

prefix = os.environ.get('MESON_INSTALL_PREFIX', '/usr/local')
datadir = join(prefix, 'share')
destdir = os.environ.get('DESTDIR', '')

if not destdir:
    print('Updating icon cache...')
    subprocess.call(['gtk-update-icon-cache', '-qtf', join(datadir, 'icons', 'hicolor')])

print('Compiling python bytecode...')
moduledir = join(datadir, 'nautilus-git', 'src')
compileall.compile_dir(destdir + moduledir, optimize=2)

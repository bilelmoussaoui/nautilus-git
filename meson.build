project('nautilus-git', 'c', version: '1.3')

message('Looking for dependencies')
python = find_program('python2')
intltool_merge = find_program('intltool-merge')
glib = dependency('glib-2.0')
gobject = dependency('gobject-2.0')
gir = dependency('gobject-introspection-1.0')
gtk = dependency('gtk+-3.0', version : '>=3.10')


message('Getting python install dir')
r = run_command(python, '-c', 'from distutils.sysconfig import get_python_lib; print(get_python_lib())')
if r.returncode() != 0
    error('Cannot find python install dir')
endif
python_dir = r.stdout().strip()

message('destination directory: ' + get_option('prefix'))
message('file manager: ' + get_option('file_manager'))
if get_option('post_install') == true
	post_install = 'enabled'
else
	post_install = 'disabled'
endif
message('post install script is: ' + post_install)

subdir('data')
subdir('po')

file_manager = get_option('file_manager')


# Configuration params
conf = configuration_data()
conf.set('DATADIR', join_paths(get_option('prefix'), get_option('datadir'), meson.project_name()))
conf.set('PYTHONDIR', python_dir)


run_command(python, '-m', 'compileall', join_paths(meson.current_source_dir(), 'src'))
install_subdir('src/', install_dir: conf.get('DATADIR'))


if file_manager == 'nautilus'
    package = 'nautilus-git'
    destination = 'nautilus-python'
else
    package = 'nemo-git'
    destination = 'nemo-python'
endif



configure_file(input : join_paths(package, 'git.py.in'), output : 'git.py', configuration : conf)
configure_file = '@0@/git.py'.format(meson.current_build_dir())
install_data(configure_file, install_mode : false,
            install_dir : join_paths(get_option('prefix'), 'share', destination, 'extensions/'))


if get_option('post_install') == true
	meson.add_install_script('meson_post_install.sh')
endif

project('nautilus-git', 'c', version: '1.1')

conf = configuration_data()
message('Looking for dependencies')
python = find_program('python2')
intltool_merge = find_program('intltool-merge')
glib = dependency('glib-2.0')
gobject = dependency('gobject-2.0')
gir = dependency('gobject-introspection-1.0')
gtk = dependency('gtk+-3.0', version : '>=3.10')
message('destination directory : ' + get_option('prefix'))
if get_option('post_install') == true
	post_install = 'enabled'
else
	post_install = 'disabled'
endif
message('post install script is : ' + post_install)

subdir('data/icons')
subdir('po')

install_data('nautilus-git/git.py', install_mode : false,
			 install_dir : get_option('prefix') + '/share/nautilus-python/extensions/')

if get_option('post_install') == true
	meson.add_install_script('meson_post_install.sh')
endif

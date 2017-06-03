project('nautilus-git',
  version: '1.3',
  meson_version: '>= 0.40.0'
)

file_manager = get_option('file_manager')
if file_manager == 'nautilus'
    package = 'nautilus-git'
    destination = 'nautilus-python'
    filename = 'nautilus-git.py'
elif file_manager == 'nemo'
    package = 'nemo-git'
    destination = 'nemo-python'
    filename = 'nemo-git.py'
endif

i18n = import('i18n')
pkgdata_dir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
extension_dir = join_paths(get_option('datadir'), destination, 'extensions')

subdir('data')
subdir('po')

install_subdir('src', install_dir: pkgdata_dir)

# Configuration params
conf = configuration_data()
conf.set('DATADIR', pkgdata_dir)
conf.set('PROJECT', meson.project_name())

configure_file(
  input : join_paths(package, filename + '.in'),
  output : filename,
  configuration : conf,
  install_dir: extension_dir
)

meson.add_install_script('meson_post_install.py')

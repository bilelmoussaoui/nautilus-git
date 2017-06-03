gnome = import('gnome')

subdir('icons')

gnome.compile_resources(
  'nautilus-git', 'nautilus-git.gresource.xml',
  gresource_bundle: true,
  install_dir : pkgdata_dir,
  install: true
)

metafile = meson.project_name() + '.metainfo.xml'
i18n.merge_file(
  input: metafile + '.in',
  output: metafile,
  po_dir: '../po',
  install: true,
  install_dir : join_paths(get_option('datadir'), 'metainfo')
)

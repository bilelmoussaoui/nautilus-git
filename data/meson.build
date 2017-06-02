gnome = import('gnome')

subdir('icons')

po_dir = join_paths(get_option('prefix'), get_option('datadir'), 'locale')
build_dir = join_paths(get_option('prefix'), get_option('datadir'))

message('TODO: Compiling resources')
gnome.compile_resources(
     'nautilus-git', 'nautilus-git.gresource.xml',
     gresource_bundle: true,
     source_dir : '.',
     install_dir : join_paths(build_dir, 'nautilus-git'),
     install: true)


metafile = meson.project_name() + '.metainfo.xml'
message('TODO: Preparing metainfo')
custom_target(metafile,
    output : metafile,
    input : metafile + '.in',
    command : [intltool_merge, '--xml-style', po_dir, '@INPUT@', '@OUTPUT@'],
    install : true,
    install_dir : join_paths(get_option('datadir'), 'metainfo')
    )

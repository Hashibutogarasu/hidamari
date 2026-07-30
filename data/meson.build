desktop_conf = configuration_data()
desktop_conf.set('bindir', join_paths(get_option('prefix'), get_option('bindir')))

desktop_file_in = configure_file(
  input: 'io.github.jeffshee.Hidamari.desktop.in',
  output: 'io.github.jeffshee.Hidamari.desktop.in.configured',
  configuration: desktop_conf,
)

desktop_file = i18n.merge_file(
  input: desktop_file_in,
  output: 'io.github.jeffshee.Hidamari.desktop',
  type: 'desktop',
  po_dir: '../po',
  install: true,
  install_dir: join_paths(get_option('datadir'), 'applications')
)

desktop_utils = find_program('desktop-file-validate', required: false)
if desktop_utils.found()
  test('Validate desktop file', desktop_utils,
    args: [desktop_file]
  )
endif

appstream_file = i18n.merge_file(
  input: 'io.github.jeffshee.Hidamari.appdata.xml.in',
  output: 'io.github.jeffshee.Hidamari.appdata.xml',
  po_dir: '../po',
  install: true,
  install_dir: join_paths(get_option('datadir'), 'appdata')
)

appstream_util = find_program('appstream-util', required: false)
if appstream_util.found()
  test('Validate appstream file', appstream_util,
    args: ['validate', appstream_file]
  )
endif

install_data('io.github.jeffshee.Hidamari.gschema.xml',
  install_dir: join_paths(get_option('datadir'), 'glib-2.0/schemas')
)

compile_schemas = find_program('glib-compile-schemas', required: false)
if compile_schemas.found()
  test('Validate schema file', compile_schemas,
    args: ['--strict', '--dry-run', meson.current_source_dir()]
  )
endif

subdir('icons')

plasma_wallpaper_id = 'io.github.jeffshee.Hidamari.wallpaper'

install_subdir('plasma/wallpapers/' + plasma_wallpaper_id,
  install_dir: join_paths(get_option('datadir'), 'plasma/wallpapers')
)

kpackagetool5 = find_program('kpackagetool5', required: false)
if kpackagetool5.found()
  meson.add_install_script('plasma-kpackage-install.py',
    join_paths(meson.current_source_dir(), 'plasma/wallpapers', plasma_wallpaper_id)
  )
endif

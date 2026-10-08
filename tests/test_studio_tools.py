import importlib.util
from pathlib import Path
import tempfile
import unittest
spec=importlib.util.spec_from_file_location('studio_tools',Path(__file__).resolve().parents[1]/'studio/tools.py')
tools=importlib.util.module_from_spec(spec);spec.loader.exec_module(tools)

class StudioToolTests(unittest.TestCase):
    def test_versioned_daw_is_detected_without_using_a_plugin_host_as_daw(self):
        ardour=tools.TOOLS['Recording & mixing'][0]
        self.assertEqual(tools.resolve_tool(ardour,lambda n:'/usr/bin/ardour9' if n=='ardour9' else None,[]),['/usr/bin/ardour9'])
        self.assertTrue(all('carla' not in item[2] for item in tools.TOOLS['Recording & mixing']))

    def test_missing_tool_is_unavailable(self):
        self.assertIsNone(tools.resolve_tool(tools.TOOLS['Recording & mixing'][0],lambda n:None,[]))

    def test_desktop_launch_preserves_wrapper_arguments_and_version_independence(self):
        with tempfile.TemporaryDirectory() as folder:
            entry=Path(folder)/'org.ardour.Ardour.desktop'
            entry.write_text('[Desktop Entry]\nType=Application\nExec=ardour99 --session "Name with spaces" %F\n')
            which=lambda n:'/usr/bin/'+n if n in {'gio','ardour99'} else None
            self.assertEqual(tools.resolve_tool(tools.TOOLS['Recording & mixing'][0],which,[folder]),
                             ['/usr/bin/gio','launch',str(entry)])

    def test_hidden_and_stale_desktop_entries_are_not_available(self):
        with tempfile.TemporaryDirectory() as folder:
            entry=Path(folder)/'ardour.desktop'
            which=lambda n:'/usr/bin/'+n if n=='gio' else None
            for data in ['Type=Application\nHidden=true\nExec=gio',
                         'Type=Application\nTryExec=missing\nExec=gio',
                         'Type=Application\nExec=missing', 'Type=Application\nExec="unterminated']:
                entry.write_text('[Desktop Entry]\n'+data+'\n')
                self.assertIsNone(tools.resolve_tool(tools.TOOLS['Recording & mixing'][0],which,[folder]))

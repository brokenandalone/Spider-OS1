"""Discover Ubuntu Studio applications already on this machine; never install."""
import configparser
import os
from pathlib import Path
import shlex
import shutil

# title, task, command candidates, desktop-ID patterns
TOOLS = {
    'Recording & mixing': [
        ('Ardour', 'Record, mix and master audio', ('ardour','ardour9','ardour8','ardour7'), ('*ardour*.desktop',)),
        ('Qtractor', 'Arrange audio and MIDI tracks', ('qtractor',), ('*qtractor*.desktop',)),
        ('Audacity', 'Record and edit audio files', ('audacity',), ('*audacity*.desktop',)),
    ],
    'Instruments & effects': [
        ('Carla', 'Load plugins and connect instruments', ('carla',), ('*carla*.desktop',)),
        ('Guitarix', 'Guitar amplification and effects', ('guitarix',), ('*guitarix*.desktop',)),
        ('Rakarrack', 'Guitar effects rack', ('rakarrack',), ('*rakarrack*.desktop',)),
        ('Hydrogen', 'Program drums and patterns', ('hydrogen',), ('*hydrogen*.desktop',)),
        ('Rosegarden', 'Compose MIDI and notation', ('rosegarden',), ('*rosegarden*.desktop',)),
        ('Qsynth', 'Play SoundFont instruments', ('qsynth',), ('*qsynth*.desktop',)),
        ('Yoshimi', 'Software synthesizer', ('yoshimi',), ('*yoshimi*.desktop',)),
    ],
    'Routing & mastering': [
        ('Audio Configuration', 'Ubuntu Studio audio settings', ('ubuntustudio-audio-config',), ('*ubuntustudio*audio*.desktop',)),
        ('Patchance', 'Connect audio and MIDI ports', ('patchance',), ('*patchance*.desktop',)),
        ('Qpwgraph', 'Manage PipeWire connections', ('qpwgraph',), ('*qpwgraph*.desktop',)),
        ('QjackCtl', 'JACK connections and controls', ('qjackctl',), ('*qjackctl*.desktop',)),
        ('Volume Control', 'Choose inputs, outputs and levels', ('pavucontrol',), ('*pavucontrol*.desktop',)),
        ('JAMin', 'Mastering processor', ('jamin',), ('*jamin*.desktop',)),
    ],
    'Video & artwork': [
        ('Kdenlive', 'Edit video and music visuals', ('kdenlive',), ('*kdenlive*.desktop',)),
        ('OBS Studio', 'Record video or broadcast', ('obs',), ('*obs*.desktop',)),
        ('Blender', 'Create 3D scenes and animation', ('blender',), ('*blender*.desktop',)),
        ('GIMP', 'Edit photographs and artwork', ('gimp','gimp-3.0'), ('*gimp*.desktop',)),
        ('Inkscape', 'Create vector artwork', ('inkscape',), ('*inkscape*.desktop',)),
        ('Krita', 'Draw and paint', ('krita',), ('*krita*.desktop',)),
    ],
}


def desktop_directories():
    home = Path(os.environ.get('XDG_DATA_HOME', str(Path.home()/'.local/share')))
    dirs = [home, *map(Path, os.environ.get('XDG_DATA_DIRS','/usr/local/share:/usr/share').split(':')),
            Path('/var/lib/flatpak/exports/share'), Path.home()/'.local/share/flatpak/exports/share']
    return [p/'applications' for p in dirs]


def resolve_tool(tool, which=None, directories=None):
    which = which or shutil.which
    title, description, candidates, patterns = tool
    for candidate in candidates:
        executable = which(candidate)
        if executable:
            return [executable]
    gio = which('gio')
    if not gio:
        return None
    # Desktop entries preserve versioned executables, wrappers and Flatpak launch args.
    for directory in directories if directories is not None else desktop_directories():
        for pattern in patterns:
            for entry in sorted(Path(directory).glob(pattern)):
                parser = configparser.ConfigParser(interpolation=None, strict=False)
                try:
                    parser.read(entry, encoding='utf-8')
                    info = parser['Desktop Entry']
                    if info.get('Type') != 'Application' or info.get('Hidden','false').lower() == 'true':
                        continue
                    if info.get('TryExec') and not which(info['TryExec']):
                        continue
                    parts = shlex.split(info.get('Exec',''))
                    if not parts or not which(parts[0]):
                        continue
                except (OSError, ValueError, configparser.Error, KeyError):
                    continue
                return [gio, 'launch', str(entry)]
    return None

import array
import atexit
import os
import sys
import tempfile
import wave

try:
    import winsound
except ImportError:
    winsound = None

_winmm = None
if sys.platform.startswith("win"):
    try:
        import ctypes
        _winmm = ctypes.windll.winmm
    except Exception:
        _winmm = None

HAS_MCI = _winmm is not None

SOUND_DIR = os.path.dirname(os.path.abspath(__file__))

SFX_ENABLED = True
MUSIC_ENABLED = True
MUSIC_FILE = "Energizing Game.wav"
MUSIC_VOLUME = 0.3

SFX = {
    "bell": ("bell.wav", 1.0),
    "punch": ("punch.wav", 1.0),
    "crit": ("crit.wav", 1.0),
    "ult": ("ult.wav", 1.0),
    "ult_berserk": ("ult_berserk.wav", 1.0),
    "ult_bloodlust": ("ult_bloodlust.wav", 1.0),
    "ult_lava": ("ult_lava.wav", 1.0),
    "hurt": ("hurt.wav", 1.0),
    "roar": ("roar.wav", 0.9),
    "tick": ("tick.wav", 0.6),
    "ko_win": ("ko_win.wav", 1.0),
    "ko_lose": ("ko_lose.wav", 1.0),
    "move": ("move.wav", 0.6),
    "select": ("select.wav", 0.7),
    "back": ("back.wav", 0.7),
    "buy": ("buy.wav", 0.9),
    "denied": ("denied.wav", 0.8),
    "cheat": ("cheat.wav", 1.0),
}

MCI_ONLY = {"move", "select", "back", "buy", "denied", "cheat", "tick", "roar"}

_aliases = {}
_music_on = False


def _mci(command):
    if _winmm is None:
        return -1
    try:
        return _winmm.mciSendStringW(command, None, 0, None)
    except Exception:
        return -1


def _open(name):
    if name in _aliases:
        return _aliases[name]
    alias = None
    entry = SFX.get(name)
    if entry and HAS_MCI:
        path = os.path.join(SOUND_DIR, entry[0])
        if os.path.exists(path):
            a = "sfx_" + name
            _mci("close " + a)
            if _mci('open "%s" type waveaudio alias %s' % (path, a)) == 0:
                _mci("setaudio %s volume to %d" % (a, int(entry[1] * 1000)))
                alias = a
    _aliases[name] = alias
    return alias


def preload():
    if HAS_MCI and SFX_ENABLED:
        for name in SFX:
            _open(name)


def _close_all():
    if HAS_MCI:
        _mci("close all")


atexit.register(_close_all)


def _quiet_copy(path, volume):
    out = os.path.join(tempfile.gettempdir(), "punch_type_music_%d.wav" % int(volume * 100))
    if os.path.exists(out):
        return out
    try:
        with wave.open(path, "rb") as src:
            params = src.getparams()
            if src.getsampwidth() != 2:
                return path
            frames = src.readframes(src.getnframes())
        samples = array.array("h")
        samples.frombytes(frames)
        quiet = array.array("h", (int(s * volume) for s in samples))
        with wave.open(out, "wb") as dst:
            dst.setparams(params)
            dst.writeframes(quiet.tobytes())
        return out
    except Exception:
        return path


def play_music():
    global _music_on
    if not MUSIC_ENABLED or _music_on:
        return
    path = os.path.join(SOUND_DIR, MUSIC_FILE)
    if winsound and os.path.exists(path):
        path = _quiet_copy(path, MUSIC_VOLUME)
        winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_LOOP)
        _music_on = True


def stop_music():
    global _music_on
    if winsound:
        winsound.PlaySound(None, winsound.SND_PURGE)
    _music_on = False


def play_sfx(name):
    if not SFX_ENABLED:
        return
    entry = SFX.get(name)
    if not entry:
        return
    if HAS_MCI:
        alias = _open(name)
        if alias:
            _mci("play %s from 0" % alias)
            return
    if winsound is None or name in MCI_ONLY:
        return
    path = os.path.join(SOUND_DIR, entry[0])
    if not os.path.exists(path):
        return
    try:
        winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT)
    except RuntimeError:
        pass


preload()

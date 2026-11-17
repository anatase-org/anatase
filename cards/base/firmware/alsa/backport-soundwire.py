"""Backport SoundWire UCM fixes missing from Fedora 45 alsa-ucm 1.2.16.1-2.

Remove when Fedora includes alsa-ucm-conf commits 182d0122 and c1f72c5d.
Only edit the affected sequences so other packaged codec settings stay current.
"""

from pathlib import Path


def replace_once(path: Path, before: str, after: str) -> None:
    text = path.read_text()
    if text.count(after) == 1:
        return
    if text.count(before) != 1:
        raise RuntimeError(f"SoundWire backport no longer matches {path}; review Fedora's UCM")
    path.write_text(text.replace(before, after, 1))


ucm = Path("/usr/share/alsa/ucm2/sof-soundwire")

# https://github.com/alsa-project/alsa-ucm-conf/commit/182d0122a7d98cfa5f2d42d3cb8e9e1b8697b69a
replace_once(
    ucm / "sof-soundwire.conf",
    "${var:MultiCodecRegex}|rt1318|",
    "${var:MultiCodecRegex}|tas2783|rt1318|",
)

# https://github.com/alsa-project/alsa-ucm-conf/commit/c1f72c5d82f5c8a87b4eebacd77bf427ccfbda48
replace_once(
    ucm / "rt721.conf",
    """\tEnableSequence [
\t\tcset "name='Headphone Switch' on"
\t]

\tDisableSequence [
\t\tcset "name='Headphone Switch' off"
\t]
""",
    """\tIf.hs {
\t\tCondition {
\t\t\tType ControlExists
\t\t\tControl "name='Headphone Switch'"
\t\t}
\t\tTrue {
\t\t\tEnableSequence [
\t\t\t\tcset "name='Headphone Switch' on"
\t\t\t]
\t\t\tDisableSequence [
\t\t\t\tcset "name='Headphone Switch' off"
\t\t\t]
\t\t}
\t}
""",
)

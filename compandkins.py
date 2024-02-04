#!/usr/bin/env python3
# coding: utf-8
""" Apply dynamic range compression/expansion
    and silence removal to AntennaPod podcasts """
import sys
from dataclasses import dataclass
from pathlib import Path
import ffmpeg  # type: ignore
# import ffrich  # type: ignore
import ffrich  # type: ignore
from rich import print

""" Edited path"""
outdir = Path.home() / "storage/shared/" / "antennapodcomp"
""" Input path """
pods = Path.home() / "storage/shared" / "antennapods"
""" Silence reduction """
SR = True


@dataclass
class Prober:
    """FFprobe streams"""

    file: Path | str

    def __post_init__(self):
        try:
            self.probe = ffmpeg.probe(str(self.file))
            astream = self.probe["streams"][0]
            self.bitrate = astream["bit_rate"]
            self.duration = astream["duration"]
        except Exception:  # incomplete download
            print(str(self.file))
            raise SystemExit
        try:
            tags = self.probe["format"]["tags"]
        except KeyError:  # missing metadata
            tags = {}
            tags["comment"] = ""
        self.comment = tags.get("comment", "")


def alreadyCompandt(i: Path) -> bool:
    probe = Prober(str(i))
    if "compandt" in probe.comment:
        print(f'"{i.name}" already processed')
        return True
    else:
        return False


def compandit(i, o, sr=False, srmath=False):
    """Compand with ffmpeg, progress bar with ffrich"""
    i = str(i)
    o = str(o)
    probe = Prober(i)

    audio = ffmpeg.input(i).audio
    """ ffmpeg says
        typical attack/decay values are 0.3 & 0.8
        But -ks , -rs, & -s are getting cut
    """
    audio = audio.filter(
        "compand",
        attacks="0.3",
        decays="0.8",
        **{"soft-knee": "6"},
        points="-85/-70|-70/-10",
        gain="-14",
        volume="-85",
        delay="0.2",
    )

    if sr:  # Remove silences!
        audio = audio.filter(
            "silenceremove",
            stop_periods="-1",
            detection="peak",
            stop_duration="0.2",  # was 0.2
            stop_threshold="-31dB",  # was -29dB
        )
    """ originally
    audio_bitrate=probe.bitrate
    but I am using 64k to save space 😞 """
    stream = ffmpeg.output(
        audio,
        o,
        f="mp3",
        audio_bitrate="64k",
        metadata="comment=compandt",
        map="0:1?",
    )  # saves thumbnail

    stream = ffmpeg.overwrite_output(stream)
    #    ffmpeg.run()
    args = ffmpeg.compile(stream)

    ffrich.main(args[1:])

    if srmath and Path(o).is_file():  # show savings!
        d1 = float(probe.duration)
        d2 = float(Prober(o).duration)
        if (d1 and d2) and (d2 - d1):
            minutes = int((d1 - d2) / 60)
            seconds = int((d1 - d2) % 60)
            portion = int((d1 - d2) / d1 * 100)
            print(
                f"{minutes} minutes {seconds} seconds. {portion}% silent."
            )


def delFile(show: Path) -> bool:
    """Delete contents of temp folder, unless -k passed"""
    keep = False
    if len(sys.argv) > 1:
        if sys.argv[1] == "-k":
            keep = True
    if not keep:
        show.unlink()
    return keep


# File choosing logic
if not any(pods.iterdir()):
    print(
        "[bright_red]Work Dir empty: [/bright_red]" + f"{pods.name}"
    )
    if any(Path(outdir).iterdir()):
        print(
            "[bright_green]"
            + "Output directory not empty!"
            + "[/bright_green]"
        )


def keyboard_escape(func):
    """Escape whole iteration w/ ctrl C"""
    def wrap(*args, **kwargs):
        try:
            func()
        except KeyboardInterrupt:
            raise KeyboardInterrupt
    return wrap


# @keyboard_escape
def main():
    ''' Main file choosing loop '''
    for podsAuthor in pods.iterdir():
        parent = Path(podsAuthor)
        if parent.is_dir():
            print(f"[green]{parent.stem}[/green]")
            parentCompandPath = outdir / parent.stem
            parentCompandPath.mkdir(exist_ok=True)
            sortedPaths = sorted(parent.iterdir())
            for mp3Path in sortedPaths:
                mp3CompandPath = Path(parentCompandPath / mp3Path.name)
                if not alreadyCompandt(mp3Path):
                    compandit(
                        mp3Path,
                        mp3CompandPath,
                        sr=SR,
                        srmath=True,
                    )
                    # TODO: Extract and Place APIC images in file
                    delFile(mp3Path)
                else:  # move the already-compandt w/ the rest
                    mp3Path.replace(mp3CompandPath)

            parent.rmdir()
            if not any(parentCompandPath.iterdir()):
                print(f"[red]Nothing in[/red] {parentCompandPath.name}")
                parentCompandPath.rmdir()


if __name__ == "__main__":
    main()

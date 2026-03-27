import subprocess
import sys
from pathlib import Path


OUT_DIR = Path("downloads")


def download_audio(url: str, out_dir: Path = OUT_DIR) -> Path:
    out_dir.mkdir(exist_ok=True)
    template = out_dir / "%(title).120s_%(id)s.%(ext)s"

    res = subprocess.run(
        [
            "yt-dlp",
            url,
            "-x",
            "--audio-format",
            "mp3",
            "--audio-quality",
            "0",
            "--print",
            "after_move:filepath",
            "-o",
            str(template),
        ],
        check=True,
        text=True,
        capture_output=True,
    )
    path_str = res.stdout.strip().splitlines()[-1].strip()
    return Path(path_str)


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python3 download_audio.py <instagram_reel_url>", file=sys.stderr)
        raise SystemExit(2)

    url = sys.argv[1].strip()
    out_path = download_audio(url, OUT_DIR)
    print(out_path)


if __name__ == "__main__":
    main()


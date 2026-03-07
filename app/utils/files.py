from pathlib import Path


def ensure_directory(path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def write_placeholder_video(path: str) -> str:
    ensure_directory(path)
    content = b"FAKE_VIDEO_BINARY"
    with open(path, "wb") as fp:
        fp.write(content)
    return path

import asyncio

from app.adapters.brief_sources.local_file import LocalFileBriefSource


def test_local_file_brief_source_reads(tmp_path):
    path = tmp_path / "brief.txt"
    path.write_text("brief line\n")

    source = LocalFileBriefSource(str(path))
    text = asyncio.run(source.fetch_latest())
    assert text == "brief line"

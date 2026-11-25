"""CLI and persistence tests for titlecase preview mode."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

import pytest
from mediafile import MediaFile

from beets.dbcore.query import InvalidQueryError
from beets.library import Item, Library
from beets.test.helper import PluginTestHelper


class TestTitlecasePreview(PluginTestHelper):
    plugin = "titlecase"
    preload_plugin = False

    @pytest.mark.parametrize("flag", ["-p", "--preview"])
    def test_preview_executes_and_shows_original_and_proposed(
        self, capsys, flag
    ):
        self.add_item(title="in a silent way")
        with self.configure_plugin({"fields": ["title"]}):
            self.run_command("titlecase", flag)
        output = capsys.readouterr().out
        assert "Preview:" in output
        assert "title: 'in a silent way' -> 'In a Silent Way'" in output

    @pytest.mark.parametrize(
        "options,field,original,expected",
        [
            ({}, "title", "in a silent way", "In a Silent Way"),
            ({}, "title", "Aaron-carl", "Aaron-Carl"),
            ({}, "title", "(original mix)", "(Original Mix)"),
            (
                {"preserve": ["easyFun"]},
                "title",
                "easyfun song",
                "easyFun Song",
            ),
            (
                {"preserve": ["THE PSYCHIC ED RUSH"]},
                "title",
                "the psychic ed rush mix",
                "THE PSYCHIC ED RUSH Mix",
            ),
            ({"replace": [("_", " ")]}, "title", "a_new_day", "A New Day"),
            ({"separators": ["/"]}, "title", "it / the test", "It / The Test"),
            ({"force_lowercase": True}, "title", "KhAmElEoN", "Khameleon"),
            (
                {"small_first_last": False},
                "title",
                "In a Silent Way",
                "in a Silent Way",
            ),
            ({}, "artist", "amyl and the sniffers", "Amyl and The Sniffers"),
            (
                {"the_artist": False},
                "artist",
                "amyl and the sniffers",
                "Amyl and the Sniffers",
            ),
            ({}, "title", "été in the city", "Été in the City"),
        ],
    )
    def test_preview_uses_existing_rules(
        self, capsys, options, field, original, expected
    ):
        item = self.add_item(**{field: original})
        with self.configure_plugin({"fields": [field], **options}):
            self.run_command("titlecase", "-p")
        assert (
            f"{field}: {original!r} -> {expected!r}" in capsys.readouterr().out
        )
        assert self.lib.get_item(item.id)[field] == original

    def test_preview_respects_configured_fields(self, capsys):
        item = self.add_item(title="new day", artist="some artist")
        with self.configure_plugin({"fields": ["artist"]}):
            self.run_command("titlecase", "-p")
        output = capsys.readouterr().out
        assert "artist: 'some artist' -> 'Some Artist'" in output
        assert "title:" not in output
        assert self.lib.get_item(item.id).title == "new day"

    @pytest.mark.parametrize(
        "query", [("title:first",), ("artist:chosen", "year:2003")]
    )
    def test_preview_filters_optional_queries(self, capsys, query):
        self.add_item(title="first song", artist="chosen", year=2003)
        self.add_item(title="second song", artist="chosen", year=2004)
        self.add_item(title="third song", artist="other", year=2003)
        with self.configure_plugin({"fields": ["title"]}):
            self.run_command("titlecase", "-p", *query)
        output = capsys.readouterr().out
        assert "title: 'first song' -> 'First Song'" in output
        assert "second song" not in output
        assert "third song" not in output

    def test_preview_preserves_database_file(self, capsys):
        db_path = self.temp_path / "preview.db"
        lib = Library(db_path, self.lib_path)
        try:
            item = Item(title="new day", artist="some artist")
            item.add(lib)
            before = db_path.read_bytes()
            with closing(sqlite3.connect(db_path)) as connection:
                rows_before = list(connection.iterdump())
            with self.configure_plugin({"fields": ["title", "artist"]}):
                self.run_command("titlecase", "-p", lib=lib)
            assert "'new day' -> 'New Day'" in capsys.readouterr().out
            assert db_path.read_bytes() == before
            with closing(sqlite3.connect(db_path)) as connection:
                assert list(connection.iterdump()) == rows_before
            assert lib.get_item(item.id).title == "new day"
        finally:
            lib._close()

    def test_preview_never_calls_persistence_methods(self):
        self.add_item(title="new day")
        self.config["import"]["write"] = True
        with (
            self.configure_plugin({"fields": ["title"]}),
            patch.object(Item, "store") as store,
            patch.object(Item, "try_write") as try_write,
            patch.object(Item, "write") as write,
        ):
            self.run_command("titlecase", "-p")
        store.assert_not_called()
        try_write.assert_not_called()
        write.assert_not_called()

    def test_preview_preserves_music_file_bytes_and_tags(self):
        item = self.add_item_fixture(title="new day", artist="some artist")
        item.write()
        path = Path(item.filepath)
        before = path.read_bytes()
        self.config["import"]["write"] = True
        with self.configure_plugin({"fields": ["title", "artist"]}):
            self.run_command("titlecase", "-p")
        assert path.read_bytes() == before
        tags = MediaFile(path)
        assert tags.title == "new day"
        assert tags.artist == "some artist"
        assert self.lib.get_item(item.id).title == "new day"

    def test_preview_preserves_live_item(self, capsys):
        item = self.add_item(
            title="new day", artists=["first artist", "second artist"]
        )
        before = dict(item)
        with (
            self.configure_plugin({"fields": ["title", "artists"]}),
            patch.object(self.lib, "items", return_value=[item]),
        ):
            self.run_command("titlecase", "-p")
        assert "'new day' -> 'New Day'" in capsys.readouterr().out
        assert dict(item) == before

    def test_preview_handles_multiple_tracks(self, capsys):
        first = self.add_item(title="first song")
        second = self.add_item(title="second song")
        with self.configure_plugin({"fields": ["title"]}):
            self.run_command("titlecase", "-p")
        output = capsys.readouterr().out
        assert "title: 'first song' -> 'First Song'" in output
        assert "title: 'second song' -> 'Second Song'" in output
        assert output.count("Preview:") == 2
        assert self.lib.get_item(first.id).title == "first song"
        assert self.lib.get_item(second.id).title == "second song"

    @pytest.mark.parametrize("empty_library", [False, True])
    def test_preview_handles_no_matches(self, capsys, empty_library):
        if not empty_library:
            self.add_item(title="existing song")
        with self.configure_plugin({"fields": ["title"]}):
            self.run_command("titlecase", "-p", "title:missing")
        assert "No matching tracks." in capsys.readouterr().out

    @pytest.mark.parametrize(
        "options,title",
        [
            ({}, "In a Silent Way"),
            ({"all_caps": True}, "ALL CAPS TITLE"),
            ({"all_lowercase": True}, "all lowercase title"),
        ],
    )
    def test_preview_handles_unchanged_values(self, capsys, options, title):
        item = self.add_item(title=title)
        with self.configure_plugin({"fields": ["title"], **options}):
            self.run_command("titlecase", "-p")
        output = capsys.readouterr().out
        assert "No changes." in output
        assert "->" not in output
        assert self.lib.get_item(item.id).title == title

    def test_preview_handles_multiple_changed_fields(self, capsys):
        self.add_item(
            title="new day", artist="some artist", album="first album"
        )
        with self.configure_plugin({"fields": ["album", "artist", "title"]}):
            self.run_command("titlecase", "-p")
        output = capsys.readouterr().out
        for field, original, proposed in [
            ("album", "first album", "First Album"),
            ("artist", "some artist", "Some Artist"),
            ("title", "new day", "New Day"),
        ]:
            assert f"{field}: {original!r} -> {proposed!r}" in output

    def test_preview_handles_list_fields(self, capsys):
        item = self.add_item(artists=["first artist", "the second artist"])
        with self.configure_plugin({"fields": ["artists"]}):
            self.run_command("titlecase", "-p")
        assert (
            "artists: ['first artist', 'the second artist'] -> "
            "['First Artist', 'The Second Artist']"
        ) in capsys.readouterr().out
        assert self.lib.get_item(item.id).artists == [
            "first artist",
            "the second artist",
        ]

    @pytest.mark.parametrize(
        "fields,values",
        [
            ([], {"title": "new day"}),
            (
                ["title", "artist", "artists"],
                {"title": "", "artist": "", "artists": []},
            ),
            (["year", "missing_field"], {"year": 2003}),
            (["title"], {"title": "123 — !!!"}),
        ],
    )
    def test_preview_handles_empty_and_non_string_fields(
        self, capsys, fields, values
    ):
        item = self.add_item(**values)
        before = dict(self.lib.get_item(item.id))
        with self.configure_plugin({"fields": fields}):
            self.run_command("titlecase", "-p")
        assert "No changes." in capsys.readouterr().out
        assert dict(self.lib.get_item(item.id)) == before

    def test_preview_ignores_missing_music_file(self, capsys):
        self.add_item(title="new day", path=self.temp_path / "missing.mp3")
        self.config["import"]["write"] = True
        with self.configure_plugin({"fields": ["title"]}):
            self.run_command("titlecase", "-p")
        assert "'new day' -> 'New Day'" in capsys.readouterr().out

    def test_preview_reports_invalid_query_without_writing(self):
        item = self.add_item(title="new day")
        with (
            self.configure_plugin({"fields": ["title"]}),
            patch.object(Item, "store") as store,
            patch.object(Item, "try_write") as try_write,
        ):
            with pytest.raises(InvalidQueryError):
                self.run_command("titlecase", "-p", "year:not-a-number")
        store.assert_not_called()
        try_write.assert_not_called()
        assert self.lib.get_item(item.id).title == "new day"

    @pytest.mark.parametrize("write_tags", [False, True])
    def test_normal_command_still_saves_and_respects_tag_write_config(
        self, write_tags
    ):
        item = self.add_item_fixture(title="new day", artist="some artist")
        item.write()
        self.config["import"]["write"] = write_tags
        with self.configure_plugin({"fields": ["title"]}):
            self.run_command("titlecase", f"id:{item.id}")
        stored = self.lib.get_item(item.id)
        assert stored.title == "New Day"
        assert stored.artist == "some artist"
        assert MediaFile(item.filepath).title == (
            "New Day" if write_tags else "new day"
        )

    def test_preview_then_normal_command(self):
        item = self.add_item(title="new day")
        self.config["import"]["write"] = False
        with self.configure_plugin({"fields": ["title"]}):
            self.run_command("titlecase", "-p")
            assert self.lib.get_item(item.id).title == "new day"
            self.run_command("titlecase")
        assert self.lib.get_item(item.id).title == "New Day"

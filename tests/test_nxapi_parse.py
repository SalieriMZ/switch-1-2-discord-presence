import pytest

from nso_rpc.config import Config
from nso_rpc.nxapi import Friend, NxapiClient, NxapiError, normalize_friend_id, parse_json_output
from nso_rpc.runtime import Runtime


def test_parse_json_plain():
    assert parse_json_output('{"a": 1}\n') == {"a": 1}


def test_parse_json_with_warning_prefix():
    out = "Warning: algo raro\nOtra línea\n[{\"nsaId\": \"x\"}]\n"
    assert parse_json_output(out) == [{"nsaId": "x"}]


def test_parse_json_multiline_pretty():
    out = 'aviso\n{\n  "a": [1, 2]\n}\n'
    assert parse_json_output(out) == {"a": [1, 2]}


def test_parse_json_garbage_raises():
    with pytest.raises(NxapiError):
        parse_json_output("nada que ver\n")


PLAYING = {
    "nsaId": "1a6e258084006b16",
    "name": "Seba",
    "imageUri": "https://cdn/img",
    "isFavoriteFriend": True,
    "presence": {"state": "PLAYING", "game": {"name": "Mario Kart World", "imageUri": "https://cdn/g"}},
}


def test_friend_from_coral_playing():
    f = Friend.from_coral(PLAYING)
    assert f == Friend(
        nsa_id="1a6e258084006b16", name="Seba", image_url="https://cdn/img",
        online=True, game_name="Mario Kart World", is_favorite=True,
    )
    assert f.status_text == "Jugando Mario Kart World"


def test_friend_from_coral_offline():
    f = Friend.from_coral({
        "nsaId": "b", "name": "X", "imageUri": "u", "isFavoriteFriend": False,
        "presence": {"state": "OFFLINE", "game": {}},
    })
    assert f.online is False and f.game_name is None
    assert f.status_text == "Desconectado"


def test_friend_online_without_game():
    f = Friend.from_coral({"nsaId": "c", "name": "Y", "presence": {"state": "ONLINE", "game": {}}})
    assert f.online is True and f.status_text == "En línea"


@pytest.mark.parametrize("raw,expected", [
    ("SW-1234-5678-9012", "1234-5678-9012"),
    (" sw-1234-5678-9012 ", "1234-5678-9012"),
    ("123456789012", "1234-5678-9012"),
    ("1234 5678 9012", "1234-5678-9012"),
    ("1A6E258084006B16", "1a6e258084006b16"),
])
def test_normalize_friend_id(raw, expected):
    assert normalize_friend_id(raw) == expected


def test_normalize_friend_id_invalid():
    with pytest.raises(NxapiError):
        normalize_friend_id("hola")


def test_presence_args_flags(tmp_path):
    rt = Runtime(tmp_path)
    client = NxapiClient(rt)
    args = client.presence_args("1a6e258084006b16", Config(update_interval=90, show_play_time=True))
    assert args[:4] == [str(rt.node), "--import", rt.discord_fix.as_uri(), str(rt.nxapi_bin)]
    assert args[4:] == [
        "nso", "presence", "--friend-nsaid", "1a6e258084006b16", "--update-interval", "90",
        "--show-play-time",
    ]
    args = client.presence_args("x", Config(show_inactive=True))
    assert "--show-inactive-presence" in args and "--show-play-time" not in args

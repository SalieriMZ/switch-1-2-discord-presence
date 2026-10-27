from nso_rpc.config import Config
from nso_rpc.onboarding import STEP_CHOOSE, wizard_start

BOT = {"id": "bot", "nickname": "Salieri2"}


def test_tutorial_done_skips_wizard():
    assert wizard_start(Config(tutorial_done=True), None) is None


def test_no_bot_starts_from_beginning():
    assert wizard_start(Config(), None) == 0


def test_bot_and_friend_already_set_skips_wizard():
    assert wizard_start(Config(friend_nsaid="1a6e258084006b16"), BOT) is None


def test_bot_without_friend_goes_to_choose_step():
    assert wizard_start(Config(), BOT) == STEP_CHOOSE

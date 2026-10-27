from nso_rpc.presence_state import PresenceMachine, State


def test_start_spawns():
    m = PresenceMachine()
    assert m.start() == "spawn"
    assert m.state is State.CONNECTING and m.attempt == 1


def test_start_twice_is_noop():
    m = PresenceMachine()
    m.start()
    assert m.start() is None


def test_connected_after_30s():
    m = PresenceMachine()
    m.start()
    m.tick(29.9)
    assert m.state is State.CONNECTING
    m.tick(30)
    assert m.state is State.CONNECTED


def test_exit_before_connect_retries():
    m = PresenceMachine()
    m.start()
    m.tick(5)
    assert m.exited(1) is None
    assert m.state is State.RETRYING and m.was_connected is False
    assert m.retry_in == 15
    m.tick_retry(14)
    assert m.retry_due() is None
    m.tick_retry(15)
    assert m.retry_due() == "spawn"
    assert m.state is State.CONNECTING and m.attempt == 2


def test_exit_after_connect_retries_and_counts():
    m = PresenceMachine()
    m.start()
    m.tick(31)
    m.exited(0)
    assert m.state is State.RETRYING and m.was_connected is True
    m.tick_retry(15)
    m.retry_due()
    m.tick(31)
    assert m.state is State.CONNECTED and m.attempt == 2


def test_stop_no_retry():
    m = PresenceMachine()
    m.start()
    assert m.stop() == "kill"
    m.exited(1)
    assert m.state is State.STOPPED
    m.tick_retry(100)
    assert m.retry_due() is None


def test_stop_while_retrying():
    m = PresenceMachine()
    m.start()
    m.exited(1)
    assert m.stop() is None
    assert m.state is State.STOPPED


def test_fatal_no_retry():
    m = PresenceMachine()
    m.start()
    m.fatal("sin motor")
    assert m.state is State.ERROR and m.error == "sin motor"
    m.exited(1)
    m.tick_retry(100)
    assert m.retry_due() is None and m.state is State.ERROR
    assert m.start() == "spawn"

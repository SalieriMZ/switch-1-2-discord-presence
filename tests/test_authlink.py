from nso_rpc.authlink import extract_auth_link

VALID = (
    "npf71b963c1b7b6d119://auth#session_token_code=eyJhbGciOiJIUzI1NiJ9.abc.def"
    "&state=mjxW0lyfjgiRv_7sZrj98&session_state=xyz"
)


def test_extract_valid_link():
    assert extract_auth_link(VALID) == VALID


def test_extract_link_inside_sentence():
    assert extract_auth_link(f'copiado: "{VALID}" listo') == VALID


def test_extract_ignores_random_text():
    assert extract_auth_link("hola https://example.com/auth#x=1") is None
    assert extract_auth_link("") is None


def test_extract_rejects_without_code():
    assert extract_auth_link("npf71b963c1b7b6d119://auth#state=abc") is None


def test_extract_reports_error_link_as_none():
    assert extract_auth_link("npf71b963c1b7b6d119://auth#error=access_denied&state=abc") is None

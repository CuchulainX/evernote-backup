import pytest

from evernote_backup.evernote_client_oauth import (
    CallbackHandler,
    EvernoteOAuthCallbackHandler,
    EvernoteOAuthClient,
    OAuthDeclinedError,
)


@pytest.fixture
def mock_evernote_oauth_client(mock_oauth_client):
    return EvernoteOAuthClient(
        backend="evernote", consumer_key="test_key", consumer_secret="test_sec"
    )


@pytest.mark.usefixtures("mock_oauth_http_server")
def test_get_auth_token(mock_oauth_client, mock_evernote_oauth_client):
    oauth_handler = EvernoteOAuthCallbackHandler(mock_evernote_oauth_client)
    oauth_handler.get_oauth_url()

    test_token = oauth_handler.wait_for_token()

    assert test_token == mock_oauth_client.fake_token


@pytest.mark.usefixtures("mock_oauth_http_server")
def test_get_auth_token_url(mock_oauth_client, mock_evernote_oauth_client):
    expected_url = "https://www.evernote.com/OAuth.action?oauth_token=fake_app.FFF"
    oauth_handler = EvernoteOAuthCallbackHandler(mock_evernote_oauth_client)

    url = oauth_handler.get_oauth_url()

    assert url == expected_url


@pytest.mark.usefixtures("mock_oauth_http_server")
def test_get_auth_token_declined(mock_oauth_client, mock_evernote_oauth_client):
    del mock_oauth_client.fake_callback_response["oauth_verifier"]

    oauth_handler = EvernoteOAuthCallbackHandler(mock_evernote_oauth_client)
    oauth_handler.get_oauth_url()

    with pytest.raises(OAuthDeclinedError):
        oauth_handler.wait_for_token()


def test_get_auth_token_interrupted(
    mock_oauth_client,
    mock_evernote_oauth_client,
    mocker,
):
    mocker.patch(
        "evernote_backup.evernote_client_oauth.StoppableHTTPServer.serve_forever"
    )
    mocker.patch("evernote_backup.evernote_client_oauth.StoppableHTTPServer.shutdown")
    mocker.patch(
        "evernote_backup.evernote_client_oauth.time.sleep",
        side_effect=KeyboardInterrupt,
    )

    oauth_handler = EvernoteOAuthCallbackHandler(mock_evernote_oauth_client)
    oauth_handler.get_oauth_url()

    with pytest.raises(KeyboardInterrupt):
        oauth_handler.wait_for_token()


def test_callback_handler_bad_url(mocker):
    mock_instance = mocker.MagicMock()
    mock_instance.path = "/fake_page"
    mock_instance.http_codes = CallbackHandler.http_codes

    CallbackHandler.do_GET(mock_instance)

    mock_instance.send_response.assert_called_once_with(
        CallbackHandler.http_codes["NOT FOUND"]
    )


def test_callback_handler(mocker):
    mock_instance = mocker.MagicMock()
    mock_instance.path = "/oauth_callback?test_param=test"
    mock_instance.http_codes = CallbackHandler.http_codes

    CallbackHandler.do_GET(mock_instance)

    assert mock_instance.server.callback_response == {"test_param": "test"}
    mock_instance.send_response.assert_called_once_with(
        CallbackHandler.http_codes["OK"]
    )

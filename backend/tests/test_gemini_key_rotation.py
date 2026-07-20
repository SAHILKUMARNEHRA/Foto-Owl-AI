from unittest.mock import MagicMock, patch
import pytest
import requests

from backend.utils.ollama import GeminiTextClient


def test_gemini_key_rotation_failover():
    client = GeminiTextClient(
        api_base_url="https://generativelanguage.googleapis.com/v1beta",
        api_key="key1,key2",
        model="gemini-2.0-flash-lite",
    )

    # First key gets 429 rate limit error, second key succeeds
    mock_resp_429 = MagicMock()
    mock_resp_429.status_code = 429
    mock_resp_429.text = "Quota exceeded"

    mock_resp_200 = MagicMock()
    mock_resp_200.status_code = 200
    mock_resp_200.json.return_value = {
        "candidates": [
            {"content": {"parts": [{"text": '{"result": "success"}'}]}}
        ]
    }

    err_429 = requests.HTTPError(response=mock_resp_429)

    with patch("requests.post") as mock_post:
        # Return 429 HTTPError for first call (key1), 200 OK for second call (key2)
        mock_post.side_effect = [err_429, mock_resp_200]

        res = client.invoke_json(system_prompt="sys", user_prompt="usr")
        assert res == {"result": "success"}
        assert mock_post.call_count == 2
        # Verify call 1 used key1 and call 2 used key2
        assert mock_post.call_args_list[0].kwargs["params"]["key"] == "key1"
        assert mock_post.call_args_list[1].kwargs["params"]["key"] == "key2"

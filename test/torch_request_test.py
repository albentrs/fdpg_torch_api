import base64
import unittest
import json
from unittest.mock import patch, mock_open, MagicMock
from fdpg_torch_api.torch_requests import load_json_file, query_to_base64, \
    extract_file_url, extract_patient_id  # Ersetze 'your_module' mit dem tatsächlichen Modulnamen


class torch_request_test(unittest.TestCase):

    @patch("builtins.open", new_callable=mock_open, read_data='{"key": "value"}')
    def test_load_valid_json(self, mock_file):
        """Tests the loading of a valid JSON file."""
        result = load_json_file("dummy.json")
        self.assertEqual(result, {"key": "value"})
        mock_file.assert_called_once_with("dummy.json", "r")

    @patch("builtins.open", new_callable=mock_open, read_data='')
    @patch("logging.getLogger")
    def test_load_empty_json(self, mock_logger, mock_file):
        """Tests the behavior of an empty JSON file."""
        with patch("json.load", return_value=None):
            result = load_json_file("dummy.json")
            self.assertIsNone(result)
            mock_logger.return_value.error.assert_called_once_with("Error to load the data of json file.")
            mock_file.assert_called_once_with("dummy.json", "r")

    @patch("builtins.open", side_effect=FileNotFoundError)
    def test_file_not_found(self, mock_file):
        """Tests the behavior if the file is not found."""
        result = load_json_file("non_existent.json")
        self.assertIsNone(result)

    @patch("builtins.open", new_callable=mock_open, read_data='invalid json')
    @patch("logging.getLogger")
    def test_invalid_json_format(self, mock_logger, mock_file):
        """Tests the behavior with invalid JSON format."""
        with patch("json.load", side_effect=json.JSONDecodeError("Expecting value", "", 0)):
            result = load_json_file("invalid.json")
            self.assertIsNone(result)
            mock_logger.return_value.error.assert_called()
            mock_file.assert_called_once_with("invalid.json", "r")

    def test_valid_json_to_base64(self):
        """Tests the conversion of a valid JSON object to Base64."""
        json_data = {"key": "value"}
        expected_base64 = base64.b64encode(json.dumps(json_data).encode("utf-8")).decode("utf-8")
        self.assertEqual(query_to_base64(json_data), expected_base64)

    def test_empty_json_to_base64(self):
        """Tests the conversion of an empty JSON object."""
        json_data = {}
        expected_base64 = base64.b64encode(json.dumps(json_data).encode("utf-8")).decode("utf-8")
        self.assertEqual(query_to_base64(json_data), expected_base64)

    def test_json_with_numbers_to_base64(self):
        """Tests the conversion of a JSON object with numbers."""
        json_data = {"num": 123, "float": 45.67}
        expected_base64 = base64.b64encode(json.dumps(json_data).encode("utf-8")).decode("utf-8")
        self.assertEqual(query_to_base64(json_data), expected_base64)

    def test_json_with_special_characters_to_base64(self):
        """Tests the conversion of a JSON object with special characters."""
        json_data = {"text": "äöüß€@!"}
        expected_base64 = base64.b64encode(json.dumps(json_data).encode("utf-8")).decode("utf-8")
        self.assertEqual(query_to_base64(json_data), expected_base64)

    @patch("os.getenv", return_value="http://localhost/7cc981e3-10dc-4e53-9489-e27666754af3")
    def test_extract_file_url(self, mock_getenv):
        """Tests the extraction and conversion of URLs."""
        torch_output = [
            {"url": "http://localhost/7cc981e3-10dc-4e53-9489-e27666754af3/01ae2a66-caeb-49ee-bda9-e7706af62483.ndjson"},
            {"url": "http://localhost/7cc981e3-10dc-4e53-9489-e27666754af3/059fb2a8-8534-4ad4-84e4-da34ef364758.ndjson"}
        ]
        expected_urls = [
            "http://localhost/7cc981e3-10dc-4e53-9489-e27666754af3/01ae2a66-caeb-49ee-bda9-e7706af62483.ndjson",
            "http://localhost/7cc981e3-10dc-4e53-9489-e27666754af3/059fb2a8-8534-4ad4-84e4-da34ef364758.ndjson"
        ]
        self.assertEqual(extract_file_url(torch_output), expected_urls)

    @patch("os.getenv", return_value="https://myserver.com")
    def test_extract_file_url_empty(self, mock_getenv):
        """Tests the behavior with empty input."""
        self.assertEqual(extract_file_url([]), [])

    @patch("os.getenv", return_value=None)
    def test_extract_file_url_no_env_var(self, mock_getenv):
        """Tests whether a ValueError is thrown if the environment variable is missing."""
        torch_output = [{"url": "http://localhost:80/path/to/file.ndjson"}]
        with self.assertRaises(ValueError) as context:
            extract_file_url(torch_output)

        # Optional: Ensure that the exception contains the correct message
        self.assertEqual(str(context.exception), "Error: Environment variable TORCH_NGINX_SERVER is not set!")

    @patch("requests.get")
    @patch("os.getenv", side_effect=lambda key:
    "True" if key == "TORCH_BASIC_AUTH" else
    "test_user" if key == "TORCH_USERNAME" else
    "test_pass" if key == "TORCH_PASSWORD" else None)
    def test_extract_patient_id_success(self, mock_getenv, mock_requests_get):
        """Tests the successful retrieval and extraction of patient IDs."""

        # Mocking the response object from requests.get
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = [
            json.dumps({"id": "VHF00061"}).encode("utf-8"),
            json.dumps({"id": "VHF00063"}).encode("utf-8")
        ]
        mock_requests_get.return_value = mock_response

        # Call the function under test
        result = extract_patient_id(
            "http://localhost/23d4127e-5edd-4b94-8d9f-ff05e1674dac/d28c2398-ce1e-452e-8a2a-4f79dfaf0986.ndjson")

        # Assert that the result matches the expected list of UUIDs
        self.assertEqual(result, ["VHF00061", "VHF00063"])

    @patch("requests.get")
    def test_extract_patient_id_failure(self, mock_requests_get):
        """Tests the behavior in the event of a failed call."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_requests_get.return_value = mock_response

        result = extract_patient_id("http://localhost/7cc981e3-10dc-4e53-9489-e27666754af3/01ae2a66-caeb-49ee-bda9-e7706af62483.ndjson")
        self.assertIsNone(result)

    @patch("requests.get")
    @patch("os.getenv", return_value=None)
    def test_extract_patient_id_missing_env_vars(self, mock_getenv, mock_requests_get):
        """Tests the behavior when environment variables are missing."""
        with self.assertRaises(ValueError) as context:  # Expecting ValueError now
            extract_patient_id(
                "http://localhost/7cc981e3-10dc-4e53-9489-e27666754af3/01ae2a66-caeb-49ee-bda9-e7706af62483.ndjson")
        # Optional: Ensure that the exception contains the correct message
        self.assertEqual(str(context.exception),
                         "Error: Environment variables TORCH_USERNAME or TORCH_PASSWORD missing")


if __name__ == "__main__":
    unittest.main()

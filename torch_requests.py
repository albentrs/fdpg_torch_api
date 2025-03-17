import base64
import urllib3
import os
import json
from dotenv import load_dotenv
import logging
import requests
from requests.auth import HTTPBasicAuth

# Logging configuration
logging.basicConfig(
    level=logging.INFO,  # Log-Level: DEBUG, INFO, WARNING, ERROR, CRITICAL
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def load_json_file(jsonfile):

    try:
        # Load JSON schema from file
        with open(jsonfile, "r") as f:
            json_data = json.load(f)
            if json_data is None:
                logger.error("Error to load the data of json file.")
                return None
            else:
                return json_data
    except FileNotFoundError:
        logger.error(f"File {jsonfile} not found.")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON format in {jsonfile}: {e}")
        return None


def query_to_base64(json_string):
    # Convert JSON string to Base64
    json_str_encoded = json.dumps(json_string).encode('utf-8')  # JSON to UTF-8 encoded bytes
    base64_encoded = base64.b64encode(json_str_encoded).decode('utf-8')  # Base64 encode and convert to string
    return base64_encoded


# input the response from methode extracteLocation, to extracte the urls
def extract_file_url(torch_output):
    load_dotenv()
    locations = []
    nginx_server_url = os.getenv("TORCH_NGINX_SERVER")
    torch_url = os.getenv("TORCH_BASE_URL")
    if nginx_server_url is None:
        raise ValueError("Error: Environment variable TORCH_NGINX_SERVER is not set!")
    if torch_url is None:
        raise ValueError("Error: Environment variable TORCH_BASE_URL is not set!")

    for elem in torch_output:
        # extracte the ndjson url
        elem_url = elem.get("url")
        # if is torch server url in bundle
        elem_url_new = elem_url.replace(torch_url, nginx_server_url)
        locations.append(elem_url_new)
    return locations


def extract_patient_id(ndjson_file_url):
    load_dotenv()
    bais_auth_torch = os.getenv("TORCH_BASIC_AUTH")
    if bais_auth_torch is None:
        raise ValueError("Error: Environment variables TORCH_USERNAME or TORCH_PASSWORD missing")
    uuid = []
    headers = {"Accept": "application/x-ndjson"}

    #  Please comment out this line if you are using https
    urllib3.disable_warnings()

    if bais_auth_torch == "True":
        username = os.getenv("TORCH_USERNAME")
        password = os.getenv("TORCH_PASSWORD")

        # If the user name or password is missing, cancel immediately
        if username is None or password is None:
            raise ValueError("Error: Environment variables TORCH_USERNAME or TORCH_PASSWORD missing")

        response = requests.get(ndjson_file_url, headers=headers,
                                auth=HTTPBasicAuth(username, password),
                                verify=False)
    else:
        response = requests.get(ndjson_file_url, headers=headers, verify=False)
    if response.status_code == 200:
        for line in response.iter_lines():
            if line:  # empty line ignor
                data = json.loads(line)
                uuid.append(data['id'])  # extract the id from each JSON-line
        return uuid
    else:
        print("Error:", response.status_code, response.text)
        return None


def create_torch_request(payload_torch):
    load_dotenv()

    header = {
        "Content-Type": "application/fhir+json"
    }

    torch_url = os.getenv("TORCH_BASE_URL") + "/fhir/$extract-data"
    #  Please comment out this line if you are using https
    urllib3.disable_warnings()

    if os.getenv("TORCH_BASIC_AUTH") == "True":
        torch_response = requests.post(torch_url, headers=header,
                                       auth=HTTPBasicAuth(os.getenv("TORCH_USERNAME"), os.getenv("TORCH_PASSWORD")),
                                       json=payload_torch, verify=False)
    else:
        torch_response = requests.post(torch_url, headers=header, verify=False)

    if torch_response.status_code == 200 or torch_response.status_code == 201 or torch_response.status_code == 202:
        return torch_response.headers['Content-Location'].replace("/fhir/__status/", '')
    else:
        logger.info("status_code: " + str(torch_response.status_code))
        return torch_response.status_code


def extract_location(responseTorchLocation):
    load_dotenv()
    torchUrl = os.getenv("TORCH_BASE_URL") + f"/fhir/__status/{responseTorchLocation}"

    # Please comment out this line if you are using https
    urllib3.disable_warnings()

    if os.getenv("TORCH_BASIC_AUTH") == "True":
        torch_response = requests.get(torchUrl,
                                      auth=HTTPBasicAuth(os.getenv("TORCH_USERNAME"), os.getenv("TORCH_PASSWORD")),
                                      verify=False)
    else:
        torch_response = requests.get(torchUrl,
                                      verify=False)
    if torch_response.status_code == 200:
        # torch_response.json()["output"] is an array of ndjson files
        locationUrls = extract_file_url(torch_response.json()["output"])
        return True, locationUrls
    elif torch_response.status_code == 202:
        return False, {"output": "request still processing on torch side"}
    if torch_response.status_code > 200:
        return False, {"error code": f"{torch_response.status_code}"}

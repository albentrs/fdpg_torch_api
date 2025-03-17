import os
from fastapi import FastAPI, HTTPException
from typing import Dict, Any
from jsonschema import validate, ValidationError
import torch_requests
from dotenv import load_dotenv

app = FastAPI()
load_dotenv()


@app.post("/api/data/")
async def push_json(data: Dict[str, Any]):
    try:
        # SQ JSON schema
        schema = torch_requests.load_json_file(r"resources/jsonschema.json")
        # Muster to create json file to extract the patient id (FDPG JSON sq + chosen fields)
        torchQueryMuster = torch_requests.load_json_file(r"resources/torchQuery.json")
        # change the groupReference in the muster
        torchQueryMuster['dataExtraction']['attributeGroups'][0]['groupReference'] = os.getenv('FDPG_GROUP_REFERENCE')
        # torch request muster
        torchRequestBody = torch_requests.load_json_file(r"resources/torchRequestBody.json")
        # JSON validieren
        validate(instance=data, schema=schema)
        # replace the cohort definition with payload
        torchQueryMuster["cohortDefinition"] = data
        # coding in base 64
        json_string_base64 = torch_requests.query_to_base64(torchQueryMuster)
        # build the torch request payload
        torchRequestBody["parameter"][0]["valueBase64Binary"] = json_string_base64
        # create torch request
        responseTorchLocation = torch_requests.create_torch_request(torchRequestBody)
        return responseTorchLocation
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {e.message}")


@app.get("/api/data/{location}")
def get_uuids(location: str):
    uuids = []
    # result is a array from ndjson files, if the request was successfully
    torchResponseStatus, result = torch_requests.extract_location(location)
    # torch response with 200 and the pressing is finish
    if torchResponseStatus:
        for ndjsonUrl in result:
            # extracte the uuid for one file and add it in uuids as array
            uuids.extend(torch_requests.extract_patient_id(ndjsonUrl))  # one array
        return uuids
    else:
        return result

# API to extracte Patient IDs from torch
The API receives the request Feasibility Portal Cohort SQ as a Json Pyaload and returns the corresponding patient IDs.   
This process is divided into two requests:
1. POST : to post the SQ of FDPG cohort to Torch. The response is location on torch, it will be used to later obtain the patient IDs.
```sh
curl --location 'http://localhost/api/data/' \
--header 'Content-Type: application/json' \
--data '{
    "version": "http://to_be_decided.com/draft-1/schema#",
    "display": "Ausgewählte Merkmale",
    "inclusionCriteria": [
        [
            {
                "termCodes": [
                    {
                        "code": "263495000",
                        "system": "http://snomed.info/sct",
                        "display": "Geschlecht"
                    }
                ],
                "context": {
                    "code": "Patient",
                    "system": "fdpg.mii.cds",
                    "version": "1.0.0",
                    "display": "Patient"
                },
                "valueFilter": {
                    "selectedConcepts": [
                        {
                            "code": "male",
                            "display": "Male",
                            "system": "http://hl7.org/fhir/administrative-gender"
                        }
                    ],
                    "type": "concept"
                }
            }
        ]
    ]
}'
```
The response:
```sh
"23d4127e-5edd-4b94-8d9f-ff05e1674dac"
```

2. GET  : to obtain the Patient IDs from Torch with location 
```sh
curl --location 'http://localhost/api/data/23d4127e-5edd-4b94-8d9f-ff05e1674dac'
```
The response:
```sh
 [
    "VHF01155",
    "VHF01034",
    ... 
 ]
```
## Requirements
- FastAPI
- Torch server
- docker
- docker-compose


## RUN
To execute the API, run the following command.
```sh
python -m uvicorn main:app --reload 
```
## Docker
This api can be executed also as a Docker container 
```sh
docker-compose up -d 
```

## Environment Variables

| Name                 | Standard                                                                                       | necessary | Beschreibung                                       |
|:---------------------|:-----------------------------------------------------------------------------------------------|-----------|:---------------------------------------------------|
| FDPG_SQ_JSON_SCHEMA  | resources/jsonschema.json                                                                      | Ja        | SQ JSON schema file                                |
| FDPG_GROUP_REFERENCE | https://www.medizininformatik-initiative.de/fhir/core/modul-person/StructureDefinition/Patient | Ja        | referenz in sq if there is deviation               |
| TORCH_BASE_URL       | ""                                                                                             | Ja        | torch server url                                   |
| TORCH_NGINX_SERVER   | ""                                                                                             | Ja        | url nginx rev-prosy of torch if there is deviation |
| TORCH_BASIC_AUTH     | False                                                                                          | Ja        | True or False if it used                           |
| TORCH_USERNAME       | ""                                                                                             |           | username if there is basic authentication          |
| TORCH_PASSWORD       | ""                                                                                             |           | password if there is basic authentication          |

## Note
if you want to use it in a productive environment, please replace all “verify=False” with “verify=path to certificates” and comment out this line “urllib3.disable_warnings()” if you use https.
# Jira Ticket Creation
This function creates Jira tickets based on the JSON message it gets.

## Setup
1. Make sure a ```config.py``` file exists within the directory, based on the [config.py.example](config.py.example), with the correct configuration:
    ~~~
    EPICS = A dictionary that links the category field of the message to a Jira epic
    DUE_DATE_BOOL = A dictionary containing booleans that links the category field of the message to whether a due date should be set
    ~~~
2. Make sure the following variables are present in the environment:
    ~~~
    JIRA_BOARD = the Jira board number
    JIRA_PROJECT = the name of the Jira project it has to make the tickets in
    JIRA_PROJECTS = the name of the Jira projects it has to look to for already existing tickets
    JIRA_SECRET_ID = the key in Google Cloud Platform (GCP) secret manager where the key for the Jira user can be found
    JIRA_SERVER = the URL to the Jira server
    JIRA_USER = the Jira user that will create the tickets
    PROJECT = the GCP project where the secret manager can be found
    ~~~
3. Deploy the function with help of the [cloudbuild.example.yaml](cloudbuild.example.yaml) to the Google Cloud Platform.

## Incoming message
To make sure the function works according to the way it was intented, the incoming messages from a Pub/Sub Topic must have the following structure based on the [company-data structure](https://vwt-digital.github.io/project-company-data.github.io/v1.1/schema):
~~~JSON
{
  "gobits": [ ],
  "issue": {
    "title": "",
    "category": "",
    "payload": {
        "field_1": "value_1",
        "field_2": "value_2",
        "field_etcetera": "value_etcetera"
    }
  }
}
~~~
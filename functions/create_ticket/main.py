import base64
import os
import json
import logging

import utils
import secretmanager
import atlassian

logging.basicConfig(level=logging.INFO, format="%(levelname)7s: %(message)s")


def handler(request):
    """
    When triggered, this function receives a request. The requests holds
    the error information. The error information is grouped and tickets
    are created in the current sprint.
    """
    logging.info(
        f"x01: stepping into handler with: {request.data.decode('utf-8')}")

    jira_user = os.environ["JIRA_USER"]
    jira_server = os.environ["JIRA_SERVER"]
    jira_project = os.environ["JIRA_PROJECT"]
    jira_projects = os.environ["JIRA_PROJECTS"]
    jira_board = os.environ["JIRA_BOARD"]
    jira_api_key = secretmanager.get_secret(
        os.environ["X_GOOGLE_GCP_PROJECT"],
        os.environ["JIRA_SECRET_ID"])

    client = atlassian.jira_init(jira_user, jira_api_key, jira_server)

    filter_prefix = "status!=Done AND status!=Cancelled AND type=Bug AND project="
    projects = [filter_prefix + project for project in jira_projects.split('+')]

    jql = " OR ".join(projects)
    titles = atlassian.list_issue_titles(client, jql)
    sprint_id = atlassian.get_current_sprint(client, jira_board)

    logging.info(
        f"Finding errors for sprint {sprint_id} of project [{jira_projects}]...")

    # Extract data from request
    envelope = json.loads(request.data.decode('utf-8'))
    payload = base64.b64decode(envelope['message']['data'])

    grouped = utils.group_by(
        json.loads(payload),
        "project_id", "resource", "type")

    for tub, data in grouped:
        title = f"Fix bug in {tub[0]} {tub[1]}"
        description = "\n".join(json.dumps(item) for item in list(data)[:5])
        if title not in titles:
            logging.info(f"Creating jira ticket: {title}")
            issue = atlassian.create_issue(
                client=client,
                project=jira_project,
                title=title,
                description=description)

            atlassian.add_to_sprint(client, sprint_id, issue.key)

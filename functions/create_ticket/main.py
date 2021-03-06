import base64
import json
import logging
import os

import atlassian
import secretmanager

logging.basicConfig(level=logging.INFO, format="%(levelname)7s: %(message)s")


def handler(request):
    """
    When triggered, this function receives a request. The requests holds
    the error information. The error information is grouped and tickets
    are created in the current sprint.
    """
    logging.info(f"x01: stepping into handler with: {request.data.decode('utf-8')}")

    jira_user = os.environ["JIRA_USER"]
    jira_server = os.environ["JIRA_SERVER"]
    jira_project = os.environ["JIRA_PROJECT"]
    jira_projects = os.environ["JIRA_PROJECTS"]
    jira_board = os.environ["JIRA_BOARD"]
    jira_api_key = secretmanager.get_secret(
        os.environ["PROJECT"], os.environ["JIRA_SECRET_ID"]
    )

    client = atlassian.jira_init(jira_user, jira_api_key, jira_server)

    filter_prefix = 'status!=Done AND status!="For Review" AND status!=Cancelled AND type=Bug AND project='
    projects = [filter_prefix + project for project in jira_projects.split("+")]

    jql = " OR ".join(projects)
    titles = atlassian.list_issue_titles(client, jql)
    sprint_id = atlassian.get_current_sprint(client, jira_board, jira_project)

    logging.info(
        f"Finding errors for sprint {sprint_id} of project [{jira_projects}]..."
    )

    # Extract data from request
    envelope = json.loads(request.data.decode("utf-8"))
    payload = json.loads(base64.b64decode(envelope["message"]["data"]))

    title = payload["issue"]["title"]
    logging.info(title)
    if title not in titles:
        logging.info(f"Creating jira ticket: {title}")
        issue = atlassian.create_issue(
            client=client,
            project=jira_project,
            title=title,
            description=str(payload["issue"]["payload"]),
        )

        atlassian.add_to_sprint(client, sprint_id, issue.key)
    else:
        logging.info(f"Not creating: {title}, duplicate found.")

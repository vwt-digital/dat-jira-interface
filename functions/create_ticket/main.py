import base64
import json
import logging
import os
from datetime import date, timedelta

import atlassian
import secretmanager
from config import DUE_DATE_BOOL, EPICS

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
    logging.info(f"Title: {title}")
    if title not in titles:
        logging.info(f"Creating jira ticket: {title}")
        issue = atlassian.create_issue(
            client=client,
            project=jira_project,
            title=title,
            description=str(payload["issue"]["payload"]),
        )

        # Add comment to jira ticket
        if payload["issue"]["comment"]:
            logging.info(f"Adding comment to issue: {title}")
            atlassian.add_comment(client, issue, payload["issue"]["comment"])

        atlassian.add_to_sprint(client, sprint_id, issue.key)
        issue_category = payload["issue"].get("category")
        if issue_category:
            epic_id = EPICS.get(issue_category)
            if epic_id:
                atlassian.add_to_epic(client, epic_id, issue.key)
            else:
                logging.error(
                    f"Category '{issue_category}' is given in message but cannot be found in EPICS dict in config."
                )
            due_date_bool = DUE_DATE_BOOL.get(issue_category)
            if due_date_bool:
                # Get today's date
                today = date.today()
                # Add a week
                week = timedelta(days=7)
                due_date = today + week
                # Set due date
                due_date_string = due_date.strftime("%Y-%m-%d")
                atlassian.set_due_date(client, issue.key, due_date_string)
    else:
        logging.info("Jira ticket found with same name, checking comments...")
        # Check for comments here
        if payload["issue"]["comment"]:
            comment = payload["issue"]["comment"]
            add_comment(client, comment, title, jira_projects)
        else:
            logging.info(f"Not creating: {title}, duplicate found without comment.")


def add_comment(client, comment, title, jira_projects):
    jql_title_list = title.split(":")
    jql_title_list[-1] = jql_title_list[-1].replace("-", " ")
    jql_title = ":".join(jql_title_list)
    # Get issues with title
    jql_prefix_titles = (
        f"type = Bug AND status != Done AND status != Cancelled "
        f'AND text ~ "{jql_title}" '
        "AND project = "
    )
    projects_titles = [
        jql_prefix_titles + project for project in jira_projects.split("+")
    ]
    jql_titles = " OR ".join(projects_titles)
    jql_titles = f"{jql_titles} ORDER BY priority DESC"
    issues = atlassian.list_issues(client, jql_titles)
    # For every issue with this title
    for issue in issues:
        # Get comments of issues
        issue_id = atlassian.get_issue_id(issue)
        issue_comment_ids = atlassian.list_issue_comment_ids(client, issue_id)
        comment_not_yet_exists = True
        for comment_id in issue_comment_ids:
            # Check if the comment without where to find it does not yet exist
            comment_body = atlassian.get_comment_body(client, issue, comment_id)
            if repr(comment_body) == repr(comment):
                logging.info(f"Identical comments found for issue: {title}")
                comment_not_yet_exists = False
                break
        if comment_not_yet_exists:
            logging.info(f"Adding comment to jira ticket: {issue}")
            # Add comment to jira ticket
            atlassian.add_comment(client, issue_id, comment)
        else:
            logging.info(f"Not update jira ticket, identical comment found: {title}")

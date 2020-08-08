import logging
import time
import typing

import jira


def get_jira_issues(
        client: jira.JIRA, project: str, query: str, max_results: int,
        start_date: str, stop_date: str, logger: logging.Logger) -> typing.List[jira.Issue]:
    """
    Query the specified JIRA Project for issues that match JQL query. The routine will measure the time required
    to gather the data, so the processing performance can be monitored and improved as needed.

    Args:
        client: Instantiated Jira Client
        project: Target Jira project
        query: JQL query
        max_results: Maximum number of results to return.
        start_date: Start date of query (CCYY-MM-DD formatted string)
        stop_date: Stop date of query (CCYY-MM-DD formatted string)
        logger: Logging facility

    Returns:
        List of Jira Issues (jira.Issue)

    """
    start_msg = (f"- Querying JIRA '{project}' project for all issues in 'To Do' in "
                 f"range of '{start_date}' to '{stop_date}'.")
    print(start_msg, end='', flush=True)
    logger.info(start_msg)

    start_time = time.perf_counter()
    results = client.search_issues(jql_str=query, maxResults=max_results,
                                   fields='key, description, attachment, summary')

    stop_msg = f" --> Complete. {len(results)} found. ({time.perf_counter() - start_time:0.2f} secs)"
    print(stop_msg)
    logger.info(stop_msg)

    return results


def connect_to_jira(url: str, user: str, password: str, logger: logging.Logger) -> jira.JIRA:
    """
    Connects to Jira; tracks timing to connect.

    Args:
        url: URL to connect to JIRA
        user: Username
        password: Password
        logger: Logging facility

    Returns:
        Instantiated JIRA Client

    """
    start_msg = "- Connecting to Jira... "
    print(start_msg, end='', flush=True)
    logger.info(start_msg)
    start_time = time.perf_counter()
    client = jira.JIRA(url, basic_auth=(user, password))
    stop_msg = f"Connected. ({time.perf_counter() - start_time:0.2f} secs)"
    print(stop_msg)
    logger.info(stop_msg)
    return client

import argparse
import logging
import time

from defects_list import Defects
from excel_reports import ExcelWorkbook
from md_jira import connect_to_jira, get_jira_issues


class CommandLineOptions:
    """ The utility command line arguments. """

    def __init__(self):
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument('user', help="Username (for Jira Access)")
        self.parser.add_argument('pswd', help="Password (for Jira Access)")
        self.parser.add_argument('start', help="Start of date range for query. Format: CCYY-MM-DD")
        self.parser.add_argument('stop', help="Stop of date range for query. Format: CCYY-MM-DD")
        self.parser.add_argument('-m', '--max_results', default=DEFAULT_MAX_RESULTS,
                                 help=f"Max number of records to return. Default: {DEFAULT_MAX_RESULTS}")
        self.parser.add_argument('-d', '--debug', action='store_true', default=False,
                                 help="Enable debugging. Default: False")

        self.args = self.parser.parse_args()

    def get_args(self):
        return self.args


def setup_logging(log_filename: str, logging_level=logging.INFO) -> logging.Logger:
    """
    Set up the logger (filename, msg preamble format, timestamps, etc.) for the tool.

    :param log_filename: Name of file to write log msgs to...
    :param logging_level: logging level (default=logging.INFO)

    :return:
        Instance of logging.Logger()

    """
    logging.basicConfig(filename=log_filename,
                        format='%(asctime)s : [%(levelname)s]: [%(name)s]: %(message)s',
                        datefmt='%m%d%YT%H:%M:%S',
                        level=logging_level)

    return logging.getLogger(__name__)


if __name__ == '__main__':

    # Default values for accessing JIRA
    DEFAULT_MAX_RESULTS = 500
    PROJECT = 'CBR'
    STATUS = ['"To Do"']
    URL = 'https://jira.pclender.com'

    # Get the CLI arguments
    cli = CommandLineOptions()
    args = cli.get_args()

    # Build the JQL query.
    JQL = (f'project = {PROJECT} '
           f'AND status in ({",".join(STATUS)}) '
           f'AND created >= {args.start} '
           f'AND created <= {args.stop} '
           f'ORDER BY priority DESC, updated DESC')

    filename = f"{PROJECT}_issues_{args.start}_to_{args.stop}"
    xlsx_name = f"{filename}.{ExcelWorkbook.EXTENSION}"
    log_name = f"{filename}.log"

    log_level = logging.DEBUG if args.debug else logging.INFO
    log = setup_logging(log_filename=log_name, logging_level=log_level)
    log.info("----------------- START -----------------")

    # Connect to Jira and query defects matching criteria
    jira_client = connect_to_jira(url=URL, user=args.user, password=args.pswd, logger=log)
    jira_issues = get_jira_issues(client=jira_client, project=PROJECT, query=JQL, max_results=args.max_results,
                                  start_date=args.start, stop_date=args.stop, logger=log)

    # Process and categorize the list of Jira defects
    start_processing = time.perf_counter()
    issues = Defects(jira_issues)
    msg = (f"- Parsing of returned defects and attachments complete. "
           f"({time.perf_counter() - start_processing:0.2f} secs)")
    log.info(msg)
    print(msg)

    # Record results to Excel spreadsheet.
    start_processing = time.perf_counter()
    xlsx = ExcelWorkbook(workbook_name=xlsx_name)
    xlsx.build_summary_sheet(issues.tally_defect_types())
    xlsx.build_detailed_table(issues.build_reporting_dict())
    xlsx.save()
    msg = f"- XLSX processing complete. ({time.perf_counter() - start_processing:0.2f} secs)"
    log.info(msg)
    print(msg)

    # Display summary of the exceptions and corresponding issue counts. This is not logged.
    total_count = 0
    print(f"\nResults:")
    for exc_type, count in sorted(issues.tally_defect_types().items(), key=lambda x: x[1], reverse=True):
        print(f"- '{exc_type}': {count}")
        total_count += count
    print(f"Total Issue Count: {total_count}")

    log.info("----------------- STOP -----------------")

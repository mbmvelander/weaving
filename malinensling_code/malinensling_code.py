#!/usr/bin/env python

import argparse
from enum import IntEnum
from strenum import StrEnum
import time
import os
import sys
import uuid
from datetime import datetime
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials


# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']


class Wrap(StrEnum):
    SNOWY_SUNRISE = "Snowy Sunrise"
    MISTY_MORNING = "Misty Morning"
    HARVEST_MOON = "Harvest Moon"
    NEW_MOON = "New Moon"
    AMBER_PEBBLES = "Amber Pebbles"
    AMETHYST_PEBBLES = "Amethyst Pebbles"
    JADE_PEBBLES = "Jade Pebbles"
    ONYX_PEBBLES = "Onyx Pebbles"


class RowIndex(IntEnum):
    CODE = 0
    T_CREATED = 1
    DATE_CREATED = 2
    NAME = 3
    SCOPE = 4
    PERCENTAGE = 5
    T_USED = 6
    DATE_USED = 7


class GoogleSheet:
    def __init__(self, sheet_id, sheet_tab="Codes", token_file="token.json", credentials_file="credentials.json", verbose_level=0, quiet=False):
        self.sheet_id = sheet_id
        self.sheet_tab = sheet_tab
        self.token_file = token_file
        self.credentials_file = credentials_file
        self.verbose_level = verbose_level
        self.quiet = quiet
        self.credentials = None
        self.sheet = None
    
    def login(self):
        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(self.token_file, 'w') as token:
                token.write(creds.to_json())
        self.credentials = creds

    def connect_to_sheet_service(self):
        if not self.credentials:
            self.login()

        service = build('sheets', 'v4', credentials=self.credentials)

        # Call the Sheets API
        self.sheet = service.spreadsheets()
    
    def create_new_code(self, name="", scope=[], percentage=10):
        if not self.sheet:
            self.connect_to_sheet_service()

        current_data = self.sheet.values().get(spreadsheetId=self.sheet_id,
                                               range=self.sheet_tab).execute()
        current_codes = [row[RowIndex.CODE] for row in current_data.get("values", [])]
        if self.verbose_level:
            print("Existing codes: ", ", ".join(current_codes))

        while True:
            new_code = str(uuid.uuid4())[:8].lower()
            if new_code in current_codes:
                if self.verbose_level:
                    print(f"Code rejected since it already exists; code={new_code}; codes={','.join(current_codes)}")
                continue
            break

        values = [""] * len(list(RowIndex))
        values[RowIndex.CODE] = new_code
        values[RowIndex.T_CREATED] = int(time.time())
        values[RowIndex.DATE_CREATED] = self.date_formula(RowIndex.T_CREATED) if values[RowIndex.T_CREATED] else ""
        values[RowIndex.NAME] = name
        values[RowIndex.SCOPE] = ",".join(scope)
        values[RowIndex.PERCENTAGE] = percentage
        values[RowIndex.T_USED] = ""
        values[RowIndex.DATE_USED] = self.date_formula(RowIndex.T_USED) if values[RowIndex.T_USED] else ""

        _ = self.sheet.values().append(spreadsheetId=self.sheet_id,
                                       body={"values": [values]},
                                       range=self.sheet_tab,
                                       valueInputOption="USER_ENTERED").execute()
        if self.verbose_level:
            print("Row added: ", values)

        if not self.quiet:
            print(f"New code created for {values[RowIndex.NAME]}: {values[RowIndex.CODE]}")
            self._print_message_to_send(values[RowIndex.NAME], values[RowIndex.CODE], values[RowIndex.SCOPE].split(","), values[RowIndex.PERCENTAGE])

        return new_code

    @staticmethod
    def date_formula(index: RowIndex):
        return f"=(INDIRECT(CONCATENATE(\"{chr(index+65)}\",ROW()))/86400)+DATE(1970,1,1)"
    
    @staticmethod
    def _print_message_to_send(name, code, scope, percentage):
        first_name = name.split()[0]
        message = f"Hi {first_name},\n\n"
        message += "Thank you for the very useful feedback you gave me in the recent malinensling Expedition! "
        message += "Here is the discount code I promised, which you can use if and when the wrap(s) "
        message += "and associated accessories come up for sale.\n\n"
        message += f"Code: {code}\n"
        message += f"Valid for: {', '.join(scope)}\n"
        message += f"Discount: {percentage}%\n\n"
        message += "Note that this discount code is personal and only valid once.\n\n\n"
        message += "Cheers,\n"
        message += "Malin"
        print("\nMESSAGE TEMPLATE:")
        print(message + "\n")


    def use_code(self, code, name="", wraps=[]):
        if not self.sheet:
            self.connect_to_sheet_service()

        current_data = self.sheet.values().get(spreadsheetId=self.sheet_id,
                                               range=self.sheet_tab).execute().get("values", [])
        current_codes = [row[RowIndex.CODE].lower() for row in current_data]
        if self.verbose_level:
            print("Current codes: ", current_codes)

        code_lower = code.lower()
        if code_lower not in current_codes:
            print(f"Code {code} doesn't exist")
            sys.exit(1)
        
        code_index = current_codes.index(code_lower)
        code_info = current_data[code_index]
        if self.verbose_level:
            print("Code info: ", code_info)

        if len(code_info) > RowIndex.T_USED:
            if code_info[RowIndex.T_USED]:
                date = datetime.fromtimestamp(int(code_info[RowIndex.T_USED])).strftime("%Y-%m-%d %H:%M:%S")
                print(f"Code {code} was already used on {date}")
                sys.exit(1)

        code_name = code_info[RowIndex.NAME]
        if name and name != code_name:
            print(f"Code {code} was not issued to {name} but to {code_name}")
            sys.exit(1)

        scope = code_info[RowIndex.SCOPE]  # No scope means all wraps are covered
        if wraps and scope:
            scope = [Wrap(wrap) for wrap in code_info[RowIndex.SCOPE].split(",")]
            not_covered = []
            for wrap in wraps:
                if wrap not in scope:
                    not_covered.append(wrap)
            if not_covered:
                wraps_string_first_part = ", ".join(not_covered[:-1])
                if wraps_string_first_part:
                    wrap_string = " or ".join([wraps_string_first_part, not_covered[-1]])
                else:
                    wrap_string = not_covered[-1]
                print(f"Code {code} does not cover wrap {wrap_string}")
                print(f"Wraps covered: {', '.join(scope)}")
                sys.exit(1)

        self._print_code_info(code_info)

        ans = input("Do you want to use this code? [y/N] ") or "n"
        if not ans.lower() in ["y", "yes"]:
            output_string = "Code was not used"
            if ans.lower() in ["n", "no"]:
                print("Ok, " + output_string.lower())
                sys.exit(0)
            print(f"Response {ans} not recognised")
            print(output_string)
            sys.exit(1)
        
        self._use_code(code_info, code_index+1)

    @staticmethod
    def _print_code_info(code_info):
        date = datetime.fromtimestamp(int(code_info[RowIndex.T_CREATED])).strftime("%Y-%m-%d %H:%M:%S")
        wraps = code_info[RowIndex.SCOPE].replace(',', ', ')
        if not wraps:
            wraps = "all"
        message = "\nVALID CODE FOUND:\n"
        message += f"Code:     {code_info[RowIndex.CODE]}\n"
        message += f"Name:     {code_info[RowIndex.NAME]}\n"
        message += f"Created:  {date}\n"
        message += f"Wraps:    {wraps}\n"
        message += f"Discount: {code_info[RowIndex.PERCENTAGE]}%\n"
        print(message)
    
    def _use_code(self, code_info, row_index):
        if len(code_info) < RowIndex.DATE_USED + 1:
            code_info += [""] * (RowIndex.DATE_USED - len(code_info) + 1)
        code_info[RowIndex.T_USED] = int(time.time())
        code_info[RowIndex.DATE_USED] = self.date_formula(RowIndex.T_USED)
        range = self.sheet_tab + f"!A{row_index}:{chr(len(RowIndex)-1+65)}{row_index}"
        if self.verbose_level:
            print(f"Updating {range} with info={code_info}")
        self.sheet.values().update(spreadsheetId=self.sheet_id,
                                   body={"values": [code_info]},
                                   range=range,
                                   valueInputOption="USER_ENTERED").execute()
        if not self.quiet:
            date = datetime.fromtimestamp(int(code_info[RowIndex.T_USED])).strftime("%Y-%m-%d %H:%M:%S")
            print(f"Code {code_info[RowIndex.CODE]} was used on {date}")

def main(command_line=None):
    sheet_env_variable_name = "GOOGLE_SHEET_ID"
    main_parser = argparse.ArgumentParser(description="Handle malinensling discount codes",
                                          formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    main_parser.add_argument(
        "-s",
        "--sheet_id",
        default="$" + sheet_env_variable_name,
        help="ID of Google sheet to interact with"
    )
    main_parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0
    )
    main_parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
    )

    subparsers = main_parser.add_subparsers(dest="command")

    create_parser = subparsers.add_parser("create", help="create a new discount code",
                                          description="Create a new discount code",
                                          formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    create_parser.add_argument(
        "name",
        help="name of person to issue the discount code to"
    )
    create_parser.add_argument(
        "-d",
        "--discount",
        type=int,
        default=10,
        help="discount amount as a percentage"
    )
    create_parser.add_argument(
        "-w",
        "--wrap",
        action="append",
        default=[],
        help="scope of discount code, e.g. wrap name"
    )

    use_parser = subparsers.add_parser("use", help="use a discount code",
                                       description="Use a discount code",
                                       formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    use_parser.add_argument(
        "code",
        help="discount code to use"
    )
    use_parser.add_argument(
        "-n",
        "--name",
        nargs="?",
        default="",
        help="name to match"
    )
    use_parser.add_argument(
        "-w",
        "--wrap",
        action="append",
        default=[],
        help="wrap to check"
    )

    args = main_parser.parse_args(command_line)

    if args.sheet_id == "$" + sheet_env_variable_name:
        args.sheet_id = os.environ.get(sheet_env_variable_name)
    if not args.sheet_id:
        print("\nNo Google sheet ID provided\n")
        main_parser.print_help()
        sys.exit(1)

    sheet = GoogleSheet(sheet_id=args.sheet_id, verbose_level=args.verbose, quiet=args.quiet)
    if args.command == "create":
        wraps = [Wrap(name) for name in args.wrap]
        sheet.create_new_code(name=args.name, scope=wraps, percentage=args.discount)
    elif args.command == "use":
        wraps = [Wrap(name) for name in args.wrap]
        sheet.use_code(args.code, name=args.name, wraps=wraps)


if __name__ == '__main__':
    main()

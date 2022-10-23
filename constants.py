import os

from kih_api import global_common

LOCATION_OF_FINANCIAL_DATABASE_FILE: str = os.getenv("KIH_API_LOCATION_EXCEL_FILE")
MONTHLY_EXPENSES_RESERVE_ACCOUNT_NAME: str = "Monthly Expenses"
TRANSFER_WISE_FINANCE_HUB_API_KEY_ENVIRONMENT_VARIABLE_KEY: str = "TRANSFER_WISE_FINANCE_HUB_API_KEY"
HOUSEHOLD_FINANCES_CHANNEL_USERNAME = "household_finances_channel" if global_common.get_environment() == global_common.Environment.PROD else global_common.get_environment_variable("TELEGRAM_CHANNEL_DEBUG_USERNAME")
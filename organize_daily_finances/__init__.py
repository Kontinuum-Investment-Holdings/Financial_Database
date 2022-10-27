import calendar
import datetime
from decimal import Decimal

import kih_api.wise.models
import pytz
from azure import functions
from kih_api import global_common
from kih_api.communication import telegram
from kih_api.finance_database import FinanceDatabase
from kih_api.wise.models import CashAccount, ProfileType, ReserveAccount, WiseAccount

import constants


def main(timer: functions.TimerRequest) -> None:
    do()

@global_common.job("Organize Daily Finances")
def do() -> None:
    wise_account: WiseAccount = WiseAccount(constants.TRANSFER_WISE_CURRENT_ACCOUNT_API_KEY_ENVIRONMENT_VARIABLE_KEY, ProfileType.Personal)
    new_zealand_datetime: datetime.datetime = datetime.datetime.now(pytz.timezone("Pacific/Auckland"))
    finance_database: FinanceDatabase = FinanceDatabase(constants.LOCATION_OF_FINANCIAL_DATABASE_FILE, new_zealand_datetime)
    nzd_account: CashAccount = wise_account.get_cash_account(global_common.Currency.NZD)
    monthly_expenses_reserve_account: ReserveAccount = wise_account.get_reserve_account(global_common.Currency.NZD, constants.MONTHLY_EXPENSES_RESERVE_ACCOUNT_NAME)

    monthly_expenses_budget: Decimal = finance_database.transfers.wants.amount
    number_of_days_in_this_month: Decimal = Decimal(str(calendar.monthrange(new_zealand_datetime.date().year, new_zealand_datetime.month)[1]))
    daily_expense_budget: Decimal = (monthly_expenses_budget / number_of_days_in_this_month).quantize(Decimal('1.00'))
    remaining_monthly_expense_budget: Decimal = (monthly_expenses_budget - (daily_expense_budget * new_zealand_datetime.day)).quantize(Decimal('1.00'))
    amount_to_transfer: Decimal = monthly_expenses_reserve_account.balance - remaining_monthly_expense_budget

    if amount_to_transfer > Decimal("0"):
        monthly_expenses_reserve_account.intra_account_transfer(nzd_account, amount_to_transfer)
    else:
        telegram.send_message(telegram.constants.telegram_channel_username,
                                            f"<u><b>Monthly Expenses Notification</b></u>"
                                            f"\nAmount over budget: <i>${kih_api.global_common.get_formatted_string_from_decimal(daily_expense_budget - amount_to_transfer, 2)}</i>", True)

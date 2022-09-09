import calendar
import datetime
from decimal import Decimal

import kih_api.wise.models
from azure import functions
from kih_api.communication import telegram
from kih_api.finance_database import FinanceDatabase
from kih_api.global_common import Currency
from kih_api.wise.models import CashAccount, ProfileTypes, ReserveAccount

import constants


def do():
    finance_database: FinanceDatabase = FinanceDatabase(constants.LOCATION_OF_FINANCIAL_DATABASE_FILE, datetime.datetime.now())
    nzd_account: CashAccount = CashAccount.get_by_profile_type_and_currency(ProfileTypes.PERSONAL, Currency.NZD)
    monthly_expenses_reserve_account: ReserveAccount = ReserveAccount.get_reserve_account_by_profile_type_currency_and_name(ProfileTypes.PERSONAL, Currency.NZD, "Monthly Expenses", False)

    monthly_expenses_budget: Decimal = finance_database.transfers.wants.amount
    number_of_days_in_this_month: Decimal = Decimal(str(calendar.monthrange(datetime.date.today().year, datetime.date.today().month)[1]))
    daily_expense_budget: Decimal = (monthly_expenses_budget / number_of_days_in_this_month).quantize(Decimal('1.00'))
    number_of_days_till_end_of_month: Decimal = number_of_days_in_this_month - Decimal(datetime.date.today().day) + Decimal("1")
    remaining_monthly_expense_budget: Decimal = (daily_expense_budget * number_of_days_till_end_of_month).quantize(Decimal('1.00'))
    amount_to_transfer: Decimal = monthly_expenses_reserve_account.balance - remaining_monthly_expense_budget

    if amount_to_transfer > Decimal("0"):
        kih_api.wise.models.IntraAccountTransfer.execute(amount_to_transfer, monthly_expenses_reserve_account, nzd_account, ProfileTypes.PERSONAL)
    else:
        telegram.send_message(telegram.constants.telegram_channel_username,
                                            f"<u><b>Monthly Expenses Notification</b></u>"
                                            f"\nAmount over budget: <i>${kih_api.global_common.get_formatted_string_from_decimal(daily_expense_budget - amount_to_transfer, 2)}</i>", True)


def main(mytimer: functions.TimerRequest) -> None:
    do()

if __name__ == "__main__":
    do()

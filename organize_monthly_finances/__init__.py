import datetime
from decimal import Decimal

from azure import functions
from kih_api import global_common
from kih_api.finance_database import FinanceDatabase
from kih_api.finance_database.exceptions import InsufficientFundsException
from kih_api.global_common import Currency
from kih_api.wise.models import CashAccount, ProfileType, Transfer, ReserveAccount, IntraAccountTransfer, WiseAccount, \
    Recipient

import constants


def main(timer: functions.TimerRequest) -> None:
    if not is_today_last_day_of_month():
        return

    do()

def is_today_last_day_of_month() -> bool:
    return (datetime.date.today() + datetime.timedelta(days=1)).day == 1

@global_common.job("Organize Monthly Expenses")
def do() -> None:
    wise_account: WiseAccount = WiseAccount(constants.TRANSFER_WISE_CURRENT_ACCOUNT_API_KEY_ENVIRONMENT_VARIABLE_KEY, ProfileType.Personal)
    financial_database: FinanceDatabase = FinanceDatabase(constants.LOCATION_OF_FINANCIAL_DATABASE_FILE)
    _transfer_to_cash_accounts(wise_account, financial_database)
    _transfer_to_reserve_accounts(wise_account, financial_database)

def _transfer_to_cash_accounts(wise_account: WiseAccount, financial_database: FinanceDatabase) -> None:
    nzd_account: CashAccount = wise_account.get_cash_account(global_common.Currency.NZD)
    excess_funds: Decimal = nzd_account.balance - financial_database.summary.salary
    finance_hub_recipient: Recipient = wise_account.get_recipient_by_account_number(financial_database.transfers.finance_hub.account_number)
    savings_recipient: Recipient = wise_account.get_recipient_by_account_number(
        financial_database.transfers.savings.account_number)

    if excess_funds < 0:
        raise InsufficientFundsException(f"Insufficient funds for monthly expenses\nRequired: NZD {str(financial_database.summary.salary)}\nContains: NZD {str(nzd_account.balance)}\nShort of: NZD {str(-excess_funds)}")

    finance_hub_transfer: Transfer = nzd_account.transfer(finance_hub_recipient, financial_database.transfers.finance_hub.amount, "Monthly Expenses")
    savings_transfer: Transfer = nzd_account.transfer(savings_recipient, (financial_database.transfers.savings.amount + excess_funds))

def _transfer_to_reserve_accounts(wise_account: WiseAccount, financial_database: FinanceDatabase) -> None:
    nzd_account: CashAccount = wise_account.get_cash_account(global_common.Currency.NZD)

    if financial_database.transfers.needs.amount > 0:
        needs_transfer: Transfer = Transfer.execute(financial_database.transfers.needs.amount, Currency.NZD, Currency.NZD, financial_database.transfers.needs.account_number, "Needs", ProfileType.Personal)

    for name, amount in financial_database.reserve.needs_reserve.expenses.items():
        reserve_account: ReserveAccount = ReserveAccount.get_reserve_account_by_profile_type_currency_and_name(ProfileType.Personal, Currency.NZD, f"{name} [Needs Reserve]", True)
        intra_account_transfer: IntraAccountTransfer = IntraAccountTransfer.execute(amount, nzd_account, reserve_account, ProfileType.Personal)

    for name, amount in financial_database.reserve.wants_reserve.expenses.items():
        reserve_account = ReserveAccount.get_reserve_account_by_profile_type_currency_and_name(ProfileType.Personal, Currency.NZD, f"{name} [Wants Reserve]", True)
        intra_account_transfer = IntraAccountTransfer.execute(amount, nzd_account, reserve_account, ProfileType.Personal)

    monthly_expenses_reserve_account: ReserveAccount = wise_account.get_reserve_account(global_common.Currency.NZD, constants.MONTHLY_EXPENSES_RESERVE_ACCOUNT_NAME, True)
    intra_account_transfer = nzd_account.intra_account_transfer(monthly_expenses_reserve_account, nzd_account.balance)

from decimal import Decimal
from typing import Optional

from azure import functions
from kih_api import global_common
from kih_api.finance_database import FinanceDatabase
from kih_api.finance_database.exceptions import InsufficientFundsException
from kih_api.global_common import Currency
from kih_api.wise.models import Transfer, ProfileTypes, CashAccount, ReserveAccount, IntraAccountTransfer

import constants

def main(timer: functions.TimerRequest) -> None:
    do()

@global_common.job("Organising Monthly Expenses")
def do() -> None:
    financial_database: FinanceDatabase = FinanceDatabase(constants.LOCATION_OF_FINANCIAL_DATABASE_FILE)
    nzd_account: CashAccount = CashAccount.get_by_profile_type_and_currency(ProfileTypes.PERSONAL, Currency.NZD)
    _transfer_to_cash_accounts(nzd_account, financial_database)
    _transfer_to_reserve_accounts(nzd_account, financial_database)

def _transfer_to_cash_accounts(nzd_account: CashAccount, financial_database: FinanceDatabase) -> None:
    excess_funds: Decimal = nzd_account.balance - financial_database.summary.salary
    if excess_funds < 0:
        raise InsufficientFundsException(f"Insufficient funds for monthly expenses\nRequired: NZD {str(financial_database.summary.salary)}\nContains: NZD {str(nzd_account.balance)}\nShort of: NZD {str(-excess_funds)}")

    finance_hub_transfer: Transfer = Transfer.execute(financial_database.transfers.finance_hub.amount, Currency.NZD, Currency.NZD, financial_database.transfers.finance_hub.account_number, "Finance Hub", ProfileTypes.PERSONAL)
    savings_transfer: Transfer = Transfer.execute((financial_database.transfers.savings.amount + excess_funds), Currency.NZD, Currency.NZD, financial_database.transfers.savings.account_number, "Savings", ProfileTypes.PERSONAL)

def _transfer_to_reserve_accounts(nzd_account: CashAccount, financial_database: FinanceDatabase) -> None:
    if financial_database.transfers.needs.amount > 0:
        needs_transfer: Transfer = Transfer.execute(financial_database.transfers.needs.amount, Currency.NZD, Currency.NZD, financial_database.transfers.needs.account_number, "Needs", ProfileTypes.PERSONAL)

    for name, amount in financial_database.reserve.needs_reserve.expenses.items():
        reserve_account: ReserveAccount = ReserveAccount.get_reserve_account_by_profile_type_currency_and_name(ProfileTypes.PERSONAL, Currency.NZD, f"{name} [Needs Reserve]", True)
        intra_account_transfer: IntraAccountTransfer = IntraAccountTransfer.execute(amount, nzd_account, reserve_account, ProfileTypes.PERSONAL)

    for name, amount in financial_database.reserve.wants_reserve.expenses.items():
        reserve_account = ReserveAccount.get_reserve_account_by_profile_type_currency_and_name(ProfileTypes.PERSONAL, Currency.NZD, f"{name} [Wants Reserve]", True)
        intra_account_transfer = IntraAccountTransfer.execute(amount, nzd_account, reserve_account, ProfileTypes.PERSONAL)

    nzd_account = CashAccount.get_by_profile_type_and_currency(ProfileTypes.PERSONAL, Currency.NZD)
    monthly_expenses_reserve_account: ReserveAccount = ReserveAccount.get_reserve_account_by_profile_type_currency_and_name(ProfileTypes.PERSONAL, Currency.NZD, constants.MONTHLY_EXPENSES_RESERVE_ACCOUNT_NAME, True)
    intra_account_transfer = IntraAccountTransfer.execute(nzd_account.balance, nzd_account, monthly_expenses_reserve_account, ProfileTypes.PERSONAL)

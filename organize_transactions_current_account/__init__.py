import datetime
from typing import List

import azure.functions as func
from kih_api import global_common
from kih_api.finance_database import FinanceDatabase
from kih_api.wise.models import WiseAccount, ProfileType, CashAccount, Transaction, Transfer, ReserveAccount, Recipient

import constants


def main(timer: func.TimerRequest) -> None:
    do()


@global_common.job("Organize Transactions [Current Account]")
def do() -> None:
    wise_account: WiseAccount = WiseAccount(constants.TRANSFER_WISE_CURRENT_ACCOUNT_API_KEY_ENVIRONMENT_VARIABLE_KEY, ProfileType.Personal)
    nzd_account: CashAccount = wise_account.get_cash_account(global_common.Currency.NZD)
    transaction_list: List[Transaction] = wise_account.get_all_transactions(nzd_account, datetime.datetime.now() - datetime.timedelta(hours=1), datetime.datetime.now())

    for transaction in transaction_list:
        if isinstance(transaction.entity, str) and "Chelmer".lower() in transaction.entity.lower():
            _organize_salary(wise_account, transaction)


def _organize_salary(wise_account: WiseAccount, transaction: Transaction) -> None:
    nzd_account: CashAccount = wise_account.get_cash_account(global_common.Currency.NZD)
    salary_reserve_account: ReserveAccount = wise_account.get_reserve_account(global_common.Currency.NZD, constants.SALARY_RESERVE_ACCOUNT_NAME, True)
    nzd_account.intra_account_transfer(salary_reserve_account, transaction.transaction_amount)

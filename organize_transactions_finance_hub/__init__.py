import datetime
from decimal import Decimal
from typing import List

import pytz
from azure import functions
from kih_api import global_common
from kih_api.communication import telegram
from kih_api.finance_database import FinanceDatabase
from kih_api.wise.models import CashAccount, ProfileType, ReserveAccount, Transaction, TransactionType, WiseAccount

import constants


def main(timer: functions.TimerRequest) -> None:
    do()


@global_common.job("Organize Transactions [Finance Hub]")
def do() -> None:
    wise_account: WiseAccount = WiseAccount(constants.TRANSFER_WISE_FINANCE_HUB_API_KEY_ENVIRONMENT_VARIABLE_KEY, ProfileType.Personal)
    nzd_account: CashAccount = wise_account.get_cash_account(global_common.Currency.NZD)
    transaction_list: List[Transaction] = wise_account.get_all_transactions(nzd_account, datetime.datetime.now() - datetime.timedelta(hours=1), datetime.datetime.now())

    for transaction in transaction_list:
        if isinstance(transaction.entity, str) and transaction.transaction_type == TransactionType.Transfer and transaction.transaction_amount > Decimal("0"):

            # TODO: Check if the transaction surname is correct
            if isinstance(transaction.entity, str):
                if "Jayasekara".lower() in transaction.entity.lower():
                    _transfer_sayurus_rent(wise_account, transaction, nzd_account)
                elif "Athaudha".lower() in transaction.entity.lower():
                    _transfer_kavindu_rent(wise_account, transaction, nzd_account)


def _transfer_sayurus_rent(wise_account: WiseAccount, transaction: Transaction, nzd_account: CashAccount) -> None:
    sayuru_reserve_account: ReserveAccount = wise_account.get_reserve_account(global_common.Currency.NZD, "Sayuru Jayasekara [Rent]")
    nzd_account.intra_account_transfer(sayuru_reserve_account, transaction.transaction_amount)

    telegram.send_message(constants.HOUSEHOLD_FINANCES_CHANNEL_USERNAME,
                          f"<b><i>Transfer Received from Sayuru Jayasekara</b></i>"
                          f"Current account balance: <i>${global_common.get_formatted_string_from_decimal(sayuru_reserve_account.balance)}</i>",
                          True)


def _transfer_kavindu_rent(wise_account: WiseAccount, transaction: Transaction, nzd_account: CashAccount) -> None:
    kavindu_reserve_account: ReserveAccount = wise_account.get_reserve_account(global_common.Currency.NZD, "Kavindu Athaudha [Rent]")
    new_zealand_datetime: datetime.datetime = datetime.datetime.now(pytz.timezone("Pacific/Auckland"))
    finance_database: FinanceDatabase = FinanceDatabase(constants.LOCATION_OF_FINANCIAL_DATABASE_FILE, new_zealand_datetime)
    monthly_rent: Decimal = finance_database.fixed_expenses.needs_expenses.expenses["Rent"]

    if transaction.transaction_amount < monthly_rent:
        return

    nzd_account.intra_account_transfer(kavindu_reserve_account, monthly_rent)
    telegram.send_message(constants.HOUSEHOLD_FINANCES_CHANNEL_USERNAME,
                          f"<b><i>Transfer Received from Kavindu Athaudha</b></i>"
                          f"Current account balance: <i>${global_common.get_formatted_string_from_decimal(kavindu_reserve_account.balance)}</i>",
                          True)

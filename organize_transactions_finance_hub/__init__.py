import datetime
from decimal import Decimal
from typing import List

from azure import functions
from kih_api import global_common
from kih_api.communication import telegram
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
            if "Smit".lower() in transaction.entity.lower():
                jason_smit_reserve_account: ReserveAccount = wise_account.get_reserve_account(global_common.Currency.NZD, "Jason Smit [Rent]")
                nzd_account.intra_account_transfer(jason_smit_reserve_account, transaction.transaction_amount)

                telegram.send_message(constants.HOUSEHOLD_FINANCES_CHANNEL_USERNAME,
                                      f"<b><i>Transfer Received from Jason Smit</b></i>"\
                                      f"Current account balance: <i>${global_common.get_formatted_string_from_decimal(jason_smit_reserve_account.balance)}</i>",
                                      True)

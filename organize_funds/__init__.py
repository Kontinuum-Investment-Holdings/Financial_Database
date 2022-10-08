import datetime
from decimal import Decimal
from typing import List

from azure import functions
from kih_api import global_common
from kih_api.communication import telegram
from kih_api.global_common import Currency
from kih_api.wise.common import override_api_key
from kih_api.wise.models import CashAccount, ProfileType, ReserveAccount, Transaction, IntraAccountTransfer, \
    TransactionType

import constants


def main(timer: functions.TimerRequest) -> None:
    override_api_key(constants.TRANSFER_WISE_FINANCE_HUB_API_KEY_ENVIRONMENT_VARIABLE_KEY)
    do()


@global_common.job("Organize Funds")
def do() -> None:
    nzd_account: CashAccount = CashAccount.get_by_profile_type_and_currency(ProfileType.Personal, Currency.NZD)
    transaction_list: List[Transaction] = Transaction.get_all(nzd_account, datetime.datetime.now() - datetime.timedelta(hours=1), datetime.datetime.now())

    for transaction in transaction_list:
        if isinstance(transaction.entity, str) and transaction.transaction_type == TransactionType.Transfer and transaction.transaction_amount > Decimal("0"):
            if "Smit".lower() in transaction.entity.lower():
                jason_smit_reserve_account: ReserveAccount = ReserveAccount.get_reserve_account_by_profile_type_currency_and_name(nzd_account.user_profile.type, nzd_account.currency, "Jason Smit [Reserve]", True)
                IntraAccountTransfer.execute(transaction.transaction_amount, nzd_account, jason_smit_reserve_account, nzd_account.user_profile.type)
                jason_smit_reserve_account = ReserveAccount.get_reserve_account_by_profile_type_currency_and_name(nzd_account.user_profile.type, nzd_account.currency, "Jason Smit [Reserve]", True)

                telegram.send_message(constants.HOUSEHOLD_FINANCES_CHANNEL_USERNAME,
                                      f"<b><i>Transfer Received from Jason Smit</b></i>"\
                                      f"Current account balance: <i>${global_common.get_formatted_string_from_decimal(jason_smit_reserve_account.balance)}</i>",
                                      True)

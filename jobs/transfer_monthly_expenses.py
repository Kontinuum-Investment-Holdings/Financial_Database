from decimal import Decimal

import global_common
from finance_database import FinanceDatabase
from finance_database.exceptions import InsufficientFundsException
from global_common import Currency
from wise.models import Transfer, ProfileTypes, CashAccount, ReserveAccount, IntraAccountTransfer

import constants


@global_common.job("Organising Monthly Expenses")
def do(event: None, context: None) -> None:
    finance_database: FinanceDatabase = FinanceDatabase(constants.LOCATION_OF_FINANCIAL_DATABASE_FILE)

    nzd_account: CashAccount = CashAccount.get_by_profile_type_and_currency(ProfileTypes.PERSONAL, Currency.NZD)
    excess_funds: Decimal = nzd_account.balance - finance_database.summary.salary

    if excess_funds < 0:
        raise InsufficientFundsException(f"Insufficient funds for monthly expenses\nRequired: NZD {str(-excess_funds)}")

    finance_hub_transfer: Transfer = Transfer.execute(finance_database.transfers.finance_hub.amount, Currency.NZD, Currency.NZD, finance_database.transfers.finance_hub.account_number, "Finance Hub", ProfileTypes.PERSONAL)
    savings_transfer: Transfer = Transfer.execute((finance_database.transfers.savings.amount + excess_funds), Currency.NZD, Currency.NZD, finance_database.transfers.savings.account_number, "Savings", ProfileTypes.PERSONAL)
    if finance_database.transfers.needs.amount > 0:
        needs_transfer: Transfer = Transfer.execute(finance_database.transfers.needs.amount, Currency.NZD, Currency.NZD, finance_database.transfers.needs.account_number, "Needs", ProfileTypes.PERSONAL)

    for name, amount in finance_database.reserve.needs_reserve.expenses.items():
        reserve_account: ReserveAccount = ReserveAccount.get_reserve_account_by_profile_type_currency_and_name(ProfileTypes.PERSONAL, Currency.NZD, f"{name} [Needs Reserve]", True)  # type: ignore
        intra_account_transfer: IntraAccountTransfer = IntraAccountTransfer.execute(amount, Currency.NZD, reserve_account, ProfileTypes.PERSONAL)  # type: ignore

    for name, amount in finance_database.reserve.wants_reserve.expenses.items():
        reserve_account: ReserveAccount = ReserveAccount.get_reserve_account_by_profile_type_currency_and_name(ProfileTypes.PERSONAL, Currency.NZD, f"{name} [Wants Reserve]", True)  # type: ignore
        intra_account_transfer: IntraAccountTransfer = IntraAccountTransfer.execute(amount, Currency.NZD, reserve_account, ProfileTypes.PERSONAL)  # type: ignore


if __name__ == "__main__":
    do(None, None)

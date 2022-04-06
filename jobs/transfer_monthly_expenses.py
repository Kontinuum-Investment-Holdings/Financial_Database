from decimal import Decimal

import global_common
from finance_database import FinanceDatabase
from finance_database.exceptions import InsufficientFundsException
from global_common import Currency
from wise.models import Transfer, ProfileTypes, AccountBalance

import constants


@global_common.threaded
@global_common.job("Organising Monthly Expenses")
def do(event: None, context: None) -> None:
    finance_database: FinanceDatabase = FinanceDatabase(constants.LOCATION_OF_FINANCIAL_DATABASE_FILE)

    nzd_account_balance: AccountBalance = AccountBalance.get_by_currency_and_profile_type(Currency.NZD, ProfileTypes.PERSONAL)
    excess_funds: Decimal = nzd_account_balance.balance - finance_database.summary.salary

    if excess_funds < 0:
        raise InsufficientFundsException(f"Insufficient funds for monthly expenses\nRequired: NZD {str(-excess_funds)}")

    finance_hub_transfer: Transfer = Transfer.execute(finance_database.transfers.finance_hub.amount, Currency.NZD, Currency.NZD, finance_database.transfers.finance_hub.account_number, "Finance Hub", ProfileTypes.PERSONAL)
    savings_transfer: Transfer = Transfer.execute((finance_database.transfers.savings.amount + excess_funds), Currency.NZD, Currency.NZD, finance_database.transfers.savings.account_number, "Savings", ProfileTypes.PERSONAL)
    if finance_database.transfers.needs.amount > 0:
        needs_transfer: Transfer = Transfer.execute(finance_database.transfers.needs.amount, Currency.NZD, Currency.NZD, finance_database.transfers.needs.account_number, "Needs", ProfileTypes.PERSONAL)


if __name__ == "__main__":
    do(None, None)

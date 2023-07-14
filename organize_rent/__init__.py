import datetime
import math
from dataclasses import dataclass
from decimal import Decimal
from typing import List

import azure.functions as func
from kih_api import global_common
from kih_api.communication import telegram
from kih_api.wise.models import ProfileType, ReserveAccount, CashAccount, WiseAccount

import constants


@dataclass
class Person:
    name: str
    rent: Decimal
    wise_jar_name: str

    def __init__(self, name: str, rent: Decimal, wise_jar_name: str = None):
        self.name = name
        self.rent = rent
        self.wise_jar_name = self.name + " [Rent]" if wise_jar_name is None else wise_jar_name


def main(timer: func.TimerRequest) -> None:
    do()


@global_common.job("Organize Rent")
def do() -> None:
    wise_account: WiseAccount = WiseAccount(constants.TRANSFER_WISE_FINANCE_HUB_API_KEY_ENVIRONMENT_VARIABLE_KEY, ProfileType.Personal)
    nzd_account: CashAccount = wise_account.get_cash_account(global_common.Currency.NZD)
    persons_list: List[Person] = [Person("Kavindu Athaudha", Decimal("397.50")), Person("Sayuru Jayasekara", Decimal("397.50"))]
    message = "<b><i>Rent notification</i></b>"

    for person in persons_list:
        reserve_account: ReserveAccount = wise_account.get_reserve_account(global_common.Currency.NZD, person.wise_jar_name, True)
        message = f"{message} \n\n<i><u>{person.name}</u></i>\n"

        if reserve_account.balance < person.rent:
            message = message + f"Insufficient funds for the rent\n" \
                                f"Current account balance: <i>${global_common.get_formatted_string_from_decimal(reserve_account.balance)}</i>\n" \
                                f"Minimum amount required: <i>${global_common.get_formatted_string_from_decimal(person.rent - reserve_account.balance)}</i>"
            continue

        reserve_account.intra_account_transfer(nzd_account, person.rent)
        next_payment_due_date: datetime.date = get_next_payment_due_date(reserve_account.balance, person.rent)

        message = message + f"Rent paid until: <i>{next_payment_due_date.strftime('%b %d, %Y')}</i>\n" \
                            f"Current account balance: <i>${global_common.get_formatted_string_from_decimal(reserve_account.balance)}</i>"

    telegram.send_message(constants.HOUSEHOLD_FINANCES_CHANNEL_USERNAME, message, True)


def get_next_payment_due_date(account_balance: Decimal, weekly_rent: Decimal) -> datetime.date:
    number_of_weeks_of_rent_paid: Decimal = Decimal(math.floor(account_balance / weekly_rent))
    return get_next_rent_payment_date(datetime.date.today(), 3) + datetime.timedelta(weeks=int(number_of_weeks_of_rent_paid))


def get_next_rent_payment_date(from_date: datetime.date, payment_day_of_week: int) -> datetime.date:
    next_rent_payment_date: datetime.date = from_date
    while True:
        if next_rent_payment_date.weekday() == payment_day_of_week:
            return next_rent_payment_date

        next_rent_payment_date = next_rent_payment_date + datetime.timedelta(days=1)

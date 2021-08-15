import time

import schedule

if __name__ == "__main__":
    # schedule.every().day.at("02:00").do(transfer_monthly_expenses.do)

    while True:
        schedule.run_pending()
        time.sleep(1)

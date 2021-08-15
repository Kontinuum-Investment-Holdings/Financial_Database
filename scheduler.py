import time

import schedule


if __name__ == "__main__":
    schedule.every().sunday.at("20:00").do(update_code_base.do)

    while True:
        schedule.run_pending()
        time.sleep(1)

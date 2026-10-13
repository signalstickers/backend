from datetime import date, timedelta


def get_current_ym_date():
    return date.today().strftime("%Y_%m")


def get_last_month_ym_date():
    return (date.today().replace(day=1) - timedelta(days=1)).strftime("%Y_%m")

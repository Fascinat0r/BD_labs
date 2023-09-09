import random

import psycopg2
from psycopg2.extras import DictCursor


class PGException(Exception):
    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self):
        print('calling str')
        if self.message:
            return 'PGException, {0} '.format(self.message)
        else:
            return 'PGException has been raised'


def add_article(cursor, name):
    cursor.execute("INSERT INTO articles (name) VALUES(%s)", (name,))


def print_articles(cursor):
    cursor.execute("SELECT name FROM articles")
    print("Articles:")
    for row in cursor:
        print(row[0])


def add_operation(cursor, debit, credit, article_name):
    cursor.execute(
        "INSERT INTO operations (debit,credit,article_id) SELECT %s,%s, id from articles where name=%s",
        (debit, credit, article_name))


def print_operations(cursor):
    cursor.execute(
        "SELECT debit,credit,articles.name, create_date FROM operations join articles on articles.id = operations.article_id")
    print("Operations:")
    for row in cursor:
        print(row)


def clear_all(cursor):
    cursor.execute("DELETE FROM balance CASCADE;")
    cursor.execute("DELETE FROM operations CASCADE;")
    cursor.execute("DELETE FROM articles CASCADE;")


def add_balance(cursor):

    cursor.execute("INSERT INTO balance DEFAULT VALUES RETURNING balance.id")
    return cursor.fetchone()[0]


def fill_balance(cursor, balance_id):
    cursor.execute(
        "SELECT SUM(debit),SUM(credit),SUM(debit) - SUM(credit)  FROM operations WHERE to_char(create_date, 'YYYY-MM') = to_char(CURRENT_TIMESTAMP, 'YYYY-MM')")
    results = cursor.fetchone()
    if results[2] < 0:
        raise PGException("ОШИБКА ОШИБКА 0 0 0 0 0. Вы так обанкротитесь :3")
    cursor.execute("UPDATE balance set debit=%s, credit=%s, amount=%s where id=%s", results.append(balance_id))


def print_balance(cursor):
    cursor.execute("SELECT debit,credit,amount, create_date FROM balance")
    print("Balance:")
    for row in cursor:
        print(row)


def calculate_profit_for_the_day(cursor, date):
    print()
    cursor.execute("SELECT SUM(debit) - SUM(credit) FROM operations where create_date=%s", (date,))
    print("Profit for " + date + " is " + str(cursor.fetchone()[0]))


def not_used_articles_in_period(cursor, start_date, end_date):
    cursor.execute(
        "select articles.name from articles full join (select * from operations where create_date>=%s and create_date<=%s) as op on articles.id=op.article_id group by articles.id having count(op.id)=0",
        (start_date, end_date))
    print("Not used articles in period " + start_date + ' - ' + end_date + ':')
    for row in cursor:
        print(row[0])


def all_operations_and_articles(cursor):
    cursor.execute(
        "select * from articles full join operations on operations.article_id=articles.id")
    print('all_operations_and_articles:')
    for row in cursor:
        print(row)

def balances_belonging_to_the_article(cursor,article_name: str):
    cursor.execute("")
    print('all_operations_and_articles:')
    for row in cursor:
        print(row)


def main():
    with psycopg2.connect(dbname='SmartHomeBudget', user='postgres', password='vezerford_admin',
                          host='localhost') as conn:
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            clear_all(cursor)
            cur_balance = add_balance(cursor)

            # 1
            articles = ["Fastfood", "Cloths", "Fuel", "Medicine"]
            for article in articles:
                add_article(cursor, article)
            print_articles(cursor)
            # 2
            add_operation(cursor, random.randint(500, 1000), random.randint(0, 1000), random.choice(articles))
            add_operation(cursor, random.randint(500, 1000), random.randint(0, 1000), random.choice(articles))
            add_operation(cursor, random.randint(500, 1000), random.randint(0, 1000), random.choice(articles))
            add_operation(cursor, random.randint(500, 1000), random.randint(0, 1000), random.choice(articles))
            print_operations(cursor)
            # 3
            fill_balance(cursor,1)
            print_balance(cursor)
            # 4
            calculate_profit_for_the_day(cursor, "2023-09-09")
            # 5
            not_used_articles_in_period(cursor, "2023-08-09", "2023-09-09")
            # 6
            all_operations_and_articles(cursor)
            # 7
            balances_belonging_to_the_article(cursor,random.choice(articles))


main()

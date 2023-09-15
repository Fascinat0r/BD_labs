import random

import psycopg2
from psycopg2 import sql
from psycopg2.extras import DictCursor

db_params = {
    'host': 'localhost',
    'database': 'SmartHomeBudget',
    'user': 'postgres',
    'password': 'vezerford_admin'
}


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
    s = ('SELECT debit,credit,articles.name, create_date '
         'FROM operations '
         'join articles on articles.id = operations.article_id')
    cursor.execute(s)
    print("Operations:")
    for row in cursor:
        print(row)


def clear_all(cursor):
    cursor.execute("TRUNCATE TABLE balance RESTART IDENTITY CASCADE")
    cursor.execute("TRUNCATE TABLE operations RESTART IDENTITY CASCADE")
    cursor.execute("TRUNCATE TABLE articles RESTART IDENTITY CASCADE")

    cursor.execute('''DROP TRIGGER IF EXISTS operation_update_protect ON operations''')
    cursor.execute('''DROP TRIGGER IF EXISTS correct_balance ON balance''')



def add_balance():
    conn = psycopg2.connect(**db_params)
    cursor = conn.cursor()
    try:
        # Calculate the sum of debit and credit operations
        cursor.execute("SELECT SUM(debit), SUM(credit) FROM operations WHERE balance_id IS NULL")
        sums = cursor.fetchone()
        debit_sum = sums[0] or 0  # Handle NULL result
        credit_sum = sums[1] or 0  # Handle NULL result
        if debit_sum - credit_sum < 0:
            raise PGException("ОШИБКА ОШИБКА 0 0 0 0. Вы так скоро обанкротитесь :3")
        # Start a transaction
        # conn.autocommit = False

        # Step 1: Insert a new balance entry
        cursor.execute(
            "INSERT INTO balance (create_date, debit, credit, amount) VALUES (CURRENT_DATE, %s, %s, %s) RETURNING id",
            [debit_sum, credit_sum, debit_sum - credit_sum])
        balance_id = cursor.fetchone()[0]

        # Step 2: Update operations with NULL balance_id to link them to the new balance
        cursor.execute(sql.SQL("UPDATE operations SET balance_id = %s WHERE balance_id IS NULL"), [balance_id])

        # Commit the transaction
        conn.commit()

    except PGException or psycopg2.DatabaseError as e:
        # Rollback the transaction in case of an error
        conn.rollback()
        print("Error:", e)
    finally:
        cursor.close()


def print_balance(cursor):
    cursor.execute("SELECT debit,credit,amount, create_date FROM balance")
    print("Balance:")
    for row in cursor:
        print(row)


def calculate_profit_for_the_day(cursor, date):
    print()
    cursor.execute("SELECT SUM(debit) - SUM(credit) FROM operations where create_date=%s", (date,))
    print("Profit for " + date + " is " + str(cursor.fetchone()[0] or 0))


def not_used_articles_in_period(cursor, start_date, end_date):
    s = ("select articles.name from articles "
         "full join ("
         "select * from operations "
         "where create_date>=%s and create_date<=%s) as op on articles.id=op.article_id "
         "group by articles.id "
         "having count(op.id)=0")
    cursor.execute(s, (start_date, end_date))
    print("Not used articles in period " + start_date + ' - ' + end_date + ':')
    for row in cursor:
        print(row[0])


def all_operations_and_articles(cursor):
    cursor.execute(
        "select * from articles full join operations on operations.article_id=articles.id")
    print('all_operations_and_articles:')
    for row in cursor:
        print(row)


def balances_belonging_to_the_article(cursor, article_name: str):
    s = ('SELECT COUNT(DISTINCT b.id) AS num_balances '
         'FROM balance b '
         'INNER JOIN operations o ON b.id = o.balance_id '
         'INNER JOIN articles a ON o.article_id = a.id '
         'WHERE a.name = %s')
    cursor.execute(s, (article_name,))
    print('balances belonging to the article', article_name, ':', cursor.fetchone()[0])


def expenses_for_given_article_in_period(cursor, start_date, end_date, article_name):
    s = ("SELECT b.id AS balance_id, SUM(o.debit) AS total_debit "
         "FROM articles a "
         "JOIN operations o ON a.id = o.article_id "
         "JOIN balance b ON o.balance_id = b.id "
         "WHERE a.name = %s AND o.create_date >= %s AND o.create_date <= %s "
         "GROUP BY b.id")
    cursor.execute(s, (article_name, start_date, end_date))
    print('Debit for', article_name, "in period", start_date, '-', end_date, ':')
    for row in cursor:
        print(row)


def delete_article(cursor, article_name):
    s = ('''WITH deleted_operations AS (
            DELETE FROM operations 
            WHERE article_id IN (
            SELECT id 
            FROM articles 
            WHERE name = %s)
            RETURNING *)
            DELETE FROM articles 
            WHERE name = %s RETURNING *''')
    cursor.execute(s, (article_name, article_name))
    print("Delete article with name", article_name, ', deleted:')
    for row in cursor:
        print(row)


def delete_most_unprofitable(cursor):
    s = ('''DELETE FROM balance 
         WHERE id = (
         SELECT id 
         FROM balance 
         ORDER BY amount ASC 
         LIMIT 1) RETURNING *''')
    cursor.execute(s)
    print('Delete most unprofitable balance, deleted:', cursor.fetchone())


def delete__most_unprofitable_balance_but_check_unique_articles():
    conn = psycopg2.connect(**db_params)
    cur = conn.cursor()

    try:
        # Begin a transaction
        conn.autocommit = False

        cur.execute('''SELECT COUNT(ars.article_id) FROM (SELECT o.article_id AS article_id FROM operations o
                       GROUP BY o.article_id) AS ars''')
        start_num_articles = cur.fetchone()[0]
        print("Articles used now:", start_num_articles)
        # Find the most unprofitable balance and delete its operations
        cur.execute('''
            DELETE FROM operations o
            WHERE o.balance_id = (SELECT balance_id FROM (
                SELECT b.id AS balance_id,
                       COALESCE(SUM(o.credit), 0) - COALESCE(SUM(o.debit), 0) AS balance_amount 
                FROM balance b
                LEFT JOIN operations o ON b.id = o.balance_id
                GROUP BY b.id
                ORDER BY balance_amount ASC
                LIMIT 1
            ) AS UnprofitableBalances);

            DELETE FROM balance b
            WHERE b.id = (SELECT balance_id FROM (
                SELECT b.id AS balance_id,
                       COALESCE(SUM(o.credit), 0) - COALESCE(SUM(o.debit), 0) AS balance_amount
                FROM balance b
                LEFT JOIN operations o ON b.id = o.balance_id
                GROUP BY b.id
                ORDER BY balance_amount ASC
                LIMIT 1
            ) AS UnprofitableBalances) RETURNING *;
        ''')
        print('Delete most unprofitable balance, deleted:', cur.fetchone())
        # Check if there are remote articles
        cur.execute('''SELECT COUNT(ars.article_id) FROM (SELECT o.article_id AS article_id FROM operations o
                               GROUP BY o.article_id) AS ars''')
        end_num_articles = cur.fetchone()[0]
        print("Articles used after deleting:", end_num_articles)

        # If there are remote articles, rollback the transaction; otherwise, commit it
        if start_num_articles - end_num_articles > 0:
            conn.rollback()
            print('Transaction rolled back, in the remote balance, articles were used,',
                  'operations within which were not carried out anywhere else')
        else:
            conn.commit()
            print("Transaction committed")
            print_balance(cur)

    except Exception as e:
        # Handle any exceptions and rollback the transaction
        conn.rollback()
        print(f"Transaction rolled back due to an error: {e}")

    finally:
        # Close the cursor and the connection
        cur.close()
        conn.close()


def increase_expenses_for_given_article(cursor, article_name, value):
    print("Increase credit value by", value, "to operations from category", article_name)
    cursor.execute('''UPDATE operations SET credit = credit + %s
                      WHERE article_id IN (SELECT id FROM articles WHERE name=%s) RETURNING balance_id''',
                   (value, article_name,))
    balances = cursor.fetchall()
    for row in balances:
        cursor.execute('''UPDATE balance SET credit=credit+%s, amount=amount-%s WHERE id=%s''', (value, value, row[0]))


def replace_article(old_article_name, new_article_name):
    print("Replace", old_article_name, 'by', new_article_name)
    if old_article_name == new_article_name:
        raise PGException("Can't replace article by themself")

    with psycopg2.connect(**db_params) as conn:
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            cursor.execute('''UPDATE operations SET article_id=(select id from articles where name=%s)
                              WHERE article_id=(select id from articles where name=%s)''',
                           (new_article_name, old_article_name))
            delete_article(cursor, old_article_name)
            conn.commit()


def replace_article_but_rollback(old_article_name, new_article_name):
    print("Replace", old_article_name, 'by', new_article_name)
    if old_article_name == new_article_name:
        raise PGException("Can't replace article by themself")

    with psycopg2.connect(**db_params) as conn:
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            cursor.execute('''UPDATE operations SET article_id=(select id from articles where name=%s)
                              WHERE article_id=(select id from articles where name=%s)''',
                           (new_article_name, old_article_name))
            delete_article(cursor, old_article_name)

            print("Rollback...")
            conn.rollback()


def main():
    with psycopg2.connect(**db_params) as conn:
        conn.autocommit = True
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            clear_all(cursor)

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
    add_balance()
    add_balance()
    with psycopg2.connect(**db_params) as conn:
        conn.autocommit = True
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            print_balance(cursor)
            # 4
            calculate_profit_for_the_day(cursor, "2023-09-11")
            # 5
            not_used_articles_in_period(cursor, "2023-08-09", "2023-09-30")
            # 6
            all_operations_and_articles(cursor)
            # 7
            balances_belonging_to_the_article(cursor, random.choice(articles))
            # 8
            expenses_for_given_article_in_period(cursor, "2023-08-09", "2023-09-30", random.choice(articles))
            # 9
            delete_article(cursor, random.choice(articles))
            # 10
            delete_most_unprofitable(cursor)
            # 11
    delete__most_unprofitable_balance_but_check_unique_articles()
    with psycopg2.connect(**db_params) as conn:
        conn.autocommit = True
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            print_operations(cursor)
            print_balance(cursor)
            # 12
            increase_expenses_for_given_article(cursor, random.choice(articles), 1000)
            print_operations(cursor)
            print_balance(cursor)
            # 13
    replace_article(random.choice(articles), random.choice(articles))
    with psycopg2.connect(**db_params) as conn:
        conn.autocommit = True
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            print_operations(cursor)
    replace_article_but_rollback(random.choice(articles), random.choice(articles))
    with psycopg2.connect(**db_params) as conn:
        conn.autocommit = True
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            print_operations(cursor)


# main()

import psycopg2.errors

from lab2 import *


def create_free_operations_view(cur):
    print('\nВсе статьи и суммы приход/расход неучтенных операций:')
    cur.execute("DROP VIEW IF EXISTS operation_view")
    cur.execute('''CREATE VIEW operation_view AS
                      SELECT a.name, SUM(o.credit) AS credit, SUM(o.debit) AS debit FROM articles a 
                      INNER JOIN operations o ON a.id=o.article_id
                      WHERE o.balance_id IS NULL
                      GROUP BY a.name;
                      SELECT * FROM operation_view;''')
    for row in cur:
        print(row)


def create_balance_view(cur):
    print('\nПредставление, отображающее все балансы и число операций, на основании которых они были сформированы:')
    cur.execute("DROP VIEW IF EXISTS balance_view")
    # cur.execute('select SUBSTRING(g.name FROM POSITION(%s IN g.name)+1), g.name from groups g', ('_',))

    cur.execute('''CREATE VIEW balance_view AS
                      SELECT b.create_date, COUNT(o.id) FROM balance b INNER JOIN operations o ON o.balance_id=b.id
                      GROUP BY b.create_date; 
                      SELECT * FROM balance_view''')
    for row in cur:
        print(row)


def create_stored_procedure_with_last_balance(cur):
    print("\nВсе операции последнего баланса и прибыли по каждой:")
    cur.execute("TRUNCATE TABLE temp")
    cur.execute('''CREATE OR REPLACE PROCEDURE last_balance()
                        LANGUAGE plpgsql
                        AS $$
                        BEGIN
                             INSERT INTO temp
                             SELECT a.name, (o.debit-o.credit) AS profit FROM operations o 
                             INNER JOIN articles a ON a.id=o.article_id
                             WHERE o.balance_id=(SELECT b.id FROM balance b 
                             WHERE b.create_date=(SELECT MAX(b.create_date) FROM balance b));
                        END;
                        $$;

                        DO $$
                        BEGIN
                          CALL last_balance();
                        END;
                        $$;
                      ''')
    cur.execute("SELECT * FROM temp")
    for row in cur:
        print(row)


def create_procedure_compare_articles(cur, article1, article2):
    print("\nБалансы, операции по статье", article1,
          "в которых составили прибыль большую, чем по статье", article2, ":")
    cur.execute("TRUNCATE TABLE temp")
    cur.execute('''CREATE OR REPLACE PROCEDURE  summary_by_groups_in_interval(firgt_article varchar, second_article varchar)
                        LANGUAGE plpgsql
                        AS $$
                        BEGIN
                            INSERT INTO temp
                            SELECT o1.balance_id FROM
                            (SELECT * FROM operations o WHERE o.article_id=(SELECT a.id FROM articles a WHERE a.name=firgt_article)) AS o1 INNER JOIN
                            (SELECT * FROM operations o WHERE o.article_id=(SELECT a.id FROM articles a WHERE a.name=second_article)) AS o2 
                            ON o1.balance_id=o2.balance_id
                            GROUP BY o1.balance_id
                            HAVING (SUM(o1.debit)-SUM(o1.credit))-(SUM(o2.debit)-SUM(o2.credit))>0;

                        END;
                        $$;

                        DO $$
                        BEGIN
                          CALL  summary_by_groups_in_interval(%s, %s);
                        END;
                        $$;

                      ''', (article1, article2,))
    cur.execute("SELECT * FROM temp")

    # ((SELECT a.id FROM articles a WHERE a.name= % s)) > 0
    # AND
    # ((SELECT a.id FROM articles a WHERE a.name= % s)) > 0
    for row in cur:
        print(row[0])


def create_procedure_worst_article_in_balance(cur, balance):
    cur.execute("TRUNCATE TABLE temp")
    article_name = ''
    cur.execute('''CREATE OR REPLACE FUNCTION get_worst_article_balance(cur_balance_id integer)
                    RETURNS varchar AS $$
                    DECLARE
                        article_name varchar;
                    BEGIN
                        SELECT a.name INTO article_name
                        FROM operations o
                        INNER JOIN articles a ON a.id = o.article_id
                        WHERE o.id = cur_balance_id
                        GROUP BY a.name
                        ORDER BY SUM(o.debit - o.credit)
                        LIMIT 1;
                    
                        RETURN article_name;
                    END;
                    $$ LANGUAGE plpgsql;''')
    cur.execute("SELECT get_worst_article_balance(%s);", (balance,))
    article_name = cur.fetchone()[0]
    print("\nCтатья, операции по которой проведены с наибольшими расходами в балансе", balance, ":", article_name)


def create_trigger_correct_balance(cur):
    cur.execute('''CREATE OR REPLACE FUNCTION pre_ins_correct_balance()
                      RETURNS trigger AS $BODY$
                    BEGIN
                      RAISE EXCEPTION 'Нельзя создать пустой баланс!';
                      RETURN NEW;
                    END $BODY$
                    LANGUAGE plpgsql;
                
                CREATE OR REPLACE TRIGGER correct_balance
                BEFORE INSERT ON balance
                    FOR EACH ROW 
                    WHEN (NEW.credit=0 AND NEW.debit=0 OR NEW.create_date IS NULL)
                    EXECUTE FUNCTION pre_ins_correct_balance();
                        ''')


def create_trigger_operation_update_protect(cur):
    cur.execute('''CREATE OR REPLACE FUNCTION pre_upd_operation_update_protect()
                        RETURNS TRIGGER AS $$
                        BEGIN
                         IF (NEW.balance_id IS NOT NULL) THEN
                         RAISE EXCEPTION 'Нельзя изменять операцию, так как она уже содержится в балансе!';
                         END IF;
                         RETURN NEW; 
                        END;
                        $$ LANGUAGE plpgsql;
                        CREATE OR REPLACE TRIGGER operation_update_protect
                        BEFORE UPDATE ON operations
                        FOR EACH ROW
                        EXECUTE PROCEDURE pre_upd_operation_update_protect()

                        ''')


def create_trigger_operation_delete_protect(cur):
    cur.execute('''CREATE OR REPLACE FUNCTION pre_del_operation_delete_protect()
                        RETURNS TRIGGER AS $$
                        BEGIN
                         IF (OLD.balance_id IS NOT NULL) THEN
                         RAISE EXCEPTION 'Нельзя удалить операцию, так как она уже содержится в балансе!';
                         END IF;
                         RETURN OLD; 
                        END;
                        $$ LANGUAGE plpgsql;
                        CREATE OR REPLACE TRIGGER operation_delete_protect
                        BEFORE DELETE ON operations
                        FOR EACH ROW
                        EXECUTE PROCEDURE pre_del_operation_delete_protect()

                        ''')


def edit_operation(cur, operation_id, new_debit, new_credit):
    cur.execute("UPDATE operations SET debit=%s, credit=%s WHERE id=%s", (new_debit, new_credit, operation_id))


def delete_operation(cur, operation_id):
    cur.execute('''DELETE FROM operations WHERE id=%s''', (operation_id,))


def financial_flows(cur, start_date, end_date, article_ids, flow_type):
    cur.execute('''CREATE TABLE IF NOT EXISTS calculate_result (
                    article_id integer,
                    article_name varchar,
                    percentage numeric);
                    
                    CREATE OR REPLACE FUNCTION calculate_article_percentage(
                        start_date date,
                        end_date date,
                        article_ids integer[],
                        flow_type text
                    )
                    RETURNS TABLE (article_id integer, article_name varchar, percentage numeric) AS $$
                    DECLARE
                        total_amount numeric := 0;
                        cur_article_id integer := 0;
                    BEGIN
                        -- Calculate the total amount of financial flows for the specified interval and flow type
                        SELECT SUM(CASE WHEN flow_type = 'debit' THEN debit ELSE credit END)
                        INTO total_amount
                        FROM operations o
                        WHERE o.create_date BETWEEN start_date AND end_date
                        AND o.article_id = ANY(article_ids);
                    
                        -- Declare a cursor for the specified articles
                        FOR cur_article_id IN SELECT unnest(article_ids) 
                        LOOP
                            -- Calculate the percentage for each article
                            INSERT INTO calculate_result
                            SELECT t.id, a.name, t.percent FROM (SELECT o.article_id AS id,
                            (SUM(CASE WHEN flow_type = 'debit' THEN o.debit ELSE o.credit END) / total_amount) * 100
                            AS percent
                            FROM operations o INNER JOIN articles a ON a.id=o.article_id
                            WHERE create_date BETWEEN start_date AND end_date
                                  AND o.article_id = cur_article_id
                            GROUP BY o.article_id) as t INNER JOIN articles a ON a.id=t.id;
                        END LOOP;
                        
                        RETURN QUERY SELECT * FROM calculate_result;
                    END;
                    $$ LANGUAGE plpgsql;''')
    cursor.execute("SELECT * FROM calculate_article_percentage(%s, %s, %s, %s);",
                   (start_date, end_date, article_ids, flow_type))

    for row in cur:
        print(row[0:2], str(round(row[2], 2)) + '%')


try:
    with psycopg2.connect(**db_params) as conn:
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            conn.autocommit = True
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
            # 3
    add_balance()
    with psycopg2.connect(**db_params) as conn:
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            conn.autocommit = True
            add_operation(cursor, random.randint(500, 1000), random.randint(0, 1000), random.choice(articles))
            add_operation(cursor, random.randint(500, 1000), random.randint(0, 1000), random.choice(articles))
            add_operation(cursor, random.randint(500, 1000), random.randint(0, 1000), random.choice(articles))
            add_operation(cursor, random.randint(500, 1000), random.randint(0, 1000), random.choice(articles))
            print_operations(cursor)
            # 1
            create_free_operations_view(cursor)
            # 2
            create_balance_view(cursor)
            # # 3
            create_stored_procedure_with_last_balance(cursor)

            create_procedure_compare_articles(cursor, random.choice(articles), random.choice(articles))

            create_procedure_worst_article_in_balance(cursor, 1)

            create_trigger_correct_balance(cursor)
    add_balance()
    # add_balance()
    with psycopg2.connect(**db_params) as conn:
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            pass

            #
            create_trigger_operation_update_protect(cursor)
            # edit_operation(cursor, 1, 1000, 1000)
            add_operation(cursor, 999, 999, random.choice(articles))
            edit_operation(cursor, 9, 1010, 1010)
            print_operations(cursor)

            create_trigger_operation_delete_protect(cursor)
            financial_flows(cursor, '2023-09-10', '2023-09-15', [1, 2], 'debit')

except PGException or psycopg2.errors.RaiseException as err:
    print(err)

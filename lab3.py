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


def create_trigger_subject_update_protect(cur):
    cur.execute('''CREATE OR REPLACE FUNCTION pre_upd_mark_subject_update_protect()
                        RETURNS TRIGGER AS $$
                        BEGIN
                         IF EXISTS(
                        SELECT m.id FROM marks m INNER JOIN public.subjects s ON s.id = m.subject_id
                        WHERE s.name = NEW.name) THEN

                         RAISE EXCEPTION 'Нельзя изменять наименование предмета, если на него есть ссылки!';
                         END IF;
                         RETURN NEW; 
                        END;
                        $$ LANGUAGE plpgsql;
                        CREATE OR REPLACE TRIGGER subject_update_protect
                        BEFORE UPDATE ON subjects
                        FOR EACH ROW
                        EXECUTE PROCEDURE pre_upd_mark_subject_update_protect()

                        ''')


def create_trigger_subject_delete_protect(cur):
    cur.execute('''CREATE OR REPLACE FUNCTION pre_del_mark_subject_delete_protect()
                        RETURNS TRIGGER AS $$
                        BEGIN
                         IF EXISTS(
                        SELECT m.id FROM marks m
                        WHERE m.subject_id = (SELECT s.id FROM subjects s WHERE s.name=OLD.name)) THEN

                         RAISE EXCEPTION 'Нельзя удалить предмет, если на него есть ссылки!';
                         END IF; 
                         RETURN NEW;
                        END;
                        $$ LANGUAGE plpgsql;
                        CREATE OR REPLACE TRIGGER subject_delete_protect
                        BEFORE DELETE ON subjects
                        FOR EACH ROW
                        EXECUTE PROCEDURE pre_del_mark_subject_delete_protect()

                        ''')


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
            # # add_mark(cursor, 1, 1, 1, 10)
            #
            # create_trigger_subject_update_protect(cursor)
            # # change_subjects_name(cursor, "Math", "Linux")
            #
            # create_trigger_subject_delete_protect(cursor)
            # # delete_subject(cursor, "Math")
            #
            # # print_marks(cursor)
            #
            # increase_in_ratings(cursor, "2002", "2023")
except PGException or psycopg2.errors.RaiseException as err:
    print(err)

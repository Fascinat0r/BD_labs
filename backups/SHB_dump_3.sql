PGDMP         (                {            SmartHomeBudget    15.3    15.2 &    .           0    0    ENCODING    ENCODING        SET client_encoding = 'UTF8';
                      false            /           0    0 
   STDSTRINGS 
   STDSTRINGS     (   SET standard_conforming_strings = 'on';
                      false            0           0    0 
   SEARCHPATH 
   SEARCHPATH     8   SELECT pg_catalog.set_config('search_path', '', false);
                      false            1           1262    48818    SmartHomeBudget    DATABASE     �   CREATE DATABASE "SmartHomeBudget" WITH TEMPLATE = template0 ENCODING = 'UTF8' LOCALE_PROVIDER = libc LOCALE = 'Russian_Russia.1251';
 !   DROP DATABASE "SmartHomeBudget";
                postgres    false            �            1255    53730    balances_worst_article(integer) 	   PROCEDURE     @  CREATE PROCEDURE public.balances_worst_article(IN cur_balance_id integer, OUT article_name character varying)
    LANGUAGE plpgsql
    AS $$
                        BEGIN
                            SELECT a.name INTO article_name FROM operations INNER JOIN articles a ON a.id=o.article_id
                            WHERE b.id = cur_balance_id
                            GROUP BY a.name
                            ORDER BY o.debit-o.credit
                            LIMIT 1;
                                     
                        END;
                        $$;
 m   DROP PROCEDURE public.balances_worst_article(IN cur_balance_id integer, OUT article_name character varying);
       public          postgres    false            �            1255    55708 9   calculate_article_percentage(date, date, integer[], text)    FUNCTION     o  CREATE FUNCTION public.calculate_article_percentage(start_date date, end_date date, article_ids integer[], flow_type text) RETURNS TABLE(article_id integer, article_name character varying, percentage numeric)
    LANGUAGE plpgsql
    AS $$
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
                    $$;
 z   DROP FUNCTION public.calculate_article_percentage(start_date date, end_date date, article_ids integer[], flow_type text);
       public          postgres    false            �            1255    53842 "   get_worst_article_balance(integer)    FUNCTION     �  CREATE FUNCTION public.get_worst_article_balance(cur_balance_id integer) RETURNS character varying
    LANGUAGE plpgsql
    AS $$
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
                    $$;
 H   DROP FUNCTION public.get_worst_article_balance(cur_balance_id integer);
       public          postgres    false            �            1255    51508    last_balance() 	   PROCEDURE       CREATE PROCEDURE public.last_balance()
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
 &   DROP PROCEDURE public.last_balance();
       public          postgres    false            �            1255    54654 "   pre_del_operation_delete_protect()    FUNCTION     �  CREATE FUNCTION public.pre_del_operation_delete_protect() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
                        BEGIN
                         IF (OLD.balance_id IS NOT NULL) THEN
                         RAISE EXCEPTION 'Нельзя удалить операцию, так как она уже содержится в балансе!';
                         END IF;
                         RETURN OLD; 
                        END;
                        $$;
 9   DROP FUNCTION public.pre_del_operation_delete_protect();
       public          postgres    false            �            1255    53932    pre_ins_correct_balance()    FUNCTION       CREATE FUNCTION public.pre_ins_correct_balance() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
                    BEGIN
                      RAISE EXCEPTION 'Нельзя создать пустой баланс!';
                      RETURN NEW;
                    END $$;
 0   DROP FUNCTION public.pre_ins_correct_balance();
       public          postgres    false            �            1255    54231 "   pre_upd_operation_update_protect()    FUNCTION     �  CREATE FUNCTION public.pre_upd_operation_update_protect() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
                        BEGIN
                         IF (NEW.balance_id IS NOT NULL) THEN
                         RAISE EXCEPTION 'Нельзя изменять операцию, так как она уже содержится в балансе!';
                         END IF;
                         RETURN NEW; 
                        END;
                        $$;
 9   DROP FUNCTION public.pre_upd_operation_update_protect();
       public          postgres    false            �            1255    51666 C   summary_by_groups_in_interval(character varying, character varying) 	   PROCEDURE     N  CREATE PROCEDURE public.summary_by_groups_in_interval(IN firgt_article character varying, IN second_article character varying)
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
 ~   DROP PROCEDURE public.summary_by_groups_in_interval(IN firgt_article character varying, IN second_article character varying);
       public          postgres    false            �            1259    48819    articles    TABLE     [   CREATE TABLE public.articles (
    id integer NOT NULL,
    name character varying(100)
);
    DROP TABLE public.articles;
       public         heap    postgres    false            �            1259    48844    articles_id_seq    SEQUENCE     �   ALTER TABLE public.articles ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.articles_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);
            public          postgres    false    214            �            1259    48822    balance    TABLE     �   CREATE TABLE public.balance (
    id integer NOT NULL,
    create_date date DEFAULT CURRENT_DATE,
    debit integer,
    credit integer,
    amount integer
);
    DROP TABLE public.balance;
       public         heap    postgres    false            �            1259    48845    balance_id_seq    SEQUENCE     �   ALTER TABLE public.balance ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.balance_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);
            public          postgres    false    215            �            1259    48825 
   operations    TABLE     �   CREATE TABLE public.operations (
    id integer NOT NULL,
    article_id integer,
    debit integer,
    credit integer,
    create_date date DEFAULT CURRENT_DATE,
    balance_id integer
);
    DROP TABLE public.operations;
       public         heap    postgres    false            �            1259    55724    balance_view    VIEW     �   CREATE VIEW public.balance_view AS
 SELECT b.create_date,
    count(o.id) AS count
   FROM (public.balance b
     JOIN public.operations o ON ((o.balance_id = b.id)))
  GROUP BY b.create_date;
    DROP VIEW public.balance_view;
       public          postgres    false    215    216    216    215            �            1259    55703    calculate_result    TABLE     }   CREATE TABLE public.calculate_result (
    article_id integer,
    article_name character varying,
    percentage numeric
);
 $   DROP TABLE public.calculate_result;
       public         heap    postgres    false            �            1259    55720    operation_view    VIEW     �   CREATE VIEW public.operation_view AS
 SELECT a.name,
    sum(o.credit) AS credit,
    sum(o.debit) AS debit
   FROM (public.articles a
     JOIN public.operations o ON ((a.id = o.article_id)))
  WHERE (o.balance_id IS NULL)
  GROUP BY a.name;
 !   DROP VIEW public.operation_view;
       public          postgres    false    214    216    216    216    216    214            �            1259    48846    operations_id_seq    SEQUENCE     �   ALTER TABLE public.operations ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.operations_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);
            public          postgres    false    216            �            1259    51324    temp    TABLE     E   CREATE TABLE public.temp (
    c character varying,
    i numeric
);
    DROP TABLE public.temp;
       public         heap    postgres    false            $          0    48819    articles 
   TABLE DATA           ,   COPY public.articles (id, name) FROM stdin;
    public          postgres    false    214   �@       %          0    48822    balance 
   TABLE DATA           I   COPY public.balance (id, create_date, debit, credit, amount) FROM stdin;
    public          postgres    false    215   �@       +          0    55703    calculate_result 
   TABLE DATA           P   COPY public.calculate_result (article_id, article_name, percentage) FROM stdin;
    public          postgres    false    221   "A       &          0    48825 
   operations 
   TABLE DATA           \   COPY public.operations (id, article_id, debit, credit, create_date, balance_id) FROM stdin;
    public          postgres    false    216   �A       *          0    51324    temp 
   TABLE DATA           $   COPY public.temp (c, i) FROM stdin;
    public          postgres    false    220   B       2           0    0    articles_id_seq    SEQUENCE SET     =   SELECT pg_catalog.setval('public.articles_id_seq', 4, true);
          public          postgres    false    217            3           0    0    balance_id_seq    SEQUENCE SET     <   SELECT pg_catalog.setval('public.balance_id_seq', 2, true);
          public          postgres    false    218            4           0    0    operations_id_seq    SEQUENCE SET     ?   SELECT pg_catalog.setval('public.operations_id_seq', 9, true);
          public          postgres    false    219            �           2606    48829    articles pk_articles 
   CONSTRAINT     R   ALTER TABLE ONLY public.articles
    ADD CONSTRAINT pk_articles PRIMARY KEY (id);
 >   ALTER TABLE ONLY public.articles DROP CONSTRAINT pk_articles;
       public            postgres    false    214            �           2606    48831    balance pk_balance 
   CONSTRAINT     P   ALTER TABLE ONLY public.balance
    ADD CONSTRAINT pk_balance PRIMARY KEY (id);
 <   ALTER TABLE ONLY public.balance DROP CONSTRAINT pk_balance;
       public            postgres    false    215            �           2606    48833    operations pk_operations 
   CONSTRAINT     V   ALTER TABLE ONLY public.operations
    ADD CONSTRAINT pk_operations PRIMARY KEY (id);
 B   ALTER TABLE ONLY public.operations DROP CONSTRAINT pk_operations;
       public            postgres    false    216            �           2620    55731    balance correct_balance    TRIGGER     �   CREATE TRIGGER correct_balance BEFORE INSERT ON public.balance FOR EACH ROW WHEN ((((new.credit = 0) AND (new.debit = 0)) OR (new.create_date IS NULL))) EXECUTE FUNCTION public.pre_ins_correct_balance();
 0   DROP TRIGGER correct_balance ON public.balance;
       public          postgres    false    215    224    215    215    215            �           2620    54655 #   operations operation_delete_protect    TRIGGER     �   CREATE TRIGGER operation_delete_protect BEFORE DELETE ON public.operations FOR EACH ROW EXECUTE FUNCTION public.pre_del_operation_delete_protect();
 <   DROP TRIGGER operation_delete_protect ON public.operations;
       public          postgres    false    241    216            �           2620    55732 #   operations operation_update_protect    TRIGGER     �   CREATE TRIGGER operation_update_protect BEFORE UPDATE ON public.operations FOR EACH ROW EXECUTE FUNCTION public.pre_upd_operation_update_protect();
 <   DROP TRIGGER operation_update_protect ON public.operations;
       public          postgres    false    236    216            �           2606    48865 !   operations fk_operations_articles    FK CONSTRAINT     �   ALTER TABLE ONLY public.operations
    ADD CONSTRAINT fk_operations_articles FOREIGN KEY (article_id) REFERENCES public.articles(id) ON DELETE CASCADE;
 K   ALTER TABLE ONLY public.operations DROP CONSTRAINT fk_operations_articles;
       public          postgres    false    216    214    3210            �           2606    48870     operations fk_operations_balance    FK CONSTRAINT     �   ALTER TABLE ONLY public.operations
    ADD CONSTRAINT fk_operations_balance FOREIGN KEY (balance_id) REFERENCES public.balance(id) ON DELETE CASCADE;
 J   ALTER TABLE ONLY public.operations DROP CONSTRAINT fk_operations_balance;
       public          postgres    false    216    3212    215            $   3   x�3�tK,.I��O�2�t��/�(�2�t+M��2��MM�L��K����� �      %   4   x�Uɱ�0�vq�)�v��s�ηoD�K�\H���}��+B\B�x�.�	�      +   k   x�M�1
1D��>��ƒG�9�6�R\�ޟ�K������z��l��34�L�%���n�u����<4�, 7�_c���a9�������t�:<mb��б�!��/9��      &   j   x�]���0C�f�V�B�����Q�^J/�	[��e���!-�H�J"��B:�Hv����I�2��+Ů��T�`B�����N�@�A��@�t_t�D� �%$�      *      x������ � �     
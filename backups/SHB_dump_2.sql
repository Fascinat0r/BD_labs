PGDMP                 	        {            SmartHomeBudget    15.3    15.2                0    0    ENCODING    ENCODING        SET client_encoding = 'UTF8';
                      false                       0    0 
   STDSTRINGS 
   STDSTRINGS     (   SET standard_conforming_strings = 'on';
                      false                       0    0 
   SEARCHPATH 
   SEARCHPATH     8   SELECT pg_catalog.set_config('search_path', '', false);
                      false                       1262    48818    SmartHomeBudget    DATABASE     �   CREATE DATABASE "SmartHomeBudget" WITH TEMPLATE = template0 ENCODING = 'UTF8' LOCALE_PROVIDER = libc LOCALE = 'Russian_Russia.1251';
 !   DROP DATABASE "SmartHomeBudget";
                postgres    false            �            1259    48819    articles    TABLE     [   CREATE TABLE public.articles (
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
       public         heap    postgres    false            �            1259    48846    operations_id_seq    SEQUENCE     �   ALTER TABLE public.operations ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.operations_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);
            public          postgres    false    216                      0    48819    articles 
   TABLE DATA           ,   COPY public.articles (id, name) FROM stdin;
    public          postgres    false    214   �                 0    48822    balance 
   TABLE DATA           I   COPY public.balance (id, create_date, debit, credit, amount) FROM stdin;
    public          postgres    false    215          	          0    48825 
   operations 
   TABLE DATA           \   COPY public.operations (id, article_id, debit, credit, create_date, balance_id) FROM stdin;
    public          postgres    false    216   G                  0    0    articles_id_seq    SEQUENCE SET     ?   SELECT pg_catalog.setval('public.articles_id_seq', 407, true);
          public          postgres    false    217                       0    0    balance_id_seq    SEQUENCE SET     =   SELECT pg_catalog.setval('public.balance_id_seq', 66, true);
          public          postgres    false    218                       0    0    operations_id_seq    SEQUENCE SET     A   SELECT pg_catalog.setval('public.operations_id_seq', 176, true);
          public          postgres    false    219            r           2606    48829    articles pk_articles 
   CONSTRAINT     R   ALTER TABLE ONLY public.articles
    ADD CONSTRAINT pk_articles PRIMARY KEY (id);
 >   ALTER TABLE ONLY public.articles DROP CONSTRAINT pk_articles;
       public            postgres    false    214            t           2606    48831    balance pk_balance 
   CONSTRAINT     P   ALTER TABLE ONLY public.balance
    ADD CONSTRAINT pk_balance PRIMARY KEY (id);
 <   ALTER TABLE ONLY public.balance DROP CONSTRAINT pk_balance;
       public            postgres    false    215            v           2606    48833    operations pk_operations 
   CONSTRAINT     V   ALTER TABLE ONLY public.operations
    ADD CONSTRAINT pk_operations PRIMARY KEY (id);
 B   ALTER TABLE ONLY public.operations DROP CONSTRAINT pk_operations;
       public            postgres    false    216            w           2606    48865 !   operations fk_operations_articles    FK CONSTRAINT     �   ALTER TABLE ONLY public.operations
    ADD CONSTRAINT fk_operations_articles FOREIGN KEY (article_id) REFERENCES public.articles(id) ON DELETE CASCADE;
 K   ALTER TABLE ONLY public.operations DROP CONSTRAINT fk_operations_articles;
       public          postgres    false    214    216    3186            x           2606    48870     operations fk_operations_balance    FK CONSTRAINT     �   ALTER TABLE ONLY public.operations
    ADD CONSTRAINT fk_operations_balance FOREIGN KEY (balance_id) REFERENCES public.balance(id) ON DELETE CASCADE;
 J   ALTER TABLE ONLY public.operations DROP CONSTRAINT fk_operations_balance;
       public          postgres    false    216    215    3188               8   x�3�4�tK,.I��O�2�4�t��/�(2M8�JSs�SN�Ԕ��̼T�=... t*�         '   x�33�4202�5�"NCs#SNSSNCC�=... a�i      	   8   x�343�4�4崴��42�4202�5�"�?.C3��1����)��*���� k2     
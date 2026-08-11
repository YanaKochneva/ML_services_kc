--
-- PostgreSQL database dump
--

\restrict rde2512eKWQ0k0cWCkVc7vyHcYhCEZufUAuD8hnpH4zmkhnBqkMB5EJ4tnpeXc2

-- Dumped from database version 18.4
-- Dumped by pg_dump version 18.4

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: transactiontype; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.transactiontype AS ENUM (
    'DEPOSIT',
    'WITHDRAW'
);


ALTER TYPE public.transactiontype OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: balance; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.balance (
    id integer NOT NULL,
    user_id integer NOT NULL,
    credits numeric(15,2) NOT NULL
);


ALTER TABLE public.balance OWNER TO postgres;

--
-- Name: balance_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.balance_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.balance_id_seq OWNER TO postgres;

--
-- Name: balance_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.balance_id_seq OWNED BY public.balance.id;


--
-- Name: llm_configs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.llm_configs (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    version character varying(20) NOT NULL,
    cost_per_request integer NOT NULL,
    description character varying(500) NOT NULL,
    max_prompt_length integer NOT NULL,
    is_active boolean NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


ALTER TABLE public.llm_configs OWNER TO postgres;

--
-- Name: llm_configs_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.llm_configs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.llm_configs_id_seq OWNER TO postgres;

--
-- Name: llm_configs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.llm_configs_id_seq OWNED BY public.llm_configs.id;


--
-- Name: mltask; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.mltask (
    id integer NOT NULL,
    user_id integer NOT NULL,
    llm_config_id integer,
    input_data json,
    output_data json,
    status character varying(20) NOT NULL,
    cost numeric(10,2) NOT NULL,
    created_at timestamp without time zone NOT NULL,
    completed_at timestamp without time zone,
    error_message character varying(500),
    validation_errors json
);


ALTER TABLE public.mltask OWNER TO postgres;

--
-- Name: mltask_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.mltask_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.mltask_id_seq OWNER TO postgres;

--
-- Name: mltask_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.mltask_id_seq OWNED BY public.mltask.id;


--
-- Name: transaction; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.transaction (
    id integer NOT NULL,
    user_id integer NOT NULL,
    amount numeric(10,2) NOT NULL,
    transaction_type public.transactiontype NOT NULL,
    description character varying(255) NOT NULL,
    created_at timestamp without time zone NOT NULL,
    status character varying(20) NOT NULL
);


ALTER TABLE public.transaction OWNER TO postgres;

--
-- Name: transaction_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.transaction_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.transaction_id_seq OWNER TO postgres;

--
-- Name: transaction_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.transaction_id_seq OWNED BY public.transaction.id;


--
-- Name: user; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public."user" (
    id integer NOT NULL,
    username character varying(50) NOT NULL,
    email character varying(255) NOT NULL,
    password_hash character varying(255) NOT NULL,
    role character varying(20) NOT NULL,
    created_at timestamp without time zone NOT NULL,
    is_active boolean NOT NULL
);


ALTER TABLE public."user" OWNER TO postgres;

--
-- Name: user_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.user_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.user_id_seq OWNER TO postgres;

--
-- Name: user_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.user_id_seq OWNED BY public."user".id;


--
-- Name: balance id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.balance ALTER COLUMN id SET DEFAULT nextval('public.balance_id_seq'::regclass);


--
-- Name: llm_configs id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.llm_configs ALTER COLUMN id SET DEFAULT nextval('public.llm_configs_id_seq'::regclass);


--
-- Name: mltask id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.mltask ALTER COLUMN id SET DEFAULT nextval('public.mltask_id_seq'::regclass);


--
-- Name: transaction id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.transaction ALTER COLUMN id SET DEFAULT nextval('public.transaction_id_seq'::regclass);


--
-- Name: user id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."user" ALTER COLUMN id SET DEFAULT nextval('public.user_id_seq'::regclass);


--
-- Data for Name: balance; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.balance (id, user_id, credits) FROM stdin;
1	1	0.00
2	2	0.00
3	3	0.00
\.


--
-- Data for Name: llm_configs; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.llm_configs (id, name, version, cost_per_request, description, max_prompt_length, is_active, created_at, updated_at) FROM stdin;
1	Qwen2.5-1.5B-Instruct	1.0	2	Default LLM model	4000	t	2026-08-11 23:13:39.985186	2026-08-11 23:13:39.985186
\.


--
-- Data for Name: mltask; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.mltask (id, user_id, llm_config_id, input_data, output_data, status, cost, created_at, completed_at, error_message, validation_errors) FROM stdin;
1	1	\N	{"prompt": "Generate a poem"}	null	PENDING	1.00	2026-08-06 17:16:50.876467	\N	\N	[]
2	1	\N	{"prompt": "Write a story"}	null	PENDING	1.00	2026-08-06 17:16:50.876846	\N	\N	[]
\.


--
-- Data for Name: transaction; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.transaction (id, user_id, amount, transaction_type, description, created_at, status) FROM stdin;
1	1	100.00	DEPOSIT	Test deposit	2026-08-06 17:16:50.877041	pending
\.


--
-- Data for Name: user; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public."user" (id, username, email, password_hash, role, created_at, is_active) FROM stdin;
1	john_doe	john@gmail.com	hashed_password	USER	2026-08-06 17:16:50.876191	t
2	jane_smith	jane@gmail.com	hashed_password	USER	2026-08-06 17:16:50.876351	t
3	admin_user	admin@gmail.com	hashed_password	USER	2026-08-06 17:16:50.876408	t
\.


--
-- Name: balance_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.balance_id_seq', 3, true);


--
-- Name: llm_configs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.llm_configs_id_seq', 1, true);


--
-- Name: mltask_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.mltask_id_seq', 2, true);


--
-- Name: transaction_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.transaction_id_seq', 1, true);


--
-- Name: user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.user_id_seq', 3, true);


--
-- Name: balance balance_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.balance
    ADD CONSTRAINT balance_pkey PRIMARY KEY (id);


--
-- Name: balance balance_user_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.balance
    ADD CONSTRAINT balance_user_id_key UNIQUE (user_id);


--
-- Name: llm_configs llm_configs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.llm_configs
    ADD CONSTRAINT llm_configs_pkey PRIMARY KEY (id);


--
-- Name: mltask mltask_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.mltask
    ADD CONSTRAINT mltask_pkey PRIMARY KEY (id);


--
-- Name: transaction transaction_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.transaction
    ADD CONSTRAINT transaction_pkey PRIMARY KEY (id);


--
-- Name: user user_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."user"
    ADD CONSTRAINT user_pkey PRIMARY KEY (id);


--
-- Name: ix_user_email; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_user_email ON public."user" USING btree (email);


--
-- Name: ix_user_username; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_user_username ON public."user" USING btree (username);


--
-- Name: balance balance_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.balance
    ADD CONSTRAINT balance_user_id_fkey FOREIGN KEY (user_id) REFERENCES public."user"(id);


--
-- Name: mltask mltask_llm_config_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.mltask
    ADD CONSTRAINT mltask_llm_config_id_fkey FOREIGN KEY (llm_config_id) REFERENCES public.llm_configs(id);


--
-- Name: mltask mltask_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.mltask
    ADD CONSTRAINT mltask_user_id_fkey FOREIGN KEY (user_id) REFERENCES public."user"(id);


--
-- Name: transaction transaction_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.transaction
    ADD CONSTRAINT transaction_user_id_fkey FOREIGN KEY (user_id) REFERENCES public."user"(id);


--
-- PostgreSQL database dump complete
--

\unrestrict rde2512eKWQ0k0cWCkVc7vyHcYhCEZufUAuD8hnpH4zmkhnBqkMB5EJ4tnpeXc2


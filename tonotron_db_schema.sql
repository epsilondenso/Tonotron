--
-- PostgreSQL database dump
--

\restrict cJOSmvawkQQoDI7LrmGQKvsmZ2GnBhxbSbRaNt9MzlOSnK7Fx1RaX0KvLbq6taL

-- Dumped from database version 18.6
-- Dumped by pg_dump version 18.6

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

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: assignments; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.assignments (
    assignment_id integer NOT NULL,
    housework_id integer NOT NULL,
    roomie_id integer NOT NULL,
    due_date date,
    completed_at timestamp with time zone,
    assigned_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    completed boolean DEFAULT false NOT NULL
);


ALTER TABLE public.assignments OWNER TO postgres;

--
-- Name: housework; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.housework (
    housework_id integer NOT NULL,
    housework_name character varying(50) NOT NULL
);


ALTER TABLE public.housework OWNER TO postgres;

--
-- Name: roomies; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.roomies (
    roomie_id integer NOT NULL,
    roomie_name character varying(15) NOT NULL,
    last_name character varying(15) NOT NULL,
    phone_number character varying(15) NOT NULL,
    telegram_id bigint,
    turn integer NOT NULL,
    is_admin boolean DEFAULT false NOT NULL
);


ALTER TABLE public.roomies OWNER TO postgres;

--
-- Name: rotation_log; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.rotation_log (
    rotation_id integer NOT NULL,
    housework_id integer NOT NULL,
    rotated_at timestamp without time zone NOT NULL
);


ALTER TABLE public.rotation_log OWNER TO postgres;

--
-- Name: rotation_log_rotation_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.rotation_log_rotation_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.rotation_log_rotation_id_seq OWNER TO postgres;

--
-- Name: rotation_log_rotation_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.rotation_log_rotation_id_seq OWNED BY public.rotation_log.rotation_id;


--
-- Name: rotation_log rotation_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.rotation_log ALTER COLUMN rotation_id SET DEFAULT nextval('public.rotation_log_rotation_id_seq'::regclass);


--
-- Name: assignments assignments_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.assignments
    ADD CONSTRAINT assignments_pkey PRIMARY KEY (assignment_id);


--
-- Name: housework housework_housework_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.housework
    ADD CONSTRAINT housework_housework_name_key UNIQUE (housework_name);


--
-- Name: housework housework_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.housework
    ADD CONSTRAINT housework_pkey PRIMARY KEY (housework_id);


--
-- Name: roomies roomies_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.roomies
    ADD CONSTRAINT roomies_pkey PRIMARY KEY (roomie_id);


--
-- Name: roomies roomies_turn_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.roomies
    ADD CONSTRAINT roomies_turn_key UNIQUE (turn);


--
-- Name: rotation_log rotation_log_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.rotation_log
    ADD CONSTRAINT rotation_log_pkey PRIMARY KEY (rotation_id);


--
-- Name: one_active_assignment_per_housework; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX one_active_assignment_per_housework ON public.assignments USING btree (housework_id) WHERE (completed_at IS NULL);


--
-- Name: rotation_log_housework_rotated_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX rotation_log_housework_rotated_idx ON public.rotation_log USING btree (housework_id, rotated_at);


--
-- Name: assignments assignments_housework_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.assignments
    ADD CONSTRAINT assignments_housework_id_fkey FOREIGN KEY (housework_id) REFERENCES public.housework(housework_id);


--
-- Name: assignments assignments_roomie_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.assignments
    ADD CONSTRAINT assignments_roomie_id_fkey FOREIGN KEY (roomie_id) REFERENCES public.roomies(roomie_id);


--
-- Name: rotation_log rotation_log_housework_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.rotation_log
    ADD CONSTRAINT rotation_log_housework_id_fkey FOREIGN KEY (housework_id) REFERENCES public.housework(housework_id);


--
-- PostgreSQL database dump complete
--

\unrestrict cJOSmvawkQQoDI7LrmGQKvsmZ2GnBhxbSbRaNt9MzlOSnK7Fx1RaX0KvLbq6taL


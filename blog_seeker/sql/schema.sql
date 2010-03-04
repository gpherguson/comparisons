-- More info on Postgres' tsearch is at:
--
-- http://www.postgresql.org/docs/8.3/static/textsearch-controls.html

-- start by creating the database itself...
--
-- create database blogsearch;

drop table blogfeeds cascade;
create table blogfeeds(
    id         serial primary key,
    blog_url   text not null unique,  -- pointer to the blog
    feed_url   text unique,           -- pointer to the feed for the blog
    created_on timestamp with time zone not null default now(),
    updated_at timestamp with time zone not null default now(),
    enabled    boolean default false,
    language   varchar(2) default 'en'
);

drop table blogarticles;
create table blogarticles(
    id             bigserial primary key,
    blog_id        integer not null references blogfeeds(id) on delete cascade,  -- fkey to the parent record in the blogfeeds table.
    created_on     timestamp with time zone not null default now(),
    article_url    text not null unique, -- url to the blog entry pointed to by this feed item.
    title          text,                 -- the title of the feed item.
    content        text,                 -- the content of the feed item, which should be a clean version of the article.
    article        text,                 -- the blog article itself.
    article_vector tsvector              -- tsvector for searching the article text.
);
CREATE INDEX article_vector_idx ON blogarticles USING gin(article_vector);

-- we need to use a trigger to force updates of the article_vector field,
-- otherwise we have to write it into the insert/update statements. Writing
-- them into the statements is more likely to be forgotten, but we gotta
-- remember to reinitialize the trigger if we change this table.
CREATE TRIGGER articletsvectorupdate BEFORE INSERT OR UPDATE
ON blogarticles FOR EACH ROW EXECUTE PROCEDURE
tsvector_update_trigger(article_vector, 'pg_catalog.english', title, feed, article);

-- create a table for temporary storage of urls at google that contain multiple
-- other urls for blogs.
drop table additional_feeds;
create table additional_feeds (
	id serial primary key,
	url text
);


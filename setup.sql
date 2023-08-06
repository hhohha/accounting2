-- mysql --user honza --password
-- use accounting2
--------------
-- mysql -p accounting2 < setup.sql

drop table if exists classifications;

create table classifications (
    id int primary key,
    type int,
    name varchar(256)
);

-- mysql --user honza --password
-- use accounting2
--
-- mysql -p accounting2 < setup.sql
drop table if exists signatures;
drop table if exists tag_links;
drop table if exists transactions;
drop table if exists classifications;

create table classifications (
    id int primary key,
    type int,
    name varchar(256)
);

create table signatures (
    id int,
    cls_id int,
    value varchar(256),
    foreign key (cls_id) references classifications (id)
);

create table transactions (
    id int primary key,
    dueDate date not null,
    amount float not null,
    bank varchar(20) not null,
    category int,
    trType int,
    writeOffDate date,
    toAccount varchar(20),
    toAccountName varchar(128),
    originalAmount float,
    currency varchar(3),
    rate float,
    variableSymbol varchar(20),
    constantSymbol varchar(20),
    specificSymbol varchar(20),
    transactionIdentifier varchar(64),
    systemDescription varchar(128),
    senderDescription varchar(128),
    addresseeDescription varchar(128),
    AV1 varchar(128),
    AV2 varchar(128),
    AV3 varchar(128),
    AV4 varchar(128),
    foreign key (category) references classifications(id),
    foreign key (trType) references classifications(id)
);

create table tag_links (
    trans_id int,
    cls_id int,
    foreign key (trans_id) references transactions(id),
    foreign key (cls_id) references classifications(id)
);

-- test data
insert into classifications values (1, 0, 'credit');
insert into classifications values (2, 0, 'card payment');
insert into classifications values (3, 0, 'cash withdrawal');
insert into classifications values (4, 1, 'food');
insert into classifications values (5, 1, 'clothes');
insert into classifications values (6, 1, 'household');
insert into classifications values (7, 1, 'transport');
insert into classifications values (8, 2, 'kaufland');
insert into classifications values (9, 2, 'billa');
insert into transactions (id, dueDate, amount, bank, category, trType) values (1, '2015-01-01', 100, 'KB', 4, 1);
insert into transactions (id, dueDate, amount, bank, category, trType) values (2, '2015-01-02', 200, 'MB', 5, 2);
insert into transactions (id, dueDate, amount, bank, category, trType) values (3, '2015-01-03', 300, 'KB', 6, 3);
insert into transactions (id, dueDate, amount, bank, category, trType, av1) values (5, '2015-01-05', 500, 'MB', 6, 3, 'some data');
insert into tag_links (trans_id, cls_id) values (1, 8);
insert into tag_links (trans_id, cls_id) values (1, 9);

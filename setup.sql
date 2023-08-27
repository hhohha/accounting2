-- mysql --user honza --password
-- use accounting2
--
-- mysql -p accounting2 < setup.sql
drop table if exists settings;
drop table if exists signatures;
drop table if exists tag_links;
drop table if exists transactions;
drop table if exists classifications;

create table settings (
    sKey varchar(32) primary key not null,
    sValue varchar(256)
);

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
    amount int not null,
    bank varchar(20) not null,
    category int,
    trType int,
    writeOffDate date,
    toAccount varchar(32),
    toAccountName varchar(128),
    originalAmount int,
    originalCurrency varchar(3),
    rate float,
    variableSymbol varchar(20),
    constantSymbol varchar(20),
    specificSymbol varchar(20),
    transactionIdentifier varchar(64),
    systemDescription varchar(128),
    senderDescription varchar(512),
    addresseeDescription varchar(128),
    AV1 varchar(256),
    AV2 varchar(256),
    AV3 varchar(256),
    AV4 varchar(256),
    signature varchar(1024),
    foreign key (category) references classifications(id),
    foreign key (trType) references classifications(id)
);

create table tag_links (
    trans_id int,
    cls_id int,
    foreign key (trans_id) references transactions(id),
    foreign key (cls_id) references classifications(id)
);
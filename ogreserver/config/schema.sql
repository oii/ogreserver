drop table if exists users;
create table users (
	  username string primary key,
	  password string not null,
	  email string not null
);

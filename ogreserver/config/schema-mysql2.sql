START TRANSACTION;

DROP DATABASE IF EXISTS ogre;
CREATE DATABASE ogre;
USE ogre;

CREATE TABLE user (
	id INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT, 
	username VARCHAR(80) NOT NULL, 
	password VARCHAR(256) NOT NULL,
	email VARCHAR(120) NOT NULL,
	display_name VARCHAR(50) NULL,
	api_key_expires VARCHAR(23) NULL,
	points INTEGER NOT NULL DEFAULT 0
);

INSERT INTO user (username, password, email, display_name) 
VALUES
	('mafro','$pbkdf2-sha256$8487$hRCC8F7LuRcipNS6F6J0Lg$C0scVARwUBq4hZ0ct9sUYLrfATdh10fpv1tpL/6T57Y','m@mafro.net','mafro'),
	('goff','$pbkdf2-sha256$8471$QOj9P4fwfm8NodS6N2YsBQ$qK.UMk3xFEQRjCXpFFBTe0wQwEqHmbQUogNwZ2UGPEU','geoffpaddison@gmail.com','goff'),
	('steve','$pbkdf2-sha256$8448$mVPKWesdI.Tce4.R8r7X.g$797F0PuuwHHxqvoXih.FwCu1x/YHFOlSvM2OnElQ0B8','steve@little-steve.co.uk','steve'),
	('holden','$pbkdf2-sha256$8304$XcuZ05oTghAipLQWIgTAGA$2s8gn8E8BJ04xNRnov2SLQ/vxAIh3ISdPslZSK6A0iY','thomasjohnholden@gmail.com','holden'),
	('bronx','$pbkdf2-sha256$7924$7t1bC.H8HwMAQMg5B2BMqQ$e7y2jR5.80g8Beozo7u7SnbyOlMWmaYkYcGYx.60oMc','mike.brookes@gmail.com','bronx'),
	('davies','$pbkdf2-sha256$7381$FqI0pnTOmRNiLEXo/R8DYA$ZI/nyv59JGh.CY5.7AHUPMtUPnNi41YO7RQDR8/LRc0','matt.davies1@gmail.com','davies'),
	('beeny','$pbkdf2-sha256$8364$HaO0lhKiNEbI2ZtTSonx/g$LTy/Q5XPtKtug0Y9Q8c52aXVxCqwjtWyYcPlqBNIecw','beenymanus@googlemail.com','beeny'),
	('damo','$pbkdf2-sha256$7782$hDDG.J.TMoZQqhXC2DtnTA$F73e/zk39EDWFhmDz7fS00x3sBLvjtfJZ/65C0MwFyw','damianbillingsley@yahoo.co.uk','damo'),
	('pooch','$pbkdf2-sha256$7760$IMTY27u3NoYwxjhHqBUCoA$c99Ia2k1SusTvYgvTSJWbuziYlYeYenHJLoV2.pIm7k','nickeshaw@hotmail.co.uk','pooch'),
	('tc','$pbkdf2-sha256$7409$DwEAwFirdU4phVDqvRci5A$rtkq1AgLxfT5FRWRzxIislMYeI/7PSzPhWyhXYT9UiM','tom@cobuso.co.uk','tc');

CREATE TABLE user_badge (
	id INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT, 
	user_id INTEGER NOT NULL,
	badge INTEGER NOT NULL,
   	been_alerted BOOLEAN NOT NULL DEFAULT 0,
	UNIQUE KEY idx (user_id, badge)
);

CREATE TABLE log (
	id INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT, 
	user_id INTEGER NOT NULL,
	api_session_key VARCHAR(256), 
	timestamp DATE,
	type VARCHAR(30),
   	data VARCHAR(200)
);


CREATE TABLE ogre_books (
	id INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT, 
	authortitle VARCHAR(500),
	users VARCHAR(200),
	formats VARCHAR(200),
	tags VARCHAR(200),
	sdbkey VARCHAR(256),
	UNIQUE KEY idx (sdbkey)
);

CREATE TABLE ogre_formats (
	id INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT, 
	authortitle VARCHAR(500),
	format VARCHAR(20),
	version_count INTEGER,
	sdbkey VARCHAR(256),
	UNIQUE KEY idx (authortitle, format)
);

CREATE TABLE ogre_versions (
	id INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT, 
	authortitle VARCHAR(500),
	version INTEGER,
	format VARCHAR(20),
	user VARCHAR(200),
	size INTEGER,
	filehash VARCHAR(256),
   	uploaded BOOLEAN,
   	dedrm BOOLEAN,
	sdbkey VARCHAR(256),
	UNIQUE KEY idx (authortitle, version, format)
);

CREATE TABLE ogre_book_comments (
	id INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT, 
	authortitle VARCHAR(500),
	sdbkey VARCHAR(256),
	username VARCHAR(50),
	comment VARCHAR(4000),
	UNIQUE KEY idx (sdbkey, username)
);

CREATE TABLE ogre_book_ratings (
	id INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT, 
	authortitle VARCHAR(500),
	sdbkey VARCHAR(256),
	username VARCHAR(50),
	rating INTEGER,
	UNIQUE KEY idx (sdbkey, username)
);

CREATE TABLE ogre_book_tags (
	id INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT, 
	authortitle VARCHAR(500),
	sdbkey VARCHAR(256),
	tag VARCHAR(50),
	UNIQUE KEY idx (sdbkey)
);

COMMIT;

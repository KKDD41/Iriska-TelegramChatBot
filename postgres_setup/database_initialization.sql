CREATE TABLE IF NOT EXISTS users (id INT PRIMARY KEY, username TEXT);
CREATE TABLE IF NOT EXISTS alarms (id INT, user_id INT, time_to_notify TIMESTAMP, notification_message TEXT);
CREATE TABLE IF NOT EXISTS mood_poll (id INT, user_id INT, answers VARCHAR(3), date DATE);
CREATE TABLE IF NOT EXISTS relapse_poll (id INT, user_id INT, answers VARCHAR(3), date DATE);
CREATE TABLE IF NOT EXISTS month_statistics (date DATE, user_id INT, ethanol_equivalent REAL);

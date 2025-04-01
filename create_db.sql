CREATE TYPE location AS ENUM ('cjl', 'forbes', 'gradcollege', 'roma', 'whitman', 'yeh');
CREATE TYPE meal AS ENUM ('breakfast', 'lunch', 'dinner');

-- Recipe_Reports rows each represent a menu item at a specific dining hall, 
-- for a specific meal, for a specific day. These rows include all of the 
-- nutritional information provided by menus.princeton.edu
CREATE TABLE Recipe_Reports (
	report_Id uuid PRIMARY KEY,
	report_Date date NOT NULL,
	report_Location location NOT NULL,
	report_Meal meal NOT NULL,

	recipe_Name varchar(255) NOT NULL,

	portion_Info varchar(255) NOT NULL,
	protein float8,
	fat float8,
	carbs float8,
	fiber float8,
	potassium float8,
	cholesterol float8,
	calories float8,
	sugar float8,
	sodium float8,
	vitamin_A float8,
	vitamin_B float8
);

-- Users tracks users of the app. This will likely be updated in the future 
-- to enable authentication via Google CAS and or university CAS systems.
CREATE TABLE Users (
	user_Id uuid PRIMARY KEY,
	username varchar(255) UNIQUE NOT NULL,
	email varchar(255) UNIQUE NOT NULL,
	password_Hash varchar(255),
	created_At timestamp NOT NULL
);

-- Food_logs link users to recipe reports on each day.
-- This allows a user to track what they ate in a day and see the nutrition info. 
CREATE TABLE Food_Logs (
	log_Id uuid PRIMARY KEY,
	user_Id uuid NOT NULL,
	report_Id uuid NOT NULL,
	log_Date date NOT NULL,
	FOREIGN KEY (user_Id) REFERENCES Users(user_Id) ON DELETE CASCADE,
	FOREIGN KEY (report_Id) REFERENCES Recipe_Reports(report_Id)
);
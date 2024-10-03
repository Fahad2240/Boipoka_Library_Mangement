# Boipoka_Library_Management
# 1. Project Overview
  Project Name: Boipoka - Book Library Management System
		
The Boipoka application is designed to facilitate the management of a library system, allowing users to subscribe, borrow, and manage books based on their subscription levels. It features role-based access to ensure that regular users and administrators can efficiently perform their respective tasks. The system incorporates business logic for managing subscriptions, borrowing limits, and the status of books, providing a robust platform for library management.


# 2. Setup Instructions
   a. **Install python-3.11.7**
   b. **git clone https://github.com/Fahad2240/Boipoka_Library_Mangement**
    then run the followings in the project directory which is fetched from github
   c. run the build.sh as chmod a+x build.sh if you are in Windows then go to GitBash 
	and run assuming your project in this directory
 	```
		cd /c/Users/User/Desktop/Book_Library_System
		./build.sh
	   	chmod a+x build.sh			
	```  					
	    				       ### Cloud Setup Instructions (Render PostgreSQL)
1. **Database URL**: Your Django project should already have a `DATABASE_URL` environment variable set up on Render's dashboard. The `DATABASE_URL` contains all the necessary connection info to your PostgreSQL database.
   - The connection string will look something like: `postgres://username:password@hostname:port/dbname`.
   - Render should automatically inject this environment variable into your Django app when deployed.

2. **Database Configuration in Django**:
   - In your `settings.py`, make sure that you’re reading the `DATABASE_URL` from the environment. Typically, you can use `dj-database-url` for this:
     ```python
     import dj_database_url
     DATABASES = {
         'default': dj_database_url.config(conn_max_age=600)
     }
     ```
3. **Deploying**: On Render, when you deploy your app, PostgreSQL will be automatically connected through the `DATABASE_URL` environment variable, so you don't need to configure anything further for cloud deployment.

### Local Development Setup
1. **Install PostgreSQL Locally**:
   - To develop locally, install PostgreSQL on your machine. You can install it using the following commands:
     - **On Windows**: Download and install PostgreSQL from [https://www.postgresql.org/download/windows/](https://www.postgresql.org/download/windows/).

2. **Create a Local Database**:
   Create a Database using pgAdmin:
	If you prefer using pgAdmin to create the database, follow these steps:
	Open pgAdmin:
	
	Launch pgAdmin and connect to your PostgreSQL server.
	Create a New Database:
	
	In pgAdmin, expand your server in the left-hand sidebar, right-click on Databases, and select Create > Database.
	In the Create Database dialog:
	Enter the Database name (e.g., your_db_name).
	Set the Owner (choose the PostgreSQL user, such as postgres).
	Click Save to create the database.
	Verify the Database:
	
	Check under Databases in the left-hand sidebar to ensure your new database is listed.

3. **Update `settings.py` for Local Development**:
   - For local development, modify the `DATABASES` configuration in `settings.py` to use your local PostgreSQL instance:
     ```python
     DATABASES = {
         'default': {
             'ENGINE': 'django.db.backends.postgresql',
             'NAME': 'your_db_name',
             'USER': 'your_username',
             'PASSWORD': 'your_password',
             'HOST': 'localhost',
             'PORT': '5432',
         }
     }
     ```

4. **Migrate the Database**:
   - Run the following commands to set up your local database:
     ```bash
     python manage.py migrate
     python manage.py createsuperuser  # To create an admin account
     ```

5. **Start the Development Server**:
   - Finally, run the development server:
     ```bash
     python manage.py runserver
     ```
# 3. Key Features

**User Authentication & Role Management:**
-User registration and login functionality.
-Two roles: Admin and Regular Users.
-Password hashing for security.
**Subscription Management:**
-Three subscription tiers: Basic, Premium, VIP.
-Users can upgrade or downgrade subscriptions.
-Manage subscription expiry and renewals.
**Content Management (Books):**
-Admins can manage book entries (CRUD operations).
-Use Google Books API to automatically fetch book metadata.
**Borrowing System:**
-Users can borrow books based on their subscription level.
-Implement due dates and overdue management.
-Admins can view overdue books and manage penalties.
**Book Availability:**
-Only books that are not borrowed are available for borrowing.
-Change book status based on borrowing actions.
**Bonus Features:**
-Integrate Google Books API for enhanced book details.
      						
      						

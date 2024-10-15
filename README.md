# Boipoka_Library_Management
# 1. Project Overview
  Project Name: Boipoka - Book Library Management System
		

The Boipoka application is designed to facilitate library management by allowing users to subscribe, borrow, and manage books according to their subscription levels. It features a user-friendly interface, starting with a welcoming index view where users can easily register or log in. Available books are displayed in a grid format, showcasing their titles, authors, and availability, and users can view detailed information about each book by clicking on the book image. If a user currently has no subscription, the book details page will present a "Create Subscription" button, allowing them to choose an appropriate subscription plan. After selecting a subscription, users can borrow books by clicking the "Borrow Book" button; once borrowed, the book will be marked as unavailable until it is returned, and the remaining copies displayed on the book list page will be updated accordingly.

Additionally, the navigation bar displays the user's subscription name and end date. If the end date has passed, a message indicating that the subscription has expired will be shown, along with a "Renew Subscription" button, which renews the subscription for an additional 30 days upon clicking. Users can also easily upgrade or downgrade their subscription by selecting the "Choose Subscription" button from the navigation bar while on either the book list or book details page. This action will change the user's subscription type, thereby adjusting their borrowing limit, which is reflected in both the book list and book details pages.

Role-based access ensures that both regular users and administrators can efficiently perform their tasks. Administrators have special access privileges through a created superuser account, which can be logged in using the username "admin" and the password "admin." From the navigation bar, admins can manage users and add new books. They can click on any book image displayed in the book list to access the book details page, where they have the option to edit or delete the book.

When the admin clicks the "Handle User" button, they can view a list of all users. By selecting a particular user, the admin can see detailed information such as the user’s name, subscription type, and maximum books allowed if the user has an active subscription; otherwise, it will indicate "No Subscription." If a user has a subscription, the admin can view and edit the subscription's start and end dates, along with the user's borrowed books, displaying the book names and their respective due dates, which can also be edited easily. The admin also has the ability to edit or delete user accounts as needed.

Additionally, the admin can manage overdue books, allowing them to send reminders, complete with penalties, via email by clicking the "Send Reminder" button. Any changes made to a user's subscription end date will be reflected in the navigation bar for that specific user. If needed, the admin can delete a subscription by clicking the "Delete Subscription" button. Furthermore, if the admin wishes to modify a due date to mark it as overdue for a user and send a reminder, this action will be accurately reflected in the user’s details page accordingly. This comprehensive administrative functionality ensures efficient user management and maintains the integrity of the borrowing system while providing a robust platform for effective library management.

The Reissue Book feature notifies users when a borrowed book’s due date is approaching. If the current time plus one day exceeds the due date, an alert will appear on the book image on the Book List page. Clicking the image redirects the user to the Book Details page, where they see an alert and the option to Reissue the book to extend the due date. Upon clicking, the user receives a confirmation message stating their reissue request has been sent to the admin. The admin can then review and approve the request from the User Details page in their session. If approved, the alert is removed, and the due date is updated, providing a seamless way for users to manage and extend their borrowed books.

Additionally, the Damaged/Lost Book Report feature allows users to report a borrowed book as lost or damaged directly from the Book List page by clicking the Report Damage/Lost option. Once the user submits this report, a request is sent to the admin, reflected on the Book List page. After reporting, the user cannot return the book, as library management does not accept damaged or lost books into the inventory. Instead, a fine of 500 TK is applied, and the option to Pay Now replaces the Return Book button. Clicking Pay Now changes the status to "Wait for Approval," notifying the admin of the pending payment. If the admin approves the payment, the borrowing instance is deleted, and the count of available copies decreases until a new copy is added to the inventory. The damage information is preserved in a separate model called DamagedorLostHistory, allowing the admin to record damaged book histories even after the borrowing information has been removed.

The Suspension of Subscription feature activates when a user has fewer than three unpaid reports for damaged or lost books that have not been approved for payment by the admin, and whose borrowing instances have been deleted. If any of these reports remain unpaid for over 24 hours, the subscription will be automatically suspended by the admin. During this suspension, the user is redirected to a suspension page instead of the Book List, where they cannot borrow books or perform any other actions. Instead, the page displays a message indicating that their account is suspended due to unpaid damages, showing both unpaid and paid reports. For unpaid reports, a Pay Now option is available. If the user clicks it, they receive a notification that their payment has been received and that they should wait for approval.

The admin has the ability to approve payments and reactivate the subscription, restoring the user’s access to borrowing books and other functionalities. However, if the user has three unpaid reports, their subscription will be suspended, and they will be redirected to the login page. Attempts to log in will be blocked, accompanied by a pop-up message stating, "You are suspended; please contact the admin." If the admin does not reactivate the user’s subscription, their login session will remain blocked, ensuring that users who have unresolved issues cannot access the system until they are addressed.

The Readlist History feature will provide users with a comprehensive list of all borrowed books, regardless of their return status, displaying a returned label with the return date for books that have been returned, while outstanding books will be marked as not returned. Additionally, users will have the option to mark any book as unread, indicating it is still incomplete. To enhance usability, a search functionality will allow users to filter their read list by book title or specify a date range (e.g., [Start Date, End Date]) to locate books borrowed within a particular timeframe. To improve accessibility, a Readlist History button will be added to the navigation bar, enabling users to easily navigate to their reading history with a single click. This update will allow users to quickly view their list of borrowed books and utilize the search functionality without the need to navigate through multiple pages, thereby streamlining their overall experience.

# 2. Setup Instructions
   a. **Install python-3.11.7**
   b. **git clone https://github.com/Fahad2240/Boipoka_Library_Mangement**
    then run the followings in the project directory which is fetched from github
   c. run the build.sh as chmod a+x build.sh if you are in Windows then go to GitBash 
	and run assuming your project in this directory
```bash
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
     # Import dj-database-url at the beginning of the file.
     import dj_database_url
     # Replace the SQLite DATABASES configuration with PostgreSQL:
     DATABASES = {
       'default': dj_database_url.config(
          # Replace this value with your local database's connection string.
          default='postgresql://postgres:postgres@localhost:5432/mysite',
          conn_max_age=600
       )
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
- User registration and login functionality.
- Two roles: Admin and Regular Users.
- Password hashing for security.

**Subscription Management:**
- Three subscription tiers: Basic, Premium, VIP.
- Users can upgrade or downgrade subscriptions.
- Manage subscription expiry and renewals.

**Content Management (Books):**
- Admins can manage book entries (CRUD operations).
- Use Google Books API to automatically fetch book metadata.

**Borrowing System:**
- Users can borrow books based on their subscription level.
- Implement due dates and overdue management.
- Admins can view overdue books and manage penalties.

**Book Availability:**
- Only books that are not borrowed are available for borrowing.
- Change book status based on borrowing actions.

**Bonus Features:**
- Integrate Google Books API for enhanced book details.

## Development Guide

### Prerequisites
- Python 3.11.7
- Django 5.1.1
- PostgreSQL 17
- Virtualenv (recommended)

### Installation Instructions
1. **Clone the Repository**:
   ```bash
   git clone [https://github.com/Fahad2240/Boipoka_Library_Mangement]
   cd Boipoka_Library_Mangement
   ```
2. **Set Up a Virtual Environment**
```
python -m venv venv
venv/bin/activate 
```
3. **Install dependencies:**
 ``` bash
  pip install -r requirements.txt
```
4. **Set up the database:**
- Run migrations to set up the database schema:
```bash
python manage.py migrate
```
5. **Create a superuser (optional for admin access):**
```bash
python manage.py createsuperuser
```
6. **Running the Development Server**
- Start the development server with:
```bash
python manage.py runserver
```
 ### You can access the application at http://127.0.0.1:8000/.
```DATABASES = {
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
### Cloud Setup Instructions (Render PostgreSQL)
1. **Database URL**: Your Django project should already have a `DATABASE_URL` environment variable set up on Render's dashboard. The `DATABASE_URL` contains all the necessary connection info to your PostgreSQL database.
   - The connection string will look something like: `postgres://username:password@hostname:port/dbname`.
   - Render should automatically inject this environment variable into your Django app when deployed.

2. **Database Configuration in Django**:
   - In your `settings.py`, make sure that you’re reading the `DATABASE_URL` from the environment. Typically, you can use `dj-database-url` for this:
     ```python
     # Import dj-database-url at the beginning of the file.
     import dj_database_url
     # Replace the SQLite DATABASES configuration with PostgreSQL:
     DATABASES = {
       'default': dj_database_url.config(
          # Replace this value with your local database's connection string.
          default='postgresql://postgres:postgres@localhost:5432/mysite',
          conn_max_age=600
       )
     }
     ```
   

      						

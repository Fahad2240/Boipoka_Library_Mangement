from datetime import timedelta
from django.utils import timezone
from unittest.mock import Mock, patch
from django.test import TestCase
from django.urls import reverse
from boipoka_app.forms import CustomUserCreationForm
from django.contrib.auth import get_user_model
from .models import Book, Borrowing, Subscription
from .views import fetch_books_data, create_books_in_db
import json

User = get_user_model()

class BoipokaAppTests(TestCase):

    # Test the 'index' view
    def test_index_view(self):
        """
        Test the index view returns a 200 status code and the correct template.
        """
        response = self.client.get(reverse('boipoka_app:index'))  # Reverse the 'index' URL
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'boipoka_app/index.html')

    # Test the 'register' view for a GET request
    def test_register_view_get(self):
        """
        Test the register view with a GET request returns a 200 status code
        and the registration form.
        """
        response = self.client.get(reverse('boipoka_app:register'))  # Reverse the 'register' URL
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'boipoka_app/register.html')
        self.assertIsInstance(response.context['form'], CustomUserCreationForm)

    # Test the 'register' view for a POST request with valid data
    def test_register_view_post_invalid(self):
        form_data = {
            'username': '',  # Invalid data
            'password1': 'short',  # Invalid password
            'password2': 'short',
            'email': '',  # Invalid email
        }
        
        response = self.client.post(reverse('boipoka_app:register'), form_data)
        
        # Debugging output
        print(f'Status Code: {response.status_code}')
        print(f'Response Content: {response.content.decode()}')  # Decode to string for readability
        
        # Check that the response is OK (200)
        self.assertEqual(response.status_code, 200)
        
        # Ensure the form is in the context
        form = response.context.get('form')
        self.assertIsNotNone(form, "Form not found in response context.")

        # Assert the errors on the form
        self.assertFormError(response, 'form', 'username', 'This field is required.') 
        self.assertFormError(response, 'form', 'email', 'This field is required.') 
        self.assertFormError(response, 'form', 'password1', 'This password is too short. It must contain at least 8 characters.')  # Adjust based on actual error message




    # Test the 'register' view for a POST request with invalid data
    def test_register_view_post_valid(self):
        form_data = {
            'username': 'testuser',
            'password1': 'secure_password',
            'password2': 'secure_password',
            'email': 'testuser@example.com',  # Ensure email is included
        }
        response = self.client.post(reverse('boipoka_app:register'), data=form_data)

        # Check if the user was created
        self.assertTrue(User.objects.filter(username='testuser').exists(), "User was not created.")
        self.assertRedirects(response, reverse('boipoka_app:login'))  # Adjust the redirect target if necessary
    # Test the 'register' view for a POST request with a missing field
    def test_register_view_post_missing_field(self):
        """
        Test the register view with a POST request where a required field is missing.
        It should not create a user and should show form validation errors.
        """
        form_data = {
            'username': '',  # Missing username
            'password1': 'TestPassword123',
            'password2': 'TestPassword123',
        }
        response = self.client.post(reverse('boipoka_app:register'), form_data)

        # Ensure no user was created
        self.assertFalse(User.objects.filter(username='').exists())

        # Check that the form re-renders with errors
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'boipoka_app/register.html')
        self.assertIsInstance(response.context['form'], CustomUserCreationForm)
        self.assertTrue(response.context['form'].errors)

    # Test the 'register' view when a user is already authenticated
    def test_register_view_authenticated_user(self):
        """
        Test the register view when the user is already authenticated.
        The user should be redirected away from the registration page.
        """
        # Create and log in a test user
        user = User.objects.create_user(username='testuser', password='TestPassword123')
        self.client.login(username='testuser', password='TestPassword123')

        # Test accessing the register page while logged in
        response = self.client.get(reverse('boipoka_app:register'))

        # Assert that the user is redirected since they're already logged in
        self.assertRedirects(response, '/')


class LoginViewTests(TestCase):
    
    def setUp(self):
        # Create a user for testing
        self.username = 'testuser'
        self.password = 'testpassword'
        self.user = User.objects.create_user(username=self.username, password=self.password)

    def test_login_view_success(self):
        """Test that a user can log in successfully."""
        response = self.client.post(reverse('boipoka_app:login'), {
            'username': self.username,
            'password': self.password
        })
        self.assertRedirects(response, reverse('boipoka_app:book_list'))
        self.assertTrue(response.wsgi_request.user.is_authenticated)  # User should be authenticated

    def test_login_view_invalid_credentials(self):
        """Test that login fails with invalid credentials."""
        response = self.client.post(reverse('boipoka_app:login'), {
            'username': 'wronguser',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid credentials')  # Check for the error message
        self.assertFalse(response.wsgi_request.user.is_authenticated)  # User should not be authenticated

    def test_login_view_get(self):
        """Test that GET requests return the login page."""
        response = self.client.get(reverse('boipoka_app:login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'boipoka_app/login.html')  # Check the template used

class LogoutViewTests(TestCase):
    
    def setUp(self):
        """Create a user and log them in for testing."""
        self.username = 'testuser'
        self.password = 'testpassword'
        self.user = User.objects.create_user(username=self.username, password=self.password)
        self.client.login(username=self.username, password=self.password)  # Log in the user

    def test_logout_view(self):
        """Test that the user can log out successfully."""
        response = self.client.get(reverse('boipoka_app:logout'))
        self.assertRedirects(response, reverse('boipoka_app:index'))  # Ensure it redirects to the index
        self.assertFalse(response.wsgi_request.user.is_authenticated)  # User should not be authenticated



class BookDataTests(TestCase):
    """Test cases for fetching and creating book data."""

    @patch('boipoka_app.views.requests.get')
    def test_fetch_books_data_success(self, mock_get):
        """Test fetch_books_data for a successful API call."""
        # Mocking the API response
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "items": [
                {
                    "volumeInfo": {
                        "title": "Test Book",
                        "authors": ["Author One", "Author Two"],
                        "description": "A test description.",
                        "imageLinks": {
                            "thumbnail": "http://example.com/test_book_thumbnail.jpg"
                        }
                    }
                }
            ]
        }

        # Mocking the image response
        mock_image_response = Mock()
        mock_image_response.status_code = 200
        mock_image_response.content = b'This is a mock image content'  # Provide bytes-like content
        with patch('boipoka_app.views.requests.get', side_effect=[mock_get.return_value, mock_image_response]):
            books = fetch_books_data()
        
        self.assertEqual(len(books), 1)
        self.assertEqual(books[0]['title'], "Test Book")
        self.assertIn('image', books[0])  # Ensure image content is returned
        self.assertEqual(books[0]['author'], "Author One, Author Two")

    @patch('boipoka_app.views.requests.get')
    def test_fetch_books_data_failure(self, mock_get):
        """Test fetch_books_data for a failed API call."""
        mock_get.return_value.status_code = 404
        
        books = fetch_books_data()
        
        self.assertEqual(books, [])

    def test_create_books_in_db(self):
        """Test create_books_in_db function."""
        book_list = [
            {
                'title': 'Test Book',
                'author': 'Test Author',
                'description': 'Test Description',
                'image': None,  # You can mock this if needed
                'availability_status': True,
                'total_copies': 1,
                'available_copies': 1,
            }
        ]

        create_books_in_db(book_list)
        
        # Check if the book is created in the database
        self.assertEqual(Book.objects.count(), 1)
        book = Book.objects.first()
        self.assertEqual(book.title, 'Test Book')
        self.assertEqual(book.author, 'Test Author')

class BookListViewTests(TestCase):
    """Test cases for the book_list view."""

    def setUp(self):
        """Create a user and log them in for testing."""
        self.username = 'testuser'
        self.password = 'testpassword'
        self.user = User.objects.create_user(username=self.username, password=self.password)
        self.client.login(username=self.username, password=self.password)

    @patch('boipoka_app.views.fetch_books_data')
    @patch('boipoka_app.views.create_books_in_db')
    def test_book_list_view(self, mock_create_books, mock_fetch_books):
        """Test that the book list view returns the correct response."""
        mock_books = [
            {
                'title': 'Mock Book',
                'author': 'Mock Author',
                'description': 'Mock Description',
                'image': 'path/to/mock_image.jpg',  # Use a valid image path
                'availability_status': True,
                'total_copies': 1,
                'available_copies': 1,
            }
        ]
        
        mock_fetch_books.return_value = mock_books
        mock_create_books.return_value = None

        # Create a book in the database for testing
        for book in mock_books:
            Book.objects.create(**book)

        response = self.client.get(reverse('boipoka_app:book_list'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'boipoka_app/book_list.html')
        self.assertContains(response, 'Mock Book')  # Ensure the mocked book appears
        self.assertContains(response, 'Mock Author')

        # Check if image URL is being used
        self.assertContains(response, 'path/to/mock_image.jpg')  # Check for the image path in the response

    @patch('boipoka_app.views.fetch_books_data')
    @patch('boipoka_app.views.create_books_in_db')
    def test_book_list_view_no_books(self, mock_create_books, mock_fetch_books):
        """Test book list view when no books are returned."""
        mock_fetch_books.return_value = []
        mock_create_books.return_value = None

        response = self.client.get(reverse('boipoka_app:book_list'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'boipoka_app/book_list.html')
        self.assertContains(response, 'No books available')  # Adjust as per your template


# class BookDetailsViewTest(TestCase):

#     def setUp(self):
#         # Create a user and a subscription for testing
#         self.user = User.objects.create_user(username='testuser', password='password123')
#         self.subscription = Subscription.objects.create(
#             user=self.user,
#             subscription_type='Basic',  # Use 'subscription_type' instead of 'tier'
#             subscription_start=timezone.now()
#         )
#         self.book = Book.objects.create(title='Test Book', author='Author Name', description='Book Description', available=True)

#         # Create a second user for borrowing scenarios
#         self.second_user = User.objects.create_user(username='anotheruser', password='password456')

#     def test_book_available_not_borrowed(self):
#         self.client.login(username='testuser', password='password123')
#         response = self.client.get(reverse('book_details', args=[self.book.pk]))
        
#         self.assertEqual(response.status_code, 200)
#         self.assertContains(response, self.book.title)
#         self.assertTrue(response.context['availability'])  # Book should be available
#         self.assertFalse(response.context['is_borrowed'])  # User has not borrowed the book

#     def test_book_borrowed_by_user(self):
#         # Simulate borrowing the book
#         Borrowing.objects.create(user=self.user, book=self.book, due_date=timezone.now() + timedelta(days=14))
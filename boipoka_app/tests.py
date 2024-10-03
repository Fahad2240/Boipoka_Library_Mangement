from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Book, Subscription, Borrowing
from .forms import CustomUserCreationForm, SubscriptionForm

User = get_user_model()

class BoipokaAppTests(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.admin_user = User.objects.create_superuser(username='adminuser', password='adminpass')
        self.book = Book.objects.create(
            title='Test Book',
            author='Test Author',
            description='Test Description',
            availability_status=True,
            total_copies=5,
            available_copies=5,
        )
        self.client.login(username='testuser', password='testpass')

    def test_index_view(self):
        response = self.client.get(reverse('boipoka_app:index'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'boipoka_app/index.html')

    def test_register_view(self):
        response = self.client.post(reverse('boipoka_app:register'), {
            'username': 'newuser',
            'password1': 'newpass123',
            'password2': 'newpass123',
        })
        self.assertEqual(response.status_code, 302)  # Should redirect
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_book_list_view(self):
        response = self.client.get(reverse('boipoka_app:book_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'boipoka_app/book_list.html')
        self.assertContains(response, self.book.title)

    def test_book_details_view(self):
        response = self.client.get(reverse('boipoka_app:book_details', kwargs={'pk': self.book.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'boipoka_app/book_details.html')
        self.assertContains(response, self.book.title)

    def test_borrow_book_view(self):
        subscription = Subscription.objects.create(user=self.user, subscription_type='Basic', subscription_start='2024-01-01', subscription_end='2024-02-01', max_books=2)
        response = self.client.post(reverse('boipoka_app:borrow_book', kwargs={'pk': self.book.pk}))
        self.assertEqual(response.status_code, 302)  # Should redirect
        self.assertEqual(Borrowing.objects.count(), 1)
        self.assertEqual(self.book.available_copies, 4)

    def test_return_book_view(self):
        # First borrow the book
        subscription = Subscription.objects.create(user=self.user, subscription_type='Basic', subscription_start='2024-01-01', subscription_end='2024-02-01', max_books=2)
        borrowing = Borrowing.objects.create(user=self.user, book=self.book, subscription=subscription)
        
        response = self.client.post(reverse('boipoka_app:return_book', kwargs={'pk': self.book.pk}), {'next': reverse('boipoka_app:book_list')})
        self.assertEqual(response.status_code, 302)  # Should redirect
        self.assertEqual(Borrowing.objects.count(), 0)  # Should be deleted
        self.assertEqual(self.book.available_copies, 5)  # Should be incremented

    def test_add_book_view(self):
        self.client.login(username='adminuser', password='adminpass')
        response = self.client.post(reverse('boipoka_app:add_book'), {
            'title': 'Another Book',
            'author': 'Another Author',
            'description': 'Another Description',
            'availability_status': True,
            'total_copies': 3,
            'available_copies': 3,
        })
        self.assertEqual(response.status_code, 302)  # Should redirect
        self.assertTrue(Book.objects.filter(title='Another Book').exists())

    def test_edit_book_view(self):
        self.client.login(username='adminuser', password='adminpass')
        response = self.client.post(reverse('boipoka_app:edit_book', kwargs={'pk': self.book.pk}), {
            'title': 'Updated Test Book',
            'author': 'Updated Author',
            'description': 'Updated Description',
            'availability_status': True,
            'total_copies': 10,
            'available_copies': 10,
        })
        self.assertEqual(response.status_code, 302)  # Should redirect
        self.book.refresh_from_db()
        self.assertEqual(self.book.title, 'Updated Test Book')

    def test_delete_book_view(self):
        self.client.login(username='adminuser', password='adminpass')
        response = self.client.post(reverse('boipoka_app:delete_book', kwargs={'pk': self.book.pk}))
        self.assertEqual(response.status_code, 302)  # Should redirect
        self.assertFalse(Book.objects.filter(pk=self.book.pk).exists())

    def test_user_details_view(self):
        response = self.client.get(reverse('boipoka_app:user_details', kwargs={'pk': self.user.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'boipoka_app/user_details.html')
        self.assertContains(response, self.user.username)

    def test_change_subscription_view(self):
        subscription = Subscription.objects.create(user=self.user, subscription_type='Basic', subscription_start='2024-01-01', subscription_end='2024-02-01', max_books=2)
        response = self.client.post(reverse('boipoka_app:change_subscription'), {'subscription_type': 'Premium'})
        self.assertEqual(response.status_code, 302)  # Should redirect
        subscription.refresh_from_db()
        self.assertEqual(subscription.subscription_type, 'Premium')

    def test_send_reminder_view(self):
        subscription = Subscription.objects.create(user=self.user, subscription_type='Basic', subscription_start='2024-01-01', subscription_end='2024-02-01', max_books=2)
        borrowing = Borrowing.objects.create(user=self.user, book=self.book, subscription=subscription, due_date='2024-01-01')
        self.client.login(username='adminuser', password='adminpass')
        response = self.client.post(reverse('boipoka_app:send_reminder', kwargs={'pk': self.user.pk}))
        self.assertEqual(response.status_code, 302)  # Should redirect

    def test_login_view(self):
        response = self.client.post(reverse('boipoka_app:login'), {
            'username': 'testuser',
            'password': 'testpass'
        })
        self.assertEqual(response.status_code, 302)  # Should redirect

    def test_logout_view(self):
        response = self.client.get(reverse('boipoka_app:logout'))
        self.assertEqual(response.status_code, 302)  # Should redirect
        self.assertFalse(response.wsgi_request.user.is_authenticated)

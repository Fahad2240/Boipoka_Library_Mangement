from django.contrib import admin
from .models import *
# Register your models here.
admin.site.register(Book)
admin.site.register(Subscription)
admin.site.register(Borrowing)
admin.site.register(DamagedorLostHistory)
admin.site.register(Notifications)
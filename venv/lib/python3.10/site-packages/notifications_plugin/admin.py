# Django Imports
from django.contrib import admin

# Local Imports
from .models import NotificationMessage, Notification


class NotificationMessageAdmin(admin.ModelAdmin):
    list_display = ["creator", "summary", "uid", "created_on"]


class NotificationAdmin(admin.ModelAdmin):
    list_display = ["receiver", "read", "read_on", "message"]


admin.site.register(NotificationMessage, NotificationMessageAdmin)
admin.site.register(Notification, NotificationAdmin)

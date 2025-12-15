# Python Imports
import uuid

# Django Imports
from django.db import models
from django.conf import settings
from django.utils import timezone


class NotificationMessageManager(models.Manager):

    def add_bulk_messages(self, messages):
        """ Create bulk notification messages

            Parameters
            ----------
            messages : list
                List of message dictionaries containing following parameters

                creator_id : User id
                    Creator of the message
                summary : str
                    Message summary
                description: str
                    Actual notification message
                message_type: str
                    Indicate the type of the message i.e. info, danger,
                    warning, success

            Return
            ------
            Returns the multiple notification message objects

        """
        msg_list = [
            NotificationMessage(**msg)
            for msg in messages
        ]
        notification_msgs = NotificationMessage.objects.bulk_create(msg_list)
        return notification_msgs

    def add_single_message(self, creator_id, summary, description, msg_type):
        """ Create single notification message

            Parameters
            ----------
            creator_id : User id
                Creator of the message
            summary : str
                Message summary
            description: str
                Actual notification message
            msg_type: str
                Indicate the type of the message i.e. info, danger, warning,
                success

            Return
            ------
            Returns the notification message object

        """
        notification_msg = NotificationMessage.objects.create(
            creator_id=creator_id, summary=summary, description=description,
            message_type=msg_type
        )
        return notification_msg


class NotificationMessage(models.Model):
    type_choices = (
        ("info", "Info"), ("success", "Success"),
        ("warning", "Warning"),("danger", "Danger")
    )
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE
    )
    summary = models.CharField(max_length=255)
    description = models.TextField()
    message_type = models.CharField(
        max_length=20, choices=type_choices, default=type_choices[0]
    )
    uid = models.UUIDField(
        unique=True, default=uuid.uuid4, editable=False
    )
    created_on = models.DateTimeField(auto_now_add=True)
    modified_on = models.DateTimeField(auto_now=True)

    objects = NotificationMessageManager()

    def __str__(self):
        return "Notification Message {0}".format(self.uid)


class NotificationManager(models.Manager):

    def add_bulk_user_notifications(self, receiver_ids, msg_id):
        notification_list = [
            Notification(receiver_id=receiver_id, message_id=msg_id)
            for receiver_id in receiver_ids
        ]
        notifications = Notification.objects.bulk_create(notification_list)
        return notifications

    def add_single_notification(self, receiver_id, msg_id):
        notification = Notification.objects.create(
            receiver_id=receiver_id, message_id=msg_id
        )
        return notification

    def add_bulk_msg_notifications(self, receiver_id, msg_ids):
        notification_list = [
            Notification(receiver_id=receiver_id, message_id=msg_id)
            for msg_id in msg_ids
        ]
        notifications = Notification.objects.bulk_create(notification_list)
        return notifications

    def mark_bulk_msg_notifications(self, receiver_id, msg_uuids, read=False):
        notifications = Notification.objects.filter(
            receiver_id=receiver_id, message__uid__in=msg_uuids
        )
        for notification in notifications:
            notification.read = read
            notification.read_on = timezone.now() if read else None
        Notification.objects.bulk_update(notifications, ['read', 'read_on'])

    def mark_bulk_user_notifications(self, receiver_ids, msg_uuid, read=False):
        notifications = Notification.objects.filter(
            receiver_id__in=receiver_ids, message__uid=msg_uuid
        )
        for notification in notifications:
            notification.read = read
            notification.read_on = timezone.now() if read else None
        Notification.objects.bulk_update(notifications, ['read', 'read_on'])

    def mark_single_notification(self, receiver_id, msg_uuid, read=False):
        notification = Notification.objects.get(
            receiver_id=receiver_id, message__uid=msg_uuid
        )
        notification.read = read
        notification.read_on = timezone.now() if read else None
        notification.save()

    def get_receiver_notifications(self, receiver_id):
        return Notification.objects.filter(receiver_id=receiver_id)

    def get_unread_receiver_notifications(self, receiver_id):
        return Notification.objects.filter(
            receiver_id=receiver_id, read=False
        )

    def get_read_receiver_notifications(self, receiver_id):
        return Notification.objects.filter(
            receiver_id=receiver_id, read=True
        )

    def get_multiple_user_notifications(self, receiver_ids):
        return Notification.objects.filter(receiver_id__in=receiver_ids)

    def get_notifications_by_msg(self, msg_uuid):
        return Notification.objects.filter(message__uid=msg_uuid)


class Notification(models.Model):
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="notifications"
    )
    message = models.ForeignKey(
        NotificationMessage, on_delete=models.CASCADE
    )
    read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    read_on = models.DateTimeField(null=True, blank=True)

    objects = NotificationManager()

    def __str__(self):
        return "Notification for {0}".format(
            self.receiver.username
        )

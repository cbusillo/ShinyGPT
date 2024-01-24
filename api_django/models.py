# models.py
from django.conf import settings
from django.db.models import (
    CASCADE,
    CharField,
    ForeignKey,
    OneToOneField,
    TextField,
    DateTimeField,
    BooleanField,
    Model,
)


class Conversation(Model):
    gpt_model_name: CharField = CharField(max_length=255)
    user: OneToOneField = OneToOneField(settings.AUTH_USER_MODEL, on_delete=CASCADE, null=True)


class Message(Model):
    conversation: ForeignKey = ForeignKey(Conversation, on_delete=CASCADE)
    text: TextField = TextField()
    is_system: BooleanField = BooleanField()
    timestamp: DateTimeField = DateTimeField(auto_now_add=True)

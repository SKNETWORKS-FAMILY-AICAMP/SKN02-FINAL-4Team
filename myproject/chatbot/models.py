from django.db import models
from myapp.models import Profile


class WebChatList(models.Model):
    chat_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(Profile, on_delete=models.CASCADE, db_column='user_id', null=True, blank=True)
    chat_last_timestamp = models.DateTimeField()
    chat_status = models.IntegerField(default=1)  # 1 for active, 0 for deleted
    chat_deleted_time = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'web_chat_list'
    
    def __str__(self):
        return f"Chat {self.chat_id} (User: {self.user})"


class Question(models.Model):
    question_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(Profile, on_delete=models.CASCADE, db_column='user_id', null=True, blank=True)
    chat = models.ForeignKey(WebChatList, on_delete=models.CASCADE, db_column='chat_id')
    question_content = models.CharField(max_length=500)
    question_timestamp = models.DateTimeField()

    class Meta:
        db_table = 'question'

    def __str__(self):
        return f"Question {self.question_id} (Chat: {self.chat_id})"


class Answer(models.Model):
    answer_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(Profile, on_delete=models.CASCADE, db_column='user_id', null=True, blank=True)
    chat = models.ForeignKey(WebChatList, on_delete=models.CASCADE, db_column='chat_id')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, db_column='question_id')
    answer_content = models.CharField(max_length=500)
    answer_timestamp = models.DateTimeField()

    class Meta:
        db_table = 'answer'

    def __str__(self):
        return f"Answer {self.answer_id} (Question: {self.question_id})"
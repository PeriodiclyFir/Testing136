from django.db import models
from django.contrib.auth.models import AbstractUser

# ---------- 1.  USERS ----------
class User(AbstractUser):
    ROLE_CHOICES = {
        "A": "Administrator",
        "S": "Serf"
    }

    role        = models.CharField(max_length = 1, choices=ROLE_CHOICES)
    avatar      = models.ImageField(upload_to="avatars/", null=True, blank=True)
    bio         = models.TextField(blank=True)

    def __str__(self):
        return self.username


# ---------- 2.  BLOCK / MODERATION ----------
class BlockReason(models.Model):
    code        = models.CharField(max_length=30, unique=True)
    explanation = models.CharField(max_length=255)

    def __str__(self):
        return self.explanation


# ---------- 3.  POSTS ----------
class Post(models.Model):
    author          = models.ForeignKey(User, on_delete=models.SET_NULL,
                                        null=True, related_name="posts")
    content         = models.TextField()
    created_at      = models.DateTimeField(auto_now_add=True)
    hidden          = models.BooleanField(default=False)
    hidden_reason   = models.ForeignKey(BlockReason, null=True, blank=True,
                                        on_delete=models.SET_NULL)

    def __str__(self):
        return f"{self.author}: {self.content[:50]}"


# ---------- 4.  COMMENTS ----------
class Comment(models.Model):
    post            = models.ForeignKey(Post, on_delete=models.CASCADE,
                                        related_name="comments")
    author          = models.ForeignKey(User, on_delete=models.SET_NULL,
                                        null=True, related_name="comments")
    content         = models.TextField()
    created_at      = models.DateTimeField(auto_now_add=True)
    hidden          = models.BooleanField(default=False)
    hidden_reason   = models.ForeignKey(BlockReason, null=True, blank=True,
                                        on_delete=models.SET_NULL)

    def __str__(self):
        return f"Comment by {self.author} on {self.post_id}"


# ---------- 5.  MEDIA ----------
class Media(models.Model):
    file            = models.FileField(upload_to="uploads/%Y/%m/%d/")
    uploaded_by     = models.ForeignKey(User, on_delete=models.SET_NULL,
                                        null=True, related_name="media")
    uploaded_at     = models.DateTimeField(auto_now_add=True)
    post            = models.ForeignKey(Post, null=True, blank=True,
                                        on_delete=models.CASCADE, related_name="media")
    comment         = models.ForeignKey(Comment, null=True, blank=True,
                                        on_delete=models.CASCADE, related_name="media")

    def __str__(self):
        return self.file.name


# ---------- 6.  LIKES ----------
class Like(models.Model):
    user            = models.ForeignKey(User, on_delete=models.CASCADE)
    post            = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="likes")
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "post")  # prevent duplicate likes

    def __str__(self):
        return f"{self.user} ❤️ {self.post_id}"

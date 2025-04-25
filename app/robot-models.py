# Prompt given to GPT-4o, April 2025:
# You are a senior Django architect.  
# Generate a *complete* Django 5 models.py file (with imports) that implements the data model described below.  
# Follow these rules:

# 1. Use django.contrib.auth.models.AbstractUser as the base for the user model.  
# 2. Include sensible on_delete behaviours, auto_now_add timestamps, and any useful unique_together / constraints.  
# 3. Name the main app app.  
# 4. Add concise docstrings for each model explaining its purpose.  
# 5. Put **all** code in one file and nothing else.

# ### Application: “CloudySky” – an Ideologically Consonant Chat Environment

# **User types**  
# * Two roles: _Administrator_ and _Serf_.  
# * Users have nickname, optional avatar image, and optional bio.  
# * Administrators can hide posts/comments; Serfs cannot.  

# **Posts**  
# * Authored by a single user.  
# * Text content, creation timestamp.  
# * May embed zero or more uploaded media items (images/files).  
# * Have many “likes” (a user may like a post at most once).  
# * Can be hidden; if hidden, store a reason chosen from a predefined lookup table of block reasons.

# **Comments**  
# * Belong to exactly one post.  
# * Authored by one user.  
# * Same hide/like/media logic as posts.

# **Block reasons**  
# * Lookup table: code (unique) + human-readable explanation.

# **Likes**  
# * Represent a user endorsing a post _or_ a comment (choose whichever modelling pattern you prefer; explain via docstring).

# **Media uploads**  
# * File (image or other) + uploader + uploaded_at timestamp.  
# * May attach to either a post or a comment.

# Provide a schema that supports:  
# – Counting each user’s posts/comments and bytes uploaded in the last 1, 7, 30 days.  
# – Showing which posts/comments have been hidden and why.  
# – Preventing duplicate likes by the same user on the same object.

# Return only the finished models.py code block.

# --------------------- Response Below ---------------------

"""
app/models.py
~~~~~~~~~~~~~
Data model for *CloudySky* – an ideologically consonant chat environment.
"""

from django.contrib.auth.models import AbstractUser
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    """Site participant with one of two roles: Administrator or Serf."""
    ADMINISTRATOR = "admin"
    SERF = "serf"

    ROLE_CHOICES = [
        (ADMINISTRATOR, "Administrator"),
        (SERF, "Serf"),
    ]

    role = models.CharField(
        max_length=8,
        choices=ROLE_CHOICES,
        default=SERF,
        help_text="Determines the user’s permission to hide content.",
    )
    nickname = models.CharField(max_length=40, unique=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    bio = models.TextField(blank=True)

    # Convenience reverse relations ─ filled by GenericRelation on target models
    uploads = GenericRelation(
        "Media",
        content_type_field="uploader_content_type",
        object_id_field="uploader_object_id",
    )

    def __str__(self) -> str:
        return self.nickname or self.username


class BlockReason(models.Model):
    """Lookup table describing why a post/comment has been hidden."""
    code = models.CharField(max_length=32, unique=True)
    description = models.CharField(max_length=255)

    class Meta:
        ordering = ["code"]

    def __str__(self) -> str:
        return f"{self.code}: {self.description}"


class Post(models.Model):
    """A user-authored post that may embed media, receive likes, and be hidden."""
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="posts"
    )
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    # hide mechanics
    is_hidden = models.BooleanField(default=False)
    hidden_reason = models.ForeignKey(
        BlockReason,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="hidden_posts",
    )
    hidden_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="hidden_posts_performed",
    )
    hidden_at = models.DateTimeField(null=True, blank=True)

    # generic relations
    media_items = GenericRelation(
        "Media",
        related_query_name="post",
    )
    likes = GenericRelation(
        "Like",
        related_query_name="post",
    )

    class Meta:
        indexes = [
            models.Index(fields=["created_at"]),
            models.Index(fields=["is_hidden"]),
        ]
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Post #{self.pk} by {self.author}"


class Comment(models.Model):
    """User comment on a post; supports likes, media, and hiding like posts."""
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name="comments"
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="comments"
    )
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    # hide mechanics
    is_hidden = models.BooleanField(default=False)
    hidden_reason = models.ForeignKey(
        BlockReason,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="hidden_comments",
    )
    hidden_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="hidden_comments_performed",
    )
    hidden_at = models.DateTimeField(null=True, blank=True)

    # generic relations
    media_items = GenericRelation(
        "Media",
        related_query_name="comment",
    )
    likes = GenericRelation(
        "Like",
        related_query_name="comment",
    )

    class Meta:
        indexes = [
            models.Index(fields=["created_at"]),
            models.Index(fields=["is_hidden"]),
        ]
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"Comment #{self.pk} on Post #{self.post_id}"


class Media(models.Model):
    """
    An uploaded file (image or other) attached to a post *or* comment.
    Uses a `GenericForeignKey` so each row points to exactly one parent object.
    """
    file = models.FileField(
        upload_to="uploads/",
        validators=[FileExtensionValidator(allowed_extensions=None)],
    )
    size_bytes = models.PositiveBigIntegerField(
        editable=False,
        help_text="Stored at upload time to allow fast aggregation.",
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    # relation to parent Post or Comment
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveBigIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    # uploader (redundant to post/comment but simplifies queries)
    uploader_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name="uploaded_media_ct",
    )
    uploader_object_id = models.PositiveBigIntegerField()
    uploader = GenericForeignKey(
        "uploader_content_type", "uploader_object_id"
    )

    class Meta:
        indexes = [
            models.Index(fields=["uploaded_at"]),
            models.Index(fields=["content_type", "object_id"]),
        ]

    def save(self, *args, **kwargs):
        # Capture file size before first save
        if not self.size_bytes and self.file:
            self.size_bytes = self.file.size
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"Media #{self.pk} ({self.file.name})"


class Like(models.Model):
    """
    A user endorsement for either a post or a comment.
    Implemented via `GenericForeignKey` so the same table services both types.
    The `(user, content_object)` pair is enforced unique to prevent duplicates.
    """
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="likes"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    # target object (Post or Comment)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveBigIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "content_type", "object_id"],
                name="unique_user_like",
            )
        ]
        indexes = [
            models.Index(fields=["created_at"]),
            models.Index(fields=["content_type", "object_id"]),
        ]

    def __str__(self) -> str:
        return f"Like #{self.pk} by {self.user}"

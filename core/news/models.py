from django.contrib.postgres.fields import ArrayField
from django.db import models


class Source(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=200, unique=True)
    normalized_name = models.CharField(max_length=200, db_index=True)
    website_url = models.CharField(max_length=500)
    description = models.TextField(null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    language = models.CharField(max_length=10, null=True, blank=True)
    credibility_score = models.FloatField(null=True, blank=True)
    political_bias = models.CharField(max_length=50, null=True, blank=True)
    status = models.IntegerField(null=True, blank=True, db_index=True)
    is_verified = models.BooleanField(default=False)
    total_articles = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    logo = models.ImageField(upload_to="source_logos/", null=True, blank=True)
    crawl_mode = models.CharField(max_length=10, null=True, blank=True)

    class Meta:
        db_table = "source"
        indexes = [
            models.Index(fields=["normalized_name"]),
        ]

    def __str__(self) -> str:
        return self.name


class Feed(models.Model):
    id = models.AutoField(primary_key=True)
    status = models.SmallIntegerField(null=True, blank=True)
    url = models.CharField(max_length=1024, null=True, blank=True)
    feed_type = models.SmallIntegerField(db_column="type", null=True, blank=True)
    language = models.CharField(max_length=2, null=True, blank=True)
    source = models.ForeignKey(
        Source,
        db_column="source_id",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="feeds",
    )
    is_xml = models.BooleanField(null=True, blank=True)
    score = models.SmallIntegerField(null=True, blank=True, db_index=True)
    publish_rate = models.SmallIntegerField(null=True, blank=True)
    raw_html = models.TextField(null=True, blank=True)
    last_crawl_time = models.IntegerField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Unix timestamp",
    )
    crawl_status = models.SmallIntegerField(null=True, blank=True)
    queued_at = models.IntegerField(default=0)
    done_at = models.IntegerField(default=0)
    extracted_at = models.IntegerField(default=0)
    failed_at = models.IntegerField(default=0)

    class Meta:
        db_table = "feed"

    def __str__(self) -> str:
        return self.url or f"Feed {self.pk}"


class Category(models.Model):
    id = models.BigAutoField(primary_key=True)
    title = models.CharField(max_length=100, unique=True, db_index=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children",
    )

    class Meta:
        db_table = "category"

    def __str__(self) -> str:
        return self.title


class Event(models.Model):
    id = models.BigAutoField(primary_key=True)
    title = models.CharField(max_length=500, null=True, blank=True)
    title_last_generated_at = models.DateTimeField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    description_last_generated_at = models.DateTimeField(null=True, blank=True)
    short_summary = models.TextField()
    detailed_summary = models.TextField()
    title_embedding = ArrayField(models.FloatField(), size=1024, null=True, blank=True)
    detailed_summary_embedding = ArrayField(
        models.FloatField(),
        size=1024,
        null=True,
        blank=True,
    )
    description_embedding = ArrayField(
        models.FloatField(),
        size=1024,
        null=True,
        blank=True,
    )
    status = models.IntegerField(db_index=True)
    confidence_score = models.FloatField()
    article_count = models.IntegerField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    last_article_added_at = models.DateTimeField(null=True, blank=True)
    event_grouping_confidence = models.FloatField(null=True, blank=True)
    synced_at = models.DateTimeField(null=True, blank=True)
    image_url = models.CharField(max_length=2048, null=True, blank=True)

    class Meta:
        db_table = "event"
        indexes = [
            models.Index(fields=["created_at"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self) -> str:
        return self.title or f"Event {self.pk}"


class Story(models.Model):
    id = models.BigAutoField(primary_key=True)
    title = models.CharField(max_length=500, null=True, blank=True)
    title_last_generated_at = models.DateTimeField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    description_last_generated_at = models.DateTimeField(null=True, blank=True)
    short_summary = models.TextField()
    detailed_summary = models.TextField()
    title_embedding = ArrayField(models.FloatField(), size=1024, null=True, blank=True)
    detailed_summary_embedding = ArrayField(
        models.FloatField(),
        size=1024,
        null=True,
        blank=True,
    )
    description_embedding = ArrayField(
        models.FloatField(),
        size=1024,
        null=True,
        blank=True,
    )
    status = models.IntegerField(db_index=True)
    confidence_score = models.FloatField()
    event_count = models.IntegerField()
    article_count = models.IntegerField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    last_event_added_at = models.DateTimeField(null=True, blank=True)
    image_url = models.CharField(max_length=2048, null=True, blank=True)

    class Meta:
        db_table = "story"
        indexes = [
            models.Index(fields=["created_at"]),
            models.Index(fields=["last_event_added_at"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self) -> str:
        return self.title or f"Story {self.pk}"


class Article(models.Model):
    id = models.BigAutoField(primary_key=True)
    url = models.CharField(max_length=8192, db_index=True)
    news_type = models.SmallIntegerField(null=True, blank=True)
    title = models.CharField(max_length=1000, null=True, blank=True)
    author = models.CharField(max_length=500, null=True, blank=True)
    published_date = models.CharField(max_length=100, null=True, blank=True)
    fetched_at = models.DateTimeField(null=True, blank=True)
    mentions_grouped_to_events = models.BooleanField(null=True, blank=True)
    article_grouping_confidence = models.FloatField(null=True, blank=True)
    raw_html = models.TextField(null=True, blank=True)
    cleaned_content = models.TextField(null=True, blank=True)
    short_summary = models.TextField(null=True, blank=True)
    detailed_summary = models.TextField(null=True, blank=True)
    key_points = ArrayField(models.TextField(), null=True, blank=True)
    content_type = models.CharField(max_length=20, null=True, blank=True)
    content_type_reasoning = models.TextField(null=True, blank=True)
    categories_reasoning = models.TextField(null=True, blank=True)
    title_embedding = ArrayField(models.FloatField(), size=1024, null=True, blank=True)
    summary_embedding = ArrayField(models.FloatField(), size=1024, null=True, blank=True)
    combined_embedding = ArrayField(models.FloatField(), size=1024, null=True, blank=True)
    cleanup_status = models.IntegerField(default=9, db_index=True)
    summarize_status = models.IntegerField(default=9, db_index=True)
    extract_entities_status = models.IntegerField(default=9, db_index=True)
    generate_embeddings_status = models.IntegerField(default=9, db_index=True)
    extract_propaganda_status = models.IntegerField(default=9, db_index=True)
    cleanup_started_at = models.DateTimeField(null=True, blank=True)
    summarize_started_at = models.DateTimeField(null=True, blank=True)
    extract_entities_started_at = models.DateTimeField(null=True, blank=True)
    generate_embeddings_started_at = models.DateTimeField(null=True, blank=True)
    extract_propaganda_started_at = models.DateTimeField(null=True, blank=True)
    extract_propaganda_completed_at = models.DateTimeField(null=True, blank=True)
    cleanup_completed_at = models.DateTimeField(null=True, blank=True)
    summarize_completed_at = models.DateTimeField(null=True, blank=True)
    extract_entities_completed_at = models.DateTimeField(null=True, blank=True)
    generate_embeddings_completed_at = models.DateTimeField(null=True, blank=True)
    cleanup_duration = models.FloatField(null=True, blank=True)
    summarize_duration = models.FloatField(null=True, blank=True)
    extract_entities_duration = models.FloatField(null=True, blank=True)
    generate_embeddings_duration = models.FloatField(null=True, blank=True)
    extract_propaganda_duration = models.FloatField(null=True, blank=True)
    cleanup_error = models.TextField(null=True, blank=True)
    summarize_error = models.TextField(null=True, blank=True)
    extract_entities_error = models.TextField(null=True, blank=True)
    generate_embeddings_error = models.TextField(null=True, blank=True)
    extract_propaganda_error = models.TextField(null=True, blank=True)
    cleanup_retry_count = models.IntegerField(null=True, blank=True)
    summarize_retry_count = models.IntegerField(null=True, blank=True)
    extract_entities_retry_count = models.IntegerField(null=True, blank=True)
    generate_embeddings_retry_count = models.IntegerField(null=True, blank=True)
    extract_propaganda_retry_count = models.IntegerField(null=True, blank=True)
    extract_entities_confidence = models.FloatField(null=True, blank=True)
    has_propaganda = models.BooleanField(null=True, blank=True, db_index=True)
    propaganda_score = models.FloatField(null=True, blank=True)
    language = models.CharField(max_length=10, null=True, blank=True)
    word_count = models.IntegerField(null=True, blank=True)
    overall_confidence_score = models.FloatField(null=True, blank=True)
    is_fully_processed = models.BooleanField(null=True, blank=True, db_index=True)
    overall_status = models.IntegerField(default=9, db_index=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    event = models.ForeignKey(
        Event,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="articles",
    )
    news_source = models.ForeignKey(
        Source,
        db_column="news_source_id",
        on_delete=models.CASCADE,
        related_name="articles",
    )
    url_hash = models.CharField(max_length=20, unique=True)
    feed = models.ForeignKey(
        Feed,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="articles",
    )
    status = models.SmallIntegerField(default=1, null=True, blank=True)
    synced_at = models.DateTimeField(null=True, blank=True)
    crawled = models.BooleanField(default=False, null=True, blank=True)
    page_type = models.SmallIntegerField(null=True, blank=True, db_index=True)
    reference_article = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="referenced_by",
    )
    reference_similarity = models.FloatField(null=True, blank=True)
    remote_image_url = models.CharField(max_length=2048, null=True, blank=True)
    image_url = models.CharField(max_length=2048, null=True, blank=True)
    calculate_references_completed_at = models.DateTimeField(null=True, blank=True)
    calculate_references_duration = models.FloatField(null=True, blank=True)
    calculate_references_error = models.TextField(null=True, blank=True)
    calculate_references_retry_count = models.IntegerField(null=True, blank=True)
    calculate_references_started_at = models.DateTimeField(null=True, blank=True)
    calculate_references_status = models.IntegerField(null=True, blank=True, db_index=True)
    image_sync_status = models.SmallIntegerField(default=1, null=True, blank=True)

    class Meta:
        db_table = "article"
        indexes = [
            models.Index(fields=["url"]),
            models.Index(fields=["news_source", "page_type"]),
            models.Index(fields=["news_source", "published_date"]),
            models.Index(fields=["published_date"]),
            models.Index(fields=["propaganda_score"]),
        ]

    def __str__(self) -> str:
        return self.title or self.url


class ArticleCategory(models.Model):
    id = models.BigAutoField(primary_key=True)
    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name="article_categories",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="category_articles",
    )

    class Meta:
        db_table = "article_category"
        constraints = [
            models.UniqueConstraint(
                fields=["article", "category"],
                name="article_category_article_id_category_id_uniq",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.article_id}-{self.category_id}"


class Entity(models.Model):
    id = models.BigAutoField(primary_key=True)
    entity_type = models.CharField(max_length=20, db_index=True)
    name = models.CharField(max_length=200)
    normalized_name = models.CharField(max_length=200, db_index=True)
    subtype = models.CharField(max_length=50, null=True, blank=True)
    aliases = ArrayField(models.CharField(max_length=200), default=list, blank=True)
    description = models.TextField()
    status = models.IntegerField(db_index=True)
    total_mentions = models.IntegerField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children",
    )

    class Meta:
        db_table = "entity"
        constraints = [
            models.UniqueConstraint(
                fields=["entity_type", "normalized_name"],
                name="entity_entity_type_normalized_name_uniq",
            ),
        ]
        indexes = [
            models.Index(fields=["entity_type", "subtype"]),
            models.Index(fields=["entity_type", "total_mentions"]),
            models.Index(fields=["normalized_name"]),
        ]

    def __str__(self) -> str:
        return f"{self.entity_type}: {self.name}"


class EntityMention(models.Model):
    id = models.BigAutoField(primary_key=True)
    mention_count = models.IntegerField()
    confidence_score = models.FloatField(null=True, blank=True)
    context = ArrayField(models.TextField(), default=list, blank=True)
    first_position = models.IntegerField(null=True, blank=True)
    sentiment = models.CharField(max_length=20, null=True, blank=True)
    context_embedding_1 = ArrayField(models.FloatField(), size=1024, null=True, blank=True)
    context_embedding_2 = ArrayField(models.FloatField(), size=1024, null=True, blank=True)
    context_embedding_3 = ArrayField(models.FloatField(), size=1024, null=True, blank=True)
    combined_context_embedding = ArrayField(
        models.FloatField(),
        size=1024,
        null=True,
        blank=True,
    )
    entity = models.ForeignKey(
        Entity,
        on_delete=models.CASCADE,
        related_name="mentions",
    )
    news_article = models.ForeignKey(
        Article,
        db_column="news_article_id",
        on_delete=models.CASCADE,
        related_name="entity_mentions",
    )
    event = models.ForeignKey(
        Event,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="entity_mentions",
    )
    impact_description = models.TextField(null=True, blank=True)
    impact_sentiment = models.CharField(max_length=20, null=True, blank=True)
    impact_type = models.CharField(max_length=20)

    class Meta:
        db_table = "entity_mention"
        constraints = [
            models.UniqueConstraint(
                fields=["news_article", "entity"],
                name="entity_mention_news_article_id_entity_id_uniq",
            ),
        ]
        indexes = [
            models.Index(fields=["entity", "news_article"]),
            models.Index(fields=["entity", "mention_count"]),
            models.Index(fields=["impact_type"]),
            models.Index(fields=["impact_sentiment"]),
        ]

    def __str__(self) -> str:
        return f"{self.entity_id} in article {self.news_article_id}"


class EventCategory(models.Model):
    id = models.BigAutoField(primary_key=True)
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="event_categories",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="category_events",
    )

    class Meta:
        db_table = "event_category"
        constraints = [
            models.UniqueConstraint(
                fields=["event", "category"],
                name="event_category_event_id_category_id_uniq",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.event_id}-{self.category_id}"


class StoryCategory(models.Model):
    id = models.BigAutoField(primary_key=True)
    story = models.ForeignKey(
        Story,
        on_delete=models.CASCADE,
        related_name="story_categories",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="category_stories",
    )

    class Meta:
        db_table = "story_category"
        constraints = [
            models.UniqueConstraint(
                fields=["story", "category"],
                name="story_category_story_id_category_id_uniq",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.story_id}-{self.category_id}"


class EventStory(models.Model):
    id = models.BigAutoField(primary_key=True)
    confidence = models.FloatField()
    rank = models.IntegerField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="event_stories",
    )
    story = models.ForeignKey(
        Story,
        on_delete=models.CASCADE,
        related_name="story_events",
    )

    class Meta:
        db_table = "event_story"
        constraints = [
            models.UniqueConstraint(
                fields=["event", "story"],
                name="event_story_event_id_story_id_uniq",
            ),
        ]
        indexes = [
            models.Index(fields=["event", "rank"]),
            models.Index(fields=["story"]),
            models.Index(fields=["confidence"]),
        ]

    def __str__(self) -> str:
        return f"{self.event_id}-{self.story_id}"


class ProcessLog(models.Model):
    id = models.BigAutoField(primary_key=True)
    process_type = models.CharField(max_length=30)
    status = models.IntegerField(db_index=True)
    started_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.FloatField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    event = models.ForeignKey(
        Event,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="process_logs",
    )
    news_article = models.ForeignKey(
        Article,
        db_column="news_article_id",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="process_logs",
    )

    class Meta:
        db_table = "process_log"
        indexes = [
            models.Index(fields=["event", "process_type"]),
            models.Index(fields=["news_article", "process_type"]),
            models.Index(fields=["process_type", "status"]),
            models.Index(fields=["started_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.process_type} ({self.status})"


class PropagandaTechnique(models.Model):
    id = models.BigAutoField(primary_key=True)
    technique = models.CharField(max_length=200)
    confidence = models.FloatField()
    text_snippet = models.TextField()
    explanation = models.TextField()
    start_position = models.IntegerField(null=True, blank=True)
    end_position = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField()
    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name="propaganda_techniques",
    )

    class Meta:
        db_table = "propaganda_technique"
        indexes = [
            models.Index(fields=["article", "confidence"]),
            models.Index(fields=["technique"]),
        ]

    def __str__(self) -> str:
        return self.technique


class ServiceControl(models.Model):
    id = models.BigAutoField(primary_key=True)
    service_enabled = models.BooleanField()
    cleanup_enabled = models.BooleanField()
    summarize_enabled = models.BooleanField()
    embeddings_enabled = models.BooleanField()
    extract_entities_enabled = models.BooleanField()
    extract_propaganda_enabled = models.BooleanField()
    event_group_articles_enabled = models.BooleanField()
    event_update_titles_enabled = models.BooleanField()
    event_embeddings_enabled = models.BooleanField()
    file_group_events_enabled = models.BooleanField()
    file_update_titles_enabled = models.BooleanField()
    file_embeddings_enabled = models.BooleanField()
    updated_at = models.DateTimeField()
    updated_by = models.CharField(max_length=255, null=True, blank=True)
    calculate_references_enabled = models.BooleanField()

    class Meta:
        db_table = "service_control"

    def __str__(self) -> str:
        return f"ServiceControl {self.pk}"


class EventReport(models.Model):
    id = models.BigAutoField(primary_key=True)
    event = models.BigIntegerField(db_column="event_id", db_index=True)
    reason = models.TextField()
    reported_by = models.BigIntegerField(db_column="reported_by_id", db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "event_report"
        indexes = [
            models.Index(fields=["event", "created_at"]),
            models.Index(fields=["reported_by"]),
        ]

    def __str__(self) -> str:
        return f"Report #{self.pk} for event {self.event}"


class EventComment(models.Model):
    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"

    STATUS_CHOICES = (
        (STATUS_PENDING, "Pending"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected"),
    )

    id = models.BigAutoField(primary_key=True)
    event_id = models.CharField(max_length=128)
    content = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    author_id = models.BigIntegerField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "event_comment"
        indexes = [
            models.Index(fields=["event_id", "created_at"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self) -> str:
        return f"Comment #{self.pk} for event {self.event_id}"


class CrawlResult(models.Model):
    id = models.AutoField(primary_key=True)
    url = models.TextField(unique=True)
    title = models.TextField(null=True, blank=True)
    body = models.TextField()
    text_content = models.TextField(null=True, blank=True)
    http_status = models.IntegerField()
    headers = models.JSONField(null=True, blank=True)
    is_spa = models.BooleanField(default=False)
    is_behind_cdn = models.BooleanField(default=False)
    has_captcha = models.BooleanField(default=False)
    crawl_mode = models.TextField()
    timestamp = models.DateTimeField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "crawl_results"
        indexes = [
            models.Index(fields=["url"]),
            models.Index(fields=["timestamp"]),
        ]

    def __str__(self) -> str:
        return self.url

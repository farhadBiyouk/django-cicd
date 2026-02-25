from django.contrib import admin

from .models import (
    Article,
    ArticleCategory,
    Category,
    CrawlResult,
    Entity,
    EntityMention,
    Event,
    EventCategory,
    EventComment,
    EventReport,
    EventStory,
    Feed,
    Follow,
    ProcessLog,
    PropagandaTechnique,
    ServiceControl,
    Source,
    Story,
    StoryCategory,
)


@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "normalized_name", "language", "status", "is_verified", "updated_at")
    search_fields = ("name", "normalized_name", "website_url")
    list_filter = ("status", "is_verified", "language")


@admin.register(Feed)
class FeedAdmin(admin.ModelAdmin):
    list_display = ("id", "url", "source", "status", "score", "last_crawl_time")
    search_fields = ("url",)
    list_filter = ("status", "crawl_status", "is_xml")
    raw_id_fields = ("source",)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "parent", "created_at", "updated_at")
    search_fields = ("title",)
    raw_id_fields = ("parent",)


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "news_source",
        "status",
        "overall_status",
        "is_fully_processed",
        "has_propaganda",
        "created_at",
    )
    search_fields = ("title", "url", "url_hash", "author")
    list_filter = (
        "status",
        "overall_status",
        "cleanup_status",
        "summarize_status",
        "extract_entities_status",
        "extract_propaganda_status",
        "generate_embeddings_status",
        "has_propaganda",
        "is_fully_processed",
        "news_source",
    )
    raw_id_fields = ("event", "news_source", "feed", "reference_article")


@admin.register(ArticleCategory)
class ArticleCategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "article", "category")
    raw_id_fields = ("article", "category")


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "status", "confidence_score", "article_count", "created_at")
    search_fields = ("title",)
    list_filter = ("status",)


@admin.register(EventCategory)
class EventCategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "event", "category")
    raw_id_fields = ("event", "category")


@admin.register(EventReport)
class EventReportAdmin(admin.ModelAdmin):
    list_display = ("id", "event", "reported_by", "created_at")
    search_fields = ("reason",)
    list_filter = ("event", "reported_by")


@admin.register(EventComment)
class EventCommentAdmin(admin.ModelAdmin):
    list_display = ("id", "event_id", "status", "author_id", "created_at")
    search_fields = ("event_id", "content")
    list_filter = ("status",)


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ("id", "user_id", "target_type", "target_id", "created_at")
    search_fields = ("target_id",)
    list_filter = ("target_type",)


@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "status", "confidence_score", "event_count", "article_count", "created_at")
    search_fields = ("title",)
    list_filter = ("status",)


@admin.register(StoryCategory)
class StoryCategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "story", "category")
    raw_id_fields = ("story", "category")


@admin.register(EventStory)
class EventStoryAdmin(admin.ModelAdmin):
    list_display = ("id", "event", "story", "rank", "confidence", "created_at")
    list_filter = ("rank",)
    raw_id_fields = ("event", "story")


@admin.register(Entity)
class EntityAdmin(admin.ModelAdmin):
    list_display = ("id", "entity_type", "name", "normalized_name", "status", "total_mentions", "updated_at")
    search_fields = ("name", "normalized_name")
    list_filter = ("entity_type", "status")
    raw_id_fields = ("parent",)


@admin.register(EntityMention)
class EntityMentionAdmin(admin.ModelAdmin):
    list_display = ("id", "entity", "news_article", "mention_count", "impact_type", "impact_sentiment")
    list_filter = ("impact_type", "impact_sentiment", "sentiment")
    raw_id_fields = ("entity", "news_article", "event")


@admin.register(ProcessLog)
class ProcessLogAdmin(admin.ModelAdmin):
    list_display = ("id", "process_type", "status", "event", "news_article", "started_at", "completed_at")
    search_fields = ("process_type", "error_message")
    list_filter = ("process_type", "status")
    raw_id_fields = ("event", "news_article")


@admin.register(PropagandaTechnique)
class PropagandaTechniqueAdmin(admin.ModelAdmin):
    list_display = ("id", "article", "technique", "confidence", "created_at")
    search_fields = ("technique", "text_snippet")
    raw_id_fields = ("article",)


@admin.register(ServiceControl)
class ServiceControlAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "service_enabled",
        "cleanup_enabled",
        "summarize_enabled",
        "embeddings_enabled",
        "extract_entities_enabled",
        "extract_propaganda_enabled",
        "calculate_references_enabled",
        "updated_at",
        "updated_by",
    )
    list_filter = (
        "service_enabled",
        "cleanup_enabled",
        "summarize_enabled",
        "embeddings_enabled",
        "extract_entities_enabled",
        "extract_propaganda_enabled",
        "calculate_references_enabled",
    )
    search_fields = ("updated_by",)


@admin.register(CrawlResult)
class CrawlResultAdmin(admin.ModelAdmin):
    list_display = ("id", "url", "http_status", "crawl_mode", "timestamp", "is_spa", "has_captcha")
    search_fields = ("url", "title")
    list_filter = ("crawl_mode", "http_status", "is_spa", "is_behind_cdn", "has_captcha")

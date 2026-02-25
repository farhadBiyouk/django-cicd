from rest_framework import serializers


class SourceListQuerySerializer(serializers.Serializer):
    page = serializers.IntegerField(required=False, min_value=1, default=1)
    page_size = serializers.IntegerField(required=False, min_value=1, max_value=100, default=20)
    search = serializers.CharField(required=False, allow_blank=False, max_length=200)
    status = serializers.IntegerField(required=False)
    is_verified = serializers.BooleanField(required=False)


class EventSourceListQuerySerializer(serializers.Serializer):
    page = serializers.IntegerField(required=False, min_value=1, default=1)
    page_size = serializers.IntegerField(required=False, min_value=1, max_value=100, default=20)


class SourceListSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    normalized_name = serializers.CharField(read_only=True)
    website_url = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True, allow_null=True)
    country = serializers.CharField(read_only=True, allow_null=True)
    language = serializers.CharField(read_only=True, allow_null=True)
    credibility_score = serializers.FloatField(read_only=True, allow_null=True)
    political_bias = serializers.CharField(read_only=True, allow_null=True)
    status = serializers.IntegerField(read_only=True, allow_null=True)
    is_verified = serializers.BooleanField(read_only=True)
    total_articles = serializers.IntegerField(read_only=True, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    logo = serializers.SerializerMethodField()
    crawl_mode = serializers.CharField(read_only=True, allow_null=True)

    def get_logo(self, obj):
        logo_name = getattr(obj, "logo", None)
        if not logo_name:
            return None

        # Preserve existing absolute URLs stored as plain strings.
        raw_value = str(logo_name)
        if raw_value.startswith("http://") or raw_value.startswith("https://"):
            return raw_value

        try:
            url = obj.logo.url
        except Exception:
            return raw_value

        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(url)
        return url


class EventSourceListSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    normalized_name = serializers.CharField(read_only=True)
    website_url = serializers.CharField(read_only=True)
    country = serializers.CharField(read_only=True, allow_null=True)
    language = serializers.CharField(read_only=True, allow_null=True)
    is_verified = serializers.BooleanField(read_only=True)
    logo = serializers.SerializerMethodField()
    published_articles_count = serializers.IntegerField(read_only=True)

    def get_logo(self, obj):
        logo_name = getattr(obj, "logo", None)
        if not logo_name:
            return None

        raw_value = str(logo_name)
        if raw_value.startswith("http://") or raw_value.startswith("https://"):
            return raw_value

        try:
            url = obj.logo.url
        except Exception:
            return raw_value

        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(url)
        return url

from rest_framework import serializers

from core.news.models import Follow


class FollowMutationSerializer(serializers.Serializer):
    target_type = serializers.CharField(max_length=20)
    target_id = serializers.CharField(max_length=128)

    TARGET_ALIASES = {
        "event": Follow.TARGET_EVENT,
        "story": Follow.TARGET_STORY,
        "file": Follow.TARGET_STORY,
        "case": Follow.TARGET_STORY,
        "person": Follow.TARGET_PERSON,
        "source": Follow.TARGET_SOURCE,
        "publisher": Follow.TARGET_SOURCE,
        "entity": Follow.TARGET_ENTITY,
    }

    def validate_target_type(self, target_type):
        normalized = target_type.strip().lower()
        canonical = self.TARGET_ALIASES.get(normalized)
        if not canonical:
            raise serializers.ValidationError(
                "target_type must be one of: event, story, person, source, entity"
            )
        return canonical

    def validate_target_id(self, target_id):
        cleaned = str(target_id).strip()
        if not cleaned:
            raise serializers.ValidationError("target_id cannot be empty")
        return cleaned


class FollowListQuerySerializer(serializers.Serializer):
    page = serializers.IntegerField(required=False, min_value=1, default=1)
    page_size = serializers.IntegerField(required=False, min_value=1, max_value=100, default=20)
    target_type = serializers.CharField(required=False, max_length=20)

    TARGET_ALIASES = FollowMutationSerializer.TARGET_ALIASES

    def validate_target_type(self, target_type):
        normalized = target_type.strip().lower()
        canonical = self.TARGET_ALIASES.get(normalized)
        if not canonical:
            raise serializers.ValidationError(
                "target_type must be one of: event, story, person, source, entity"
            )
        return canonical


class FollowSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    user_id = serializers.IntegerField(read_only=True)
    target_type = serializers.CharField(read_only=True)
    target_id = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

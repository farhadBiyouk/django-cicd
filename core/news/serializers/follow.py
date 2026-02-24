from rest_framework import serializers

from core.news.models import Follow


class FollowMutationSerializer(serializers.Serializer):
    TARGET_TYPE_CHOICES = [
        Follow.TARGET_EVENT,
        Follow.TARGET_STORY,
        Follow.TARGET_PERSON,
        Follow.TARGET_SOURCE,
        Follow.TARGET_ENTITY,
    ]

    target_type = serializers.ChoiceField(choices=TARGET_TYPE_CHOICES)
    target_id = serializers.CharField(max_length=128)

    def validate_target_id(self, target_id):
        cleaned = str(target_id).strip()
        if not cleaned:
            raise serializers.ValidationError("target_id cannot be empty")
        return cleaned


class FollowListQuerySerializer(serializers.Serializer):
    page = serializers.IntegerField(required=False, min_value=1, default=1)
    page_size = serializers.IntegerField(required=False, min_value=1, max_value=100, default=20)
    target_type = serializers.ChoiceField(
        choices=FollowMutationSerializer.TARGET_TYPE_CHOICES,
        required=False,
    )


class FollowSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    user_id = serializers.IntegerField(read_only=True)
    target_type = serializers.CharField(read_only=True)
    target_id = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

from rest_framework import serializers

from core.news.models import EventComment


class EventCommentCreateSerializer(serializers.Serializer):
    content = serializers.CharField(max_length=4000)

    def validate_content(self, content):
        cleaned = content.strip()
        if not cleaned:
            raise serializers.ValidationError("content cannot be empty")
        return cleaned


class EventCommentReplySerializer(serializers.Serializer):
    content = serializers.CharField(max_length=4000)

    def validate_content(self, content):
        cleaned = content.strip()
        if not cleaned:
            raise serializers.ValidationError("content cannot be empty")
        return cleaned


class EventCommentSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    event_id = serializers.CharField(read_only=True)
    content = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    author_id = serializers.IntegerField(read_only=True)
    reply_to = serializers.IntegerField(read_only=True, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    replies = serializers.SerializerMethodField()

    def get_replies(self, obj):
        children_map = self.context.get("children_map", {})
        children = children_map.get(obj.id, [])
        return EventCommentSerializer(children, many=True, context=self.context).data


class EventCommentStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=[
        EventComment.STATUS_APPROVED,
        EventComment.STATUS_REJECTED,
    ])

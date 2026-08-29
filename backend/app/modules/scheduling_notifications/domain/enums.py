import enum


class NotificationStatus(enum.StrEnum):
    pending = "pending"
    sent = "sent"
    cancelled = "cancelled"
    failed = "failed"

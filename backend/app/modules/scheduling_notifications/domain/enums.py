import enum


class NotificationStatus(str, enum.Enum):
    pending = "pending"
    sent = "sent"
    cancelled = "cancelled"
    failed = "failed"

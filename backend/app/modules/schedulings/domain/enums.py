import enum


class SchedulingStatus(enum.StrEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class SchedulingSource(enum.StrEnum):
    WHATSAPP = "whatsapp"
    APP = "app"


class CancelledByType(enum.StrEnum):
    CLIENT = "client"
    ESTABLISHMENT = "establishment"
    SYSTEM = "system"


class ChangedBySource(enum.StrEnum):
    USER = "user"
    CLIENT = "client"
    SYSTEM = "system"

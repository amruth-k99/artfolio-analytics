"""
Application-wide constants for dimension table values.

These are NOT database-backed — they're pure Python constants for
validation and consistency across the codebase.
"""

# Event types that are seeded into d_event_types on startup
EVENT_TYPES = [
    "PAGE_VIEW",
    "CLICK",
    "LOGIN",
    "LOGOUT",
    "REGISTER",
    "PORTFOLIO_CREATED",
    "PORTFOLIO_UPDATED",
    "PORTFOLIO_DELETED",
    "PORTFOLIO_VIEWED",
]

# Referral categories (matches Literal on ReferralSources model)
REFERRAL_CATEGORIES = ["social", "search", "email", "direct", "other"]

# Visitor types (matches Literal on Visitors model)
VISITOR_TYPES = ["new", "returning"]

# User types (matches Literal on Visitors model)
USER_TYPES = ["guest", "user", "admin"]

# Account statuses (matches Literal on Visitors model)
ACCOUNT_STATUSES = ["active", "inactive", "deleted"]

# Device types
DEVICE_TYPES = ["desktop", "mobile", "tablet"]

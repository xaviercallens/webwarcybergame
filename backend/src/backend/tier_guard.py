"""
Tier-gated access dependency for FastAPI.
Ensures the current player meets the minimum subscription tier for an endpoint.
"""
from fastapi import Depends, HTTPException, status
from backend import auth, models

# Tier hierarchy (higher index = higher tier)
_TIER_ORDER = [
    models.SubscriptionTier.FREE,
    models.SubscriptionTier.CYBER_PASS,
    models.SubscriptionTier.DEV_API,
    models.SubscriptionTier.ENTERPRISE,
]


def _tier_level(tier: models.SubscriptionTier) -> int:
    try:
        return _TIER_ORDER.index(tier)
    except ValueError:
        return 0


def require_tier(minimum_tier: models.SubscriptionTier):
    """
    FastAPI dependency factory that checks if the current user's subscription
    tier meets the minimum required tier for an endpoint.

    Usage:
        @app.get("/api/premium-feature")
        def premium(user = Depends(require_tier(SubscriptionTier.CYBER_PASS))):
            ...
    """
    def dependency(current_user: models.Player = Depends(auth.get_current_user)):
        user_level = _tier_level(current_user.subscription_tier)
        required_level = _tier_level(minimum_tier)
        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "TIER_INSUFFICIENT",
                    "message": f"This feature requires {minimum_tier.value} tier or higher.",
                    "current_tier": current_user.subscription_tier.value,
                    "required_tier": minimum_tier.value,
                }
            )
        return current_user
    return dependency

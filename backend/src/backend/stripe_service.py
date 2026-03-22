"""
Stripe integration service for WebWarCyberGame subscription management.
Uses Stripe Checkout Sessions for payment and webhooks for lifecycle events.
"""
import os
import hashlib
import secrets
from typing import Optional

import stripe

from backend.models import SubscriptionTier

# ── Stripe Configuration ──
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "sk_test_placeholder")
WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "whsec_test_placeholder")

# Price IDs from Stripe Dashboard (test mode)
PRICE_MAP = {
    SubscriptionTier.CYBER_PASS: os.environ.get("STRIPE_PRICE_CYBER_PASS", "price_cyber_pass_test"),
    SubscriptionTier.DEV_API: os.environ.get("STRIPE_PRICE_DEV_API", "price_dev_api_test"),
    SubscriptionTier.ENTERPRISE: os.environ.get("STRIPE_PRICE_ENTERPRISE", "price_enterprise_test"),
}

TIER_NAMES = {
    SubscriptionTier.FREE: "Operative (Free)",
    SubscriptionTier.CYBER_PASS: "Cyber-Pass — $9.99/season",
    SubscriptionTier.DEV_API: "Developer API — $4.99/mo",
    SubscriptionTier.ENTERPRISE: "Enterprise Enclave — $500/mo",
}

BASE_URL = os.environ.get("APP_BASE_URL", "http://localhost:8000")


def create_checkout_session(tier: SubscriptionTier, player_id: int, player_email: Optional[str] = None) -> str:
    """Create a Stripe Checkout Session and return the URL."""
    price_id = PRICE_MAP.get(tier)
    if not price_id:
        raise ValueError(f"No Stripe price configured for tier: {tier}")

    session_params = {
        "mode": "subscription",
        "line_items": [{"price": price_id, "quantity": 1}],
        "success_url": f"{BASE_URL}/?subscription=success&tier={tier.value}",
        "cancel_url": f"{BASE_URL}/?subscription=cancelled",
        "metadata": {"player_id": str(player_id), "tier": tier.value},
    }
    if player_email:
        session_params["customer_email"] = player_email

    session = stripe.checkout.Session.create(**session_params)
    return session.url


def cancel_subscription(stripe_subscription_id: str) -> dict:
    """Cancel a subscription at the end of the current billing period."""
    sub = stripe.Subscription.modify(
        stripe_subscription_id,
        cancel_at_period_end=True
    )
    return {"status": sub.status, "cancel_at_period_end": sub.cancel_at_period_end}


def get_portal_url(stripe_customer_id: str) -> str:
    """Generate a Stripe Customer Portal session URL."""
    session = stripe.billing_portal.Session.create(
        customer=stripe_customer_id,
        return_url=f"{BASE_URL}/?view=subscription",
    )
    return session.url


def construct_webhook_event(payload: bytes, sig_header: str):
    """Verify and construct a Stripe webhook event."""
    return stripe.Webhook.construct_event(payload, sig_header, WEBHOOK_SECRET)


def generate_api_token() -> tuple[str, str]:
    """Generate a new API token. Returns (raw_token, hashed_token)."""
    raw = secrets.token_urlsafe(48)
    hashed = hashlib.sha256(raw.encode()).hexdigest()
    return raw, hashed


def hash_token(raw_token: str) -> str:
    """Hash a raw API token for lookup."""
    return hashlib.sha256(raw_token.encode()).hexdigest()

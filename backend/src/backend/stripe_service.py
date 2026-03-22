"""
Stripe integration service for WebWarCyberGame subscription management.
Uses Stripe Checkout Sessions with Google Pay support for payment.
Configured for Google Cloud Platform deployment.
"""
import os
import hashlib
import secrets
from typing import Optional

import stripe

from backend.models import SubscriptionTier

# ── Stripe Configuration ──
# In production on GCP, these are set via Cloud Run environment variables
# or Secret Manager references. For local dev, use .env or export.
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "sk_test_placeholder")
WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "whsec_test_placeholder")

# Price IDs from Stripe Dashboard (test mode)
# Create these in Stripe Dashboard → Products → Pricing
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

# ── GCP / Google Pay Configuration ──
# BASE_URL should point to your Cloud Run service URL in production
BASE_URL = os.environ.get("APP_BASE_URL", "http://localhost:8000")

# Google Pay is enabled automatically in Stripe Checkout when:
# 1. Google Pay is enabled in Stripe Dashboard → Settings → Payment methods
# 2. The checkout session uses payment_method_types that include 'card'
# Stripe handles the Google Pay button rendering within its hosted checkout page.
# No additional merchant ID is needed for Stripe Checkout (Stripe handles it).
# For custom Google Pay integration outside Stripe Checkout:
GOOGLE_PAY_MERCHANT_ID = os.environ.get("GOOGLE_PAY_MERCHANT_ID", "BCR2DN4T7X5XVLSW")
GOOGLE_PAY_MERCHANT_NAME = os.environ.get("GOOGLE_PAY_MERCHANT_NAME", "Neo-Hack: Gridlock")
GOOGLE_PAY_ENVIRONMENT = os.environ.get("GOOGLE_PAY_ENVIRONMENT", "TEST")  # "TEST" or "PRODUCTION"


def create_checkout_session(
    tier: SubscriptionTier,
    player_id: int,
    player_email: Optional[str] = None,
) -> str:
    """
    Create a Stripe Checkout Session with Google Pay enabled.
    Google Pay appears automatically in Stripe Checkout when enabled
    in your Stripe Dashboard payment method settings.
    """
    price_id = PRICE_MAP.get(tier)
    if not price_id:
        raise ValueError(f"No Stripe price configured for tier: {tier}")

    session_params = {
        "mode": "subscription",
        "line_items": [{"price": price_id, "quantity": 1}],
        "success_url": f"{BASE_URL}/?subscription=success&tier={tier.value}",
        "cancel_url": f"{BASE_URL}/?subscription=cancelled",
        "metadata": {"player_id": str(player_id), "tier": tier.value},
        # Enable automatic tax collection for international compliance
        # "automatic_tax": {"enabled": True},
        # Allow promotion codes for marketing campaigns
        "allow_promotion_codes": True,
        # Payment method types — 'card' enables Google Pay + Apple Pay automatically
        "payment_method_types": ["card"],
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
    """Generate a Stripe Customer Portal session URL for self-serve billing."""
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


def get_google_pay_config() -> dict:
    """
    Return Google Pay configuration for client-side integration.
    This is used when you want a custom Google Pay button outside Stripe Checkout
    (e.g., for in-app purchases or direct payment requests).
    """
    return {
        "environment": GOOGLE_PAY_ENVIRONMENT,
        "merchantInfo": {
            "merchantId": GOOGLE_PAY_MERCHANT_ID,
            "merchantName": GOOGLE_PAY_MERCHANT_NAME,
        },
        "allowedPaymentMethods": [{
            "type": "CARD",
            "parameters": {
                "allowedAuthMethods": ["PAN_ONLY", "CRYPTOGRAM_3DS"],
                "allowedCardNetworks": ["MASTERCARD", "VISA", "AMEX", "DISCOVER"],
            },
            "tokenizationSpecification": {
                "type": "PAYMENT_GATEWAY",
                "parameters": {
                    "gateway": "stripe",
                    "stripe:version": "2023-10-16",
                    "stripe:publishableKey": os.environ.get(
                        "STRIPE_PUBLISHABLE_KEY", "pk_test_placeholder"
                    ),
                },
            },
        }],
    }

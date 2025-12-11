# license_server.py
"""
Quantum Foam RNG - License Server
Handles license key generation, validation, and usage tracking
"""

import secrets
import hashlib
import hmac
import time
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

class LicenseTier(Enum):
    """License tiers with different capabilities"""
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"

@dataclass
class License:
    """License key data structure"""
    key: str
    tier: LicenseTier
    customer_id: str
    customer_email: str
    issued_at: datetime
    expires_at: Optional[datetime]
    max_requests_per_month: int
    requests_this_month: int = 0
    last_reset: datetime = None
    is_active: bool = True
    metadata: Dict = None
    
    def __post_init__(self):
        if self.last_reset is None:
            self.last_reset = datetime.now()
        if self.metadata is None:
            self.metadata = {}

class LicenseGenerator:
    """Generates cryptographically secure license keys"""
    
    def __init__(self, secret_key: str):
        """
        Args:
            secret_key: Server secret for HMAC signing (keep this SECRET!)
        """
        self.secret_key = secret_key.encode()
    
    def generate_key(self, customer_id: str, tier: LicenseTier) -> str:
        """
        Generate a license key with format:
        QFRNG-{TIER}-{RANDOM}-{CHECKSUM}
        
        Example: QFRNG-PRO-X7K9M2P4-A3F8
        """
        # Random component (8 chars, uppercase alphanumeric)
        random_part = self._generate_random_alphanum(8)
        
        # Create base key
        base_key = f"QFRNG-{tier.value.upper()}-{random_part}"
        
        # Generate checksum
        checksum = self._generate_checksum(base_key, customer_id)
        
        # Final key
        return f"{base_key}-{checksum}"
    
    def _generate_random_alphanum(self, length: int) -> str:
        """Generate random alphanumeric string (excluding ambiguous chars)"""
        # Exclude: 0, O, 1, I, L to avoid confusion
        chars = "23456789ABCDEFGHJKMNPQRSTUVWXYZ"
        return ''.join(secrets.choice(chars) for _ in range(length))
    
    def _generate_checksum(self, base_key: str, customer_id: str) -> str:
        """Generate HMAC checksum for key validation"""
        data = f"{base_key}:{customer_id}".encode()
        mac = hmac.new(self.secret_key, data, hashlib.sha256)
        # Take first 4 bytes and convert to hex
        return mac.hexdigest()[:4].upper()
    
    def validate_key_format(self, key: str, customer_id: str) -> bool:
        """Validate key format and checksum"""
        try:
            parts = key.split('-')
            if len(parts) != 4:
                return False
            
            prefix, tier, random, checksum = parts
            
            if prefix != "QFRNG":
                return False
            
            # Reconstruct base key and verify checksum
            base_key = f"{prefix}-{tier}-{random}"
            expected_checksum = self._generate_checksum(base_key, customer_id)
            
            return hmac.compare_digest(checksum, expected_checksum)
        except Exception:
            return False

class LicenseManager:
    """Manages license validation, usage tracking, and rate limiting"""
    
    def __init__(self, secret_key: str):
        self.generator = LicenseGenerator(secret_key)
        self.licenses: Dict[str, License] = {}
        
        # Tier configurations
        self.tier_limits = {
            LicenseTier.FREE: 1000,           # 1K requests/month
            LicenseTier.PRO: 100000,          # 100K requests/month
            LicenseTier.ENTERPRISE: 10000000  # 10M requests/month
        }
    
    def create_license(
        self,
        customer_id: str,
        customer_email: str,
        tier: LicenseTier,
        duration_days: Optional[int] = None
    ) -> License:
        """Create a new license"""
        key = self.generator.generate_key(customer_id, tier)
        
        issued_at = datetime.now()
        expires_at = None
        if duration_days:
            expires_at = issued_at + timedelta(days=duration_days)
        
        license = License(
            key=key,
            tier=tier,
            customer_id=customer_id,
            customer_email=customer_email,
            issued_at=issued_at,
            expires_at=expires_at,
            max_requests_per_month=self.tier_limits[tier],
            last_reset=issued_at
        )
        
        self.licenses[key] = license
        return license
    
    def validate_license(self, key: str, customer_id: str) -> Tuple[bool, Optional[str]]:
        """
        Validate a license key
        
        Returns:
            (is_valid, error_message)
        """
        # Check format
        if not self.generator.validate_key_format(key, customer_id):
            return False, "Invalid key format or checksum"
        
        # Check if key exists
        if key not in self.licenses:
            return False, "License key not found"
        
        license = self.licenses[key]
        
        # Check if active
        if not license.is_active:
            return False, "License has been revoked"
        
        # Check expiration
        if license.expires_at and datetime.now() > license.expires_at:
            return False, "License has expired"
        
        # Check customer ID match
        if license.customer_id != customer_id:
            return False, "Customer ID mismatch"
        
        return True, None
    
    def check_rate_limit(self, key: str) -> Tuple[bool, Dict]:
        """
        Check if license has available quota
        
        Returns:
            (has_quota, usage_info)
        """
        if key not in self.licenses:
            return False, {"error": "Invalid license"}
        
        license = self.licenses[key]
        
        # Reset monthly counter if needed
        now = datetime.now()
        if (now - license.last_reset).days >= 30:
            license.requests_this_month = 0
            license.last_reset = now
        
        # Check quota
        has_quota = license.requests_this_month < license.max_requests_per_month
        
        usage_info = {
            "tier": license.tier.value,
            "requests_used": license.requests_this_month,
            "requests_limit": license.max_requests_per_month,
            "quota_remaining": license.max_requests_per_month - license.requests_this_month,
            "reset_date": (license.last_reset + timedelta(days=30)).isoformat()
        }
        
        return has_quota, usage_info
    
    def record_usage(self, key: str, num_requests: int = 1) -> bool:
        """Record API usage for a license"""
        if key not in self.licenses:
            return False
        
        license = self.licenses[key]
        license.requests_this_month += num_requests
        return True
    
    def revoke_license(self, key: str) -> bool:
        """Revoke a license"""
        if key in self.licenses:
            self.licenses[key].is_active = False
            return True
        return False
    
    def get_license_info(self, key: str) -> Optional[Dict]:
        """Get detailed license information"""
        if key not in self.licenses:
            return None
        
        license = self.licenses[key]
        return {
            "key": license.key,
            "tier": license.tier.value,
            "customer_email": license.customer_email,
            "issued_at": license.issued_at.isoformat(),
            "expires_at": license.expires_at.isoformat() if license.expires_at else None,
            "is_active": license.is_active,
            "usage": {
                "requests_this_month": license.requests_this_month,
                "max_requests_per_month": license.max_requests_per_month,
                "last_reset": license.last_reset.isoformat()
            }
        }


# Example usage
if __name__ == "__main__":
    # Initialize with your secret key (KEEP THIS SECRET!)
    SECRET_KEY = secrets.token_hex(32)  # Generate once and store securely
    print(f"🔐 Server Secret Key (SAVE THIS): {SECRET_KEY}\n")
    
    manager = LicenseManager(SECRET_KEY)
    
    # Create licenses
    print("=" * 60)
    print("Creating Sample Licenses")
    print("=" * 60)
    
    # Free tier
    free_license = manager.create_license(
        customer_id="CUST-001",
        customer_email="user@example.com",
        tier=LicenseTier.FREE
    )
    print(f"\n✅ FREE License Created:")
    print(f"   Key: {free_license.key}")
    print(f"   Quota: {free_license.max_requests_per_month:,} requests/month")
    
    # Pro tier (1 year)
    pro_license = manager.create_license(
        customer_id="CUST-002",
        customer_email="pro@company.com",
        tier=LicenseTier.PRO,
        duration_days=365
    )
    print(f"\n💎 PRO License Created:")
    print(f"   Key: {pro_license.key}")
    print(f"   Quota: {pro_license.max_requests_per_month:,} requests/month")
    print(f"   Expires: {pro_license.expires_at.strftime('%Y-%m-%d')}")
    
    # Enterprise tier
    ent_license = manager.create_license(
        customer_id="CUST-003",
        customer_email="enterprise@bigcorp.com",
        tier=LicenseTier.ENTERPRISE
    )
    print(f"\n🏢 ENTERPRISE License Created:")
    print(f"   Key: {ent_license.key}")
    print(f"   Quota: {ent_license.max_requests_per_month:,} requests/month")
    
    # Validate licenses
    print("\n" + "=" * 60)
    print("Testing License Validation")
    print("=" * 60)
    
    valid, error = manager.validate_license(pro_license.key, "CUST-002")
    print(f"\n✓ Valid key: {valid}")
    
    valid, error = manager.validate_license(pro_license.key, "WRONG-CUSTOMER")
    print(f"✗ Wrong customer: {valid} - {error}")
    
    # Test rate limiting
    print("\n" + "=" * 60)
    print("Testing Rate Limiting")
    print("=" * 60)
    
    has_quota, usage = manager.check_rate_limit(pro_license.key)
    print(f"\n📊 Usage Info:")
    print(f"   Tier: {usage['tier'].upper()}")
    print(f"   Used: {usage['requests_used']:,}")
    print(f"   Remaining: {usage['quota_remaining']:,}")
    
    # Simulate usage
    manager.record_usage(pro_license.key, 50)
    has_quota, usage = manager.check_rate_limit(pro_license.key)
    print(f"\n📊 After 50 requests:")
    print(f"   Used: {usage['requests_used']:,}")
    print(f"   Remaining: {usage['quota_remaining']:,}")

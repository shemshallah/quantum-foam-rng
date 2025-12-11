# quantum_foam_pro.py
"""
Quantum Foam RNG - Pro Edition Client
With integrated license key validation
"""

import requests
import json
from typing import List, Optional, Dict
from datetime import datetime

class LicenseError(Exception):
    """Raised when license validation fails"""
    pass

class QuotaExceededError(Exception):
    """Raised when API quota is exceeded"""
    pass

class QuantumFoamPro:
    """
    Pro edition with license key authentication
    """
    
    def __init__(
        self,
        license_key: str,
        customer_id: str,
        api_url: str = "https://api.quantumfoam.io"
    ):
        """
        Initialize Pro client with license key
        
        Args:
            license_key: Your QFRNG Pro license key
            customer_id: Your customer ID
            api_url: API endpoint (default: production)
        """
        self.license_key = license_key
        self.customer_id = customer_id
        self.api_url = api_url.rstrip('/')
        
        # Validate license on initialization
        self._validate_license()
        
        # Cache license info
        self.license_info = None
        self._fetch_license_info()
    
    def _validate_license(self):
        """Validate license key with server"""
        try:
            response = requests.post(
                f"{self.api_url}/v1/validate",
                json={
                    "license_key": self.license_key,
                    "customer_id": self.customer_id
                },
                timeout=10
            )
            
            if response.status_code == 401:
                raise LicenseError("Invalid license key or customer ID")
            elif response.status_code == 403:
                data = response.json()
                raise LicenseError(f"License error: {data.get('error', 'Unknown error')}")
            elif response.status_code != 200:
                raise LicenseError(f"License validation failed: {response.status_code}")
            
        except requests.RequestException as e:
            raise LicenseError(f"Could not connect to license server: {e}")
    
    def _fetch_license_info(self):
        """Fetch license information and quota status"""
        try:
            response = requests.get(
                f"{self.api_url}/v1/license/info",
                headers=self._get_auth_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                self.license_info = response.json()
        except:
            pass  # Non-critical, continue without cached info
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for API requests"""
        return {
            "Authorization": f"Bearer {self.license_key}",
            "X-Customer-ID": self.customer_id,
            "User-Agent": "QuantumFoamPro/1.0"
        }
    
    def get_quota_status(self) -> Dict:
        """
        Check current quota status
        
        Returns:
            dict with keys: tier, requests_used, requests_limit, quota_remaining, reset_date
        """
        response = requests.get(
            f"{self.api_url}/v1/quota",
            headers=self._get_auth_headers(),
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise LicenseError(f"Could not fetch quota: {response.status_code}")
    
    def get_optimized_bases(self) -> List[tuple]:
        """
        Fetch the 75 optimized measurement bases (PRO ONLY)
        
        This is the secret sauce - only available to Pro/Enterprise tiers
        
        Returns:
            List of (theta, phi) tuples for optimized bases
        """
        response = requests.get(
            f"{self.api_url}/v1/bases/optimized",
            headers=self._get_auth_headers(),
            timeout=10
        )
        
        if response.status_code == 403:
            data = response.json()
            if "quota" in data.get("error", "").lower():
                raise QuotaExceededError(
                    f"Monthly quota exceeded. Resets on {data.get('reset_date')}"
                )
            raise LicenseError(f"Access denied: {data.get('error')}")
        elif response.status_code != 200:
            raise LicenseError(f"Could not fetch bases: {response.status_code}")
        
        data = response.json()
        return [(b['theta'], b['phi']) for b in data['bases']]
    
    def generate_random_bits(
        self,
        num_bits: int,
        basis_optimization: str = "pro"
    ) -> str:
        """
        Generate quantum random bits using optimized bases
        
        Args:
            num_bits: Number of random bits to generate
            basis_optimization: "pro" or "enterprise" (enterprise has lower noise)
        
        Returns:
            String of random bits (e.g., "101010110...")
        """
        response = requests.post(
            f"{self.api_url}/v1/generate",
            headers=self._get_auth_headers(),
            json={
                "num_bits": num_bits,
                "optimization": basis_optimization
            },
            timeout=30
        )
        
        if response.status_code == 403:
            data = response.json()
            if "quota" in data.get("error", "").lower():
                raise QuotaExceededError(
                    f"Monthly quota exceeded. Resets on {data.get('reset_date')}"
                )
            raise LicenseError(f"Access denied: {data.get('error')}")
        elif response.status_code != 200:
            raise LicenseError(f"Generation failed: {response.status_code}")
        
        return response.json()['bits']
    
    def generate_random_integer(self, min_val: int, max_val: int) -> int:
        """Generate random integer in range [min_val, max_val]"""
        bits_needed = (max_val - min_val).bit_length()
        bits = self.generate_random_bits(bits_needed)
        value = int(bits, 2)
        return min_val + (value % (max_val - min_val + 1))
    
    def generate_random_float(self, min_val: float = 0.0, max_val: float = 1.0) -> float:
        """Generate random float in range [min_val, max_val]"""
        bits = self.generate_random_bits(53)  # Double precision
        normalized = int(bits, 2) / (2**53 - 1)
        return min_val + normalized * (max_val - min_val)
    
    def print_license_info(self):
        """Print formatted license information"""
        if not self.license_info:
            self._fetch_license_info()
        
        info = self.license_info
        print("=" * 60)
        print("QUANTUM FOAM RNG - PRO LICENSE")
        print("=" * 60)
        print(f"Tier:        {info['tier'].upper()}")
        print(f"Email:       {info['customer_email']}")
        print(f"Status:      {'✓ Active' if info['is_active'] else '✗ Inactive'}")
        print(f"Issued:      {info['issued_at'][:10]}")
        if info['expires_at']:
            print(f"Expires:     {info['expires_at'][:10]}")
        print("\n" + "-" * 60)
        print("USAGE THIS MONTH")
        print("-" * 60)
        usage = info['usage']
        used = usage['requests_this_month']
        limit = usage['max_requests_per_month']
        remaining = limit - used
        pct = (used / limit) * 100 if limit > 0 else 0
        
        print(f"Used:        {used:,} requests")
        print(f"Limit:       {limit:,} requests/month")
        print(f"Remaining:   {remaining:,} requests")
        print(f"Usage:       {pct:.1f}%")
        print(f"Resets:      {usage['last_reset'][:10]}")
        print("=" * 60)


# Example usage
if __name__ == "__main__":
    """
    IMPORTANT: This example uses placeholder values.
    Replace with your actual license key from the license server.
    """
    
    # Example license key (from license server output)
    LICENSE_KEY = "QFRNG-PRO-X7K9M2P4-A3F8"
    CUSTOMER_ID = "CUST-002"
    
    print("Initializing Quantum Foam RNG Pro...\n")
    
    try:
        # Initialize client
        qf = QuantumFoamPro(
            license_key=LICENSE_KEY,
            customer_id=CUSTOMER_ID,
            api_url="https://api.quantumfoam.io"  # Your API endpoint
        )
        
        print("✓ License validated successfully!\n")
        
        # Show license info
        qf.print_license_info()
        
        print("\n" + "=" * 60)
        print("GENERATING QUANTUM RANDOM NUMBERS")
        print("=" * 60)
        
        # Generate random bits
        bits = qf.generate_random_bits(32)
        print(f"\n32 Random Bits:\n{bits}")
        
        # Generate random integer
        rand_int = qf.generate_random_integer(1, 100)
        print(f"\nRandom Integer (1-100): {rand_int}")
        
        # Generate random float
        rand_float = qf.generate_random_float(0.0, 1.0)
        print(f"Random Float (0-1): {rand_float:.10f}")
        
        # Check quota
        print("\n" + "=" * 60)
        quota = qf.get_quota_status()
        print(f"Quota Remaining: {quota['quota_remaining']:,} requests")
        print(f"Resets: {quota['reset_date'][:10]}")
        
    except LicenseError as e:
        print(f"❌ License Error: {e}")
        print("\nPlease check:")
        print("  1. Your license key is correct")
        print("  2. Your customer ID matches the license")
        print("  3. Your license hasn't expired")
        print("  4. You have an active subscription")
        
    except QuotaExceededError as e:
        print(f"❌ Quota Exceeded: {e}")
        print("\nYour monthly quota has been used up.")
        print("Options:")
        print("  1. Wait until quota resets next month")
        print("  2. Upgrade to a higher tier")
        print("  3. Purchase additional quota")
        
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")

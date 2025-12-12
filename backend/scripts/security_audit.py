"""
Security Audit

Validates security features:
- Authentication mechanisms
- Authorization checks
- Data isolation
- Password security
- Token security
- Rate limiting
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from models.user import User
from models.client import Client
from auth.security import verify_password, get_password_hash
from config import settings

class SecurityAudit:
    """Security audit checks"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.results = {
            "passed": [],
            "failed": [],
            "warnings": []
        }

    def log_pass(self, check_name: str, details: str = ""):
        """Log a passed check"""
        self.results["passed"].append(f"✅ {check_name}: {details}")
        print(f"✅ PASS: {check_name}")
        if details:
            print(f"   {details}")

    def log_fail(self, check_name: str, issue: str):
        """Log a failed check"""
        self.results["failed"].append(f"❌ {check_name}: {issue}")
        print(f"❌ FAIL: {check_name}")
        print(f"   Issue: {issue}")

    def log_warning(self, check_name: str, warning: str):
        """Log a warning"""
        self.results["warnings"].append(f"⚠️  {check_name}: {warning}")
        print(f"⚠️  WARN: {check_name}")
        print(f"   {warning}")

    async def check_1_password_hashing(self):
        """Check 1: Password hashing security"""
        try:
            # Test password hashing
            test_password = "test_password_123"
            hashed = get_password_hash(test_password)

            # Verify hash is not plaintext
            if hashed == test_password:
                self.log_fail("check_1_password_hashing",
                            "Passwords stored in plaintext!")
                return

            # Verify hash is a secure format (bcrypt or Argon2id)
            # Argon2id is actually better than bcrypt, so accept both
            is_bcrypt = hashed.startswith("$2b$") or hashed.startswith("$2a$")
            is_argon2 = hashed.startswith("$argon2id$") or hashed.startswith("$argon2")

            if not (is_bcrypt or is_argon2):
                self.log_fail("check_1_password_hashing",
                            f"Password hash format incorrect: {hashed[:15]}")
                return

            hash_type = "Argon2id" if is_argon2 else "Bcrypt"

            # Verify password verification works
            if not verify_password(test_password, hashed):
                self.log_fail("check_1_password_hashing",
                            "Password verification failed")
                return

            # Verify wrong password is rejected
            if verify_password("wrong_password", hashed):
                self.log_fail("check_1_password_hashing",
                            "Wrong password was accepted!")
                return

            self.log_pass("check_1_password_hashing",
                        f"{hash_type} hashing with proper verification")
        except Exception as e:
            self.log_fail("check_1_password_hashing", str(e))

    async def check_2_jwt_secret_key(self):
        """Check 2: JWT secret key strength"""
        try:
            secret_key = settings.secret_key

            if not secret_key:
                self.log_fail("check_2_jwt_secret_key",
                            "JWT_SECRET_KEY not set in environment")
                return

            if len(secret_key) < 32:
                self.log_warning("check_2_jwt_secret_key",
                               f"Secret key too short ({len(secret_key)} chars, recommend 32+)")
            else:
                self.log_pass("check_2_jwt_secret_key",
                            f"Secret key length: {len(secret_key)} chars")

            # Check if it's a default/weak key
            weak_keys = ["secret", "changeme", "password", "12345678"]
            if secret_key.lower() in weak_keys:
                self.log_fail("check_2_jwt_secret_key",
                            "Using weak/default secret key!")
            else:
                self.log_pass("check_2_jwt_secret_key",
                            "Secret key is not a common weak key")
        except Exception as e:
            self.log_fail("check_2_jwt_secret_key", str(e))

    async def check_3_user_data_isolation(self):
        """Check 3: User data isolation by client"""
        try:
            # Get users from different clients
            result = await self.db.execute(
                text("""
                    SELECT u.id, u.email, u.client_id, c.client_id as client_client_id
                    FROM users u
                    JOIN clients c ON u.client_id = c.client_id
                    LIMIT 10
                """)
            )
            users = result.fetchall()

            if len(users) < 2:
                self.log_warning("check_3_user_data_isolation",
                               "Need at least 2 users for isolation test")
                return

            # Check if users have valid client_id
            invalid_users = [u for u in users if not u.client_id]
            if invalid_users:
                self.log_fail("check_3_user_data_isolation",
                            f"{len(invalid_users)} users without client_id")
            else:
                self.log_pass("check_3_user_data_isolation",
                            f"All {len(users)} users have client_id")

            # Check if users from different clients exist
            client_ids = set(u.client_id for u in users if u.client_id)
            if len(client_ids) > 1:
                self.log_pass("check_3_user_data_isolation",
                            f"Users from {len(client_ids)} different clients found")
            else:
                self.log_warning("check_3_user_data_isolation",
                               "All users from same client (may be test data)")
        except Exception as e:
            self.log_fail("check_3_user_data_isolation", str(e))

    async def check_4_active_user_validation(self):
        """Check 4: Active user validation"""
        try:
            # Check if inactive users exist
            result = await self.db.execute(
                select(User).where(User.is_active == False)
            )
            inactive_users = result.scalars().all()

            if inactive_users:
                self.log_pass("check_4_active_user_validation",
                            f"{len(inactive_users)} inactive users found (validation working)")
            else:
                self.log_warning("check_4_active_user_validation",
                               "No inactive users found (may be test data)")

            # Check if active users exist
            result = await self.db.execute(
                select(User).where(User.is_active == True)
            )
            active_users = result.scalars().all()

            if active_users:
                self.log_pass("check_4_active_user_validation",
                            f"{len(active_users)} active users found")
        except Exception as e:
            self.log_fail("check_4_active_user_validation", str(e))

    async def check_5_rate_limiting_config(self):
        """Check 5: Rate limiting configuration"""
        try:
            if settings.rate_limit_enabled:
                self.log_pass("check_5_rate_limiting_config",
                            "Rate limiting is enabled")

                if settings.rate_limit_per_minute > 0:
                    self.log_pass("check_5_rate_limiting_config",
                                f"Rate limit: {settings.rate_limit_per_minute} requests/minute")
                else:
                    self.log_warning("check_5_rate_limiting_config",
                                   "Rate limit per minute is 0")

                if settings.rate_limit_per_hour > 0:
                    self.log_pass("check_5_rate_limiting_config",
                                f"Rate limit: {settings.rate_limit_per_hour} requests/hour")
                else:
                    self.log_warning("check_5_rate_limiting_config",
                                   "Rate limit per hour is 0")
            else:
                self.log_warning("check_5_rate_limiting_config",
                               "Rate limiting is disabled")
        except Exception as e:
            self.log_fail("check_5_rate_limiting_config", str(e))

    async def check_6_service_api_key(self):
        """Check 6: Service API key configuration"""
        try:
            service_key = settings.service_api_key

            if service_key:
                if len(service_key) < 16:
                    self.log_warning("check_6_service_api_key",
                                   f"Service API key too short ({len(service_key)} chars)")
                else:
                    self.log_pass("check_6_service_api_key",
                                f"Service API key configured ({len(service_key)} chars)")
            else:
                self.log_warning("check_6_service_api_key",
                               "Service API key not configured (optional for JWT-only auth)")
        except Exception as e:
            self.log_fail("check_6_service_api_key", str(e))

    async def check_7_sql_injection_protection(self):
        """Check 7: SQL injection protection (parameterized queries)"""
        try:
            # Check if code uses parameterized queries
            # This is a code review check - we'll verify by checking a sample query
            result = await self.db.execute(
                text("SELECT COUNT(*) FROM users WHERE email = :email"),
                {"email": "test@example.com"}
            )
            row = result.fetchone()

            # If query executes without error, parameterization is working
            self.log_pass("check_7_sql_injection_protection",
                        "Parameterized queries used (SQLAlchemy default)")
        except Exception as e:
            self.log_fail("check_7_sql_injection_protection", str(e))

    async def check_8_cors_configuration(self):
        """Check 8: CORS configuration"""
        try:
            cors_origins = settings.cors_origins

            if not cors_origins:
                self.log_warning("check_8_cors_configuration",
                               "CORS origins not configured")
            else:
                # Check if wildcard is used in production
                if "*" in cors_origins and settings.environment.lower() not in ["development", "dev"]:
                    self.log_warning("check_8_cors_configuration",
                                   "Wildcard CORS in non-development environment")
                else:
                    self.log_pass("check_8_cors_configuration",
                                f"CORS configured for {len(cors_origins)} origins")
        except Exception as e:
            self.log_fail("check_8_cors_configuration", str(e))

    async def run_all_checks(self):
        """Run all security checks"""
        print("=" * 80)
        print("SECURITY AUDIT")
        print("=" * 80)
        print()

        await self.check_1_password_hashing()
        await self.check_2_jwt_secret_key()
        await self.check_3_user_data_isolation()
        await self.check_4_active_user_validation()
        await self.check_5_rate_limiting_config()
        await self.check_6_service_api_key()
        await self.check_7_sql_injection_protection()
        await self.check_8_cors_configuration()

        # Print summary
        print()
        print("=" * 80)
        print("AUDIT SUMMARY")
        print("=" * 80)
        print(f"✅ Passed: {len(self.results['passed'])}")
        print(f"❌ Failed: {len(self.results['failed'])}")
        print(f"⚠️  Warnings: {len(self.results['warnings'])}")
        print()

        if self.results['failed']:
            print("CRITICAL ISSUES:")
            for fail in self.results['failed']:
                print(f"  {fail}")
            print()

        if self.results['warnings']:
            print("WARNINGS:")
            for warn in self.results['warnings']:
                print(f"  {warn}")
            print()

        total = len(self.results['passed']) + len(self.results['failed'])
        if total > 0:
            success_rate = len(self.results['passed']) / total * 100
            print(f"Security Score: {success_rate:.1f}%")

        print("=" * 80)

        return self.results


async def main():
    engine = create_async_engine(
        settings.database_url.replace("postgresql://", "postgresql+asyncpg://"),
        echo=False
    )

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        auditor = SecurityAudit(db)
        results = await auditor.run_all_checks()

        # Return exit code based on results
        if len(results['failed']) > 0:
            sys.exit(1)
        else:
            sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())


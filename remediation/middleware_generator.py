"""
AstraCrew: Defensive Input Sanitization & Pre-Execution Middleware Generator
"""

from schemas.models import AttackProbeExecution


class MiddlewareGenerator:
    """Compiles defense rules into drop-in Python ASGI middleware firewalls."""

    @staticmethod
    def generate_fastapi_middleware(failed_probes: list[AttackProbeExecution]) -> str:
        has_base64_breach = any(
            "base64" in p.injected_payload.lower() or p.probe_id == "PRB-004" for p in failed_probes
        )

        middleware_code = '''"""
AstraCrew Auto-Generated Defensive Perimeter Firewall
Generated dynamically from confirmed security audit breach traces.
Drop this into your FastAPI service to intercept injection payloads before LLM invocation.
"""
import re
import base64
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware


class PromptFirewallMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.delimiter_patterns = [
            re.compile(r"---.*?END.*?---", re.IGNORECASE),
            re.compile(r"\\[SYSTEM.*?\\]", re.IGNORECASE),
            re.compile(r"<\\|im_end\\|>", re.IGNORECASE),
            re.compile(r"<\\|im_start\\|>", re.IGNORECASE),
            re.compile(r"CANARY_[A-Za-z0-9_]+", re.IGNORECASE),
        ]
        self.override_keywords = [
            re.compile(r"ignore\\s+(?:all\\s+)?previous\\s+instructions", re.IGNORECASE),
            re.compile(r"disregard\\s+prior\\s+directives", re.IGNORECASE),
            re.compile(r"switch\\s+to\\s+debug\\s+mode", re.IGNORECASE),
            re.compile(r"act\\s+as\\s+the\\s+admin", re.IGNORECASE),
        ]

    async def dispatch(self, request: Request, call_next):
        if request.method in ["POST", "PUT"]:
            try:
                body_bytes = await request.body()
                payload = body_bytes.decode("utf-8", errors="ignore")

                for pattern in self.delimiter_patterns:
                    if pattern.search(payload):
                        raise HTTPException(
                            status_code=403,
                            detail="Security Violation: Prohibited structural delimiter detected.",
                        )

                for kw in self.override_keywords:
                    if kw.search(payload):
                        raise HTTPException(
                            status_code=403,
                            detail="Security Violation: Prompt override signature detected.",
                        )
'''
        if has_base64_breach:
            middleware_code += '''
                b64_matches = re.findall(r"([A-Za-z0-9+/]{20,}={0,2})", payload)
                for candidate in b64_matches:
                    try:
                        decoded = base64.b64decode(candidate).decode("utf-8", errors="ignore")
                        for pattern in self.delimiter_patterns + self.override_keywords:
                            if pattern.search(decoded):
                                raise HTTPException(
                                    status_code=403,
                                    detail="Security Violation: Obfuscated injection payload detected.",
                                )
                    except Exception:
                        pass
'''
        middleware_code += '''
            except HTTPException:
                raise
            except Exception:
                pass
        return await call_next(request)

# Example Usage:
# app = FastAPI()
# app.add_middleware(PromptFirewallMiddleware)
'''
        return middleware_code
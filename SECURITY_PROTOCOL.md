# AFS FastAPI Security Protocol

## Explicit Approval for Security-Sensitive Changes

**CRITICAL REQUIREMENT**: All changes identified as security-sensitive MUST undergo an explicit manual approval process before being merged into the main codebase. This is in addition to automated safety validations.

### Definition of Security-Sensitive Changes:

Changes are considered security-sensitive if they:
- Introduce new network communication protocols or modify existing ones.
- Affect authentication, authorization, or access control mechanisms.
- Handle sensitive data (e.g., GPS coordinates, operational telemetry, personal data).
- Modify core safety logic (e.g., emergency stop systems, collision avoidance).
- Introduce or modify cryptographic operations.
- Affect external interfaces or third-party integrations.

### Approval Process:

1.  **Identification**: Developers (human or AI) MUST flag changes as security-sensitive during the development process (e.g., in the commit message, pull request description).
2.  **Review**: Security-sensitive changes MUST be reviewed by a designated security expert or a team member with security expertise.
3.  **Approval**: The security expert MUST explicitly approve the changes (e.g., via a pull request approval, a dedicated sign-off).
4.  **Documentation**: The approval MUST be documented (e.g., in the pull request comments, commit history).

### Enforcement:

-   Automated checks (e.g., CI/CD pipelines) MAY be configured to identify pull requests flagged as security-sensitive and require specific approvals.
-   Human developers are responsible for adhering to this protocol and seeking appropriate approvals.

## Automated Safety Standards Validation

In addition to manual approval for security-sensitive changes, the project utilizes automated pre-commit hooks to ensure compliance with agricultural safety standards (e.g., ISO 18497, ISO 11783).

-   **Hook**: `.claude/hooks/safety_validation.py`
-   **Purpose**: Ensures agricultural safety standards compliance.

This automated validation serves as a first line of defense, but does not replace the need for explicit manual approval for changes deemed security-critical.

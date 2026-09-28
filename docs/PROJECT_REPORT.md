# Project Report, Testing, and Portfolio Guide

Use this as a course-report starting point. Replace bracketed items with your own results and keep the claims accurate: the repository includes a local implementation and cloud-ready adapters, but cloud resources are not deployed by default.

## Abstract

Goodplate is a full-stack personal wellness meal-planning demonstration. A React client communicates with a FastAPI REST backend. The backend authenticates demo users, stores user-specific profiles and generated meal examples in SQLite or configurable PostgreSQL, and stores uploaded image bytes in local storage or an S3-compatible bucket. A deterministic rules engine provides no-key plan generation, while an optional AI-compatible endpoint demonstrates structured requests, response validation, error handling, and local fallback. The system illustrates client-server architecture and cloud-service boundaries without presenting recommendations as clinical advice.

## Introduction and problem statement

Meal decisions can be repetitive, and separate documents or device-local data are difficult to organize. This prototype demonstrates a central account-backed place to maintain profile preferences, generate meal examples, retrieve plan history, and store food images. The project objective is to demonstrate cloud computing concepts with an executable local path and no mandatory paid service.

### Objectives

- Build a responsive client and documented REST API.
- Protect profile, plan, and file access through authentication and owner-scoped authorization.
- Keep structured records separate from image bytes.
- Generate personalized general-wellness examples from explicit preferences.
- Keep the fallback runnable without a hosted AI API or cloud credentials.
- Describe scale, availability, deployment, tests, and remaining production work honestly.

## Existing and proposed system

An unstructured, device-local approach keeps plans separate from user preferences and images. Goodplate uses a browser client, an API boundary, a relational data model, and a file-storage abstraction. The local adapters use SQLite and a local directory; cloud configuration switches the database to PostgreSQL and object bytes to an S3-compatible bucket. This does not by itself provide high availability or multi-region disaster recovery.

## Technology and architecture

- React + Vite: forms, profile, meal plan, saved plans, file library, and dashboard.
- FastAPI + Pydantic: REST routes, validation, OpenAPI docs, health endpoint, CORS.
- SQLAlchemy: users, plans, and file metadata.
- PBKDF2-HMAC-SHA256 + signed expiring token: demo authentication.
- Rules engine + optional AI-compatible chat-completions call: meal generation and fallback.
- Local files or S3-compatible storage: meal image bytes.
- GitHub Actions: frontend build/lint and backend integration checks.

The full diagram and detailed cloud-service mapping are in [ARCHITECTURE.md](ARCHITECTURE.md).

## Data flow and database design

A user registers/logs in, receives an access token, saves preferences, and requests a plan. The API derives the user ID from the verified token, checks preference filters, generates a plan, and persists it under that owner. Uploads are checked for media type/signature/size, keyed beneath the owner ID, and recorded in `user_files`. Read and delete queries include both record ID and current owner ID.

| Table | Primary key | Main fields | Relationship |
|---|---|---|---|
| `users` | `id` | email (unique), name, password hash, profile JSON, creation time | Parent of plans and file metadata |
| `plans` | `id` | owner foreign key, meal response JSON, creation time | Belongs to one user |
| `user_files` | `id` | owner foreign key, display name, object key, content type, size, creation time | Metadata for one stored image |

Cloud SQL/Firestore terminology: a relational database stores searchable structured profile/plan/file records. Object storage holds file bytes. This code uses PostgreSQL-compatible relational storage rather than Firestore; Firestore would be a valid alternative design but requires implementing a distinct persistence adapter and security rules.

## AI recommendation logic

The local rule path selects from a small in-code catalog using the requested diet and known allergy tags. It adds approximate calories/macros and a hydration reminder. If both `AI_API_URL` and `AI_API_KEY` exist, the backend sends selected profile fields to a compatible chat-completions API. It checks required meal objects, text lengths, calorie ranges, and restricted words for diet/allergy conflicts. Network, response, or validation failures trigger the local rules path. The key is read only by the backend. The result is a toy educational meal example, not a clinically validated plan.

## Authentication, APIs, and storage

Passwords are PBKDF2-HMAC-SHA256 hashed with random salts. The API signs expiring HMAC bearer tokens and looks up the subject user for each protected route. The token is held in browser session storage; logout clears the browser's copy but does not revoke already copied tokens. For public deployment, prefer managed OIDC/Firebase Auth or implement token revocation/refresh rotation and stricter account recovery. User A cannot read User B's plan/file through ordinary API operations; automated tests verify that behavior.

The API request/response details and status codes are published by FastAPI at `/docs`. File metadata is in the database; bytes use `backend/app/storage.py`. Local file storage is not durable across ephemeral container replacement; use private object storage for hosted uploads.

## Local implementation and deployment

Follow the exact local steps in the root README. For a hosted version, publish `dist/` to static hosting, deploy the backend image, configure PostgreSQL/S3-compatible secrets and exact CORS origins, then verify the public health route and owner isolation. An AWS variant could use Amplify or CloudFront for frontend, App Runner/ECS for API, RDS for PostgreSQL, S3 for images, Cognito for managed identity, Secrets Manager and CloudWatch. This starter's custom token flow must be adapted to verify Cognito tokens before claiming Cognito authentication.

## Testing strategy and results

Run `python -m unittest discover -s backend/tests -t backend -v`, `npm run build`, and `npm run lint`. The API suite uses temporary SQLite and local temporary uploads; it does not access live cloud services.

| ID | Scenario / input | Expected result | Actual / status |
|---|---|---|---|
| T01 | New registration with valid synthetic account | `201`, token returned | Automated test passed |
| T02 | Existing email with different case | `409`, no duplicate | Automated test passed |
| T03 | Valid login | `200`, token returned | Automated test passed |
| T04 | Incorrect password | `401`, generic message | Implemented; manual test not recorded |
| T05 | Protected profile without token | `401` | Automated test passed |
| T06 | Save valid profile | `200`, persisted preferences | Automated test passed |
| T07 | Invalid age/diet/goal | `422` validation error | Implemented; manual test not recorded |
| T08 | Generate plan with default profile | `201`, saved plan | Automated test passed |
| T09 | Vegan profile | No listed animal products | Automated test passed |
| T10 | Vegetarian profile | No listed meat/fish | Engine rule; standalone test not recorded |
| T11 | Allergy filter such as sesame | Matching tagged meals excluded | Automated vegan/allergy test passed |
| T12 | Different general goal | Deterministic selection can differ | Implemented; standalone test not recorded |
| T13 | AI endpoint absent | Local rules path | Automated default path passed |
| T14 | AI provider network failure | Local fallback | Automated test passed |
| T15 | AI response omits required meal | Reject response, use local fallback | Validation implemented; response case not separately tested |
| T16 | Save and list plans | Plan appears for owner | Automated test passed |
| T17 | Read own plan | `200` | Automated test passed |
| T18 | User B requests User A plan | `404` | Automated test passed |
| T19 | User B deletes User A plan | `404`; record retained | Automated test passed |
| T20 | Valid PNG upload | `201`, metadata saved | Automated test passed |
| T21 | Download own image | Original bytes returned | Automated test passed |
| T22 | User B downloads User A image | `404` | Automated test passed |
| T23 | Text file upload | `415` | Automated test passed |
| T24 | Oversized image | `413` | Implemented; manual test not recorded |
| T25 | Delete own image | Object and metadata removed | Implemented; manual test not recorded |
| T26 | Storage provider unavailable | `503` for file operation | Implemented; failure test not recorded |
| T27 | Database unavailable | API error; no false success | No live failure-injection test |
| T28 | Logout in browser | Local token removed; sign-in shown | Frontend flow implemented; manual test not recorded |
| T29 | Responsive desktop dashboard | Layout fits desktop | Manual browser proof needed |
| T30 | Responsive mobile dashboard | Navigation and content fit | Manual browser proof needed |
| T31 | Cloud PostgreSQL connection | API reads/writes cloud DB | Requires your cloud credentials; not run |
| T32 | S3-compatible object write/read | Private uploaded bytes persist | Requires bucket credentials; not run |
| T33 | Production startup without JWT secret | Startup fails clearly | Implemented; dedicated test not recorded |
| T34 | CI workflow | Build/lint/API tests execute | Configure via GitHub push; not run by this workspace |

Do not mark manual/cloud cases as passed until you perform and record them. Capture output with synthetic data only.

## Security, scale, limitations, future work

Current protections include salted password hashes, expiring signed tokens, input validation, user-scoped data queries, image signature/size checks, exact configurable CORS, and server-side secrets. Before real public users: rate-limit sensitive routes, adopt mature identity/OIDC, add recovery/verification, token revocation, migrations, structured redacted logs, malware scanning, database/object backups, restore testing, monitoring/alerts, HTTPS validation, and load tests.

At 10 users a single API with small managed database is enough. At 1,000, add API replicas behind a load balancer, connection pooling, indexes, CDN for static assets, and request limits. At 100,000, measure and add autoscaling, partitioning/read replicas, queue-based long AI/image tasks, caching, lifecycle policies, tracing, multi-zone recovery, and explicit provider quotas/cost controls. These are architecture plans, not test results.

Limitations: small illustrative catalog; no daily intake tracker, progress dashboard analytics, coach role, food database sync, clinical checks, recipe nutrition verification, Firebase implementation, live cloud deployment, automatic backups, or monitoring dashboard. Future work can add those as separate tested features. Advantages today: no-cost local execution, clean client/API/data/storage boundaries, persisted account data, safe demo scoping, documented API and repeatable tests.

## Screenshot and GitHub proof checklist

Capture genuine images after running the app; use the project `screenshots/` directory. The directory README lists filenames and privacy requirements. Recommended evidence: `01-dashboard-desktop.png`, `02-dashboard-mobile.png`, `03-account-register.png`, `04-profile-preferences.png`, `05-generated-plan.png`, `06-saved-plans.png`, `07-private-file-library.png`, `08-api-openapi-docs.png`, `09-test-results.png`, `10-deployed-app.png` (only after deployment). A screenshot proves only what is visible in it; pair cloud claims with sanitized console/API configuration and avoid exposing tokens or secrets.

For authentic development history, commit in real stages as you implement: repository/docs; responsive frontend; API/database; authentication/isolation; rules engine; object storage; integration tests; deployment configuration; final report. Use truthful commit messages and dates; do not backdate or fabricate development history. Example messages: `Add FastAPI account and profile routes`, `Add owner-scoped plan persistence`, `Add private image storage adapter`, `Document cloud deployment architecture`.

## Resume and LinkedIn wording

**Two-line project description:** Built a React and FastAPI personal wellness planner with account authentication, user-isolated saved plans, and private image uploads. Added SQLite/PostgreSQL and local/S3 storage adapters plus a diet/allergy-aware rules engine with optional validated AI fallback.

**Resume bullets:**

- Developed REST endpoints for accounts, profiles, saved plans, and file uploads using FastAPI, SQLAlchemy, schema validation, and owner-scoped queries.
- Implemented a local-first meal suggestion engine with dietary/allergy filters and an optional AI-provider integration that falls back on provider errors or invalid responses.
- Added integration tests for authentication, user isolation, plan persistence, uploads, and fallback behavior; documented container/cloud deployment configuration.

**LinkedIn description:** Goodplate is a cloud-computing course project exploring how a web client, API, authentication, relational persistence, object storage, and a recommendation service fit together. The demo runs locally without cloud credentials and can be configured for PostgreSQL and S3-compatible storage. Its generated meal examples are for general wellness education only, not medical advice.

**Skills demonstrated:** React, JavaScript, Vite, Python, FastAPI, REST, Pydantic, SQLAlchemy, SQLite, PostgreSQL configuration, object-storage adapters, token authentication, input validation, testing, GitHub Actions, Docker, CORS, cloud architecture, technical documentation.

## Interview questions and sample answers

1. **Explain your project.** Goodplate is a React and FastAPI demo that lets synthetic users maintain meal preferences, generate general wellness meal examples, save plans, and privately upload meal images. SQLite and local files make it runnable offline; the adapters can use PostgreSQL and S3-compatible storage when deployed.
2. **Which cloud concepts does it demonstrate?** The hosted model separates static web hosting, API compute, managed structured data, and object storage. It also demonstrates environment configuration, authentication, CI, and stateless API scaling concepts. Local execution simulates those service boundaries, not cloud availability.
3. **Why separate the database from object storage?** Profiles and plan metadata are structured records that need indexed queries and relationships. Images are large binary objects, so the database stores metadata and an object key while local disk or a bucket stores the bytes.
4. **How do you prevent one user from reading another user's plans?** The API verifies an expiring bearer token, gets the subject user ID from its signed payload, then scopes each plan/file query by both record ID and owner ID. Integration tests verify cross-account reads/deletes return not found.
5. **What happens if the AI API is offline?** The app works without AI credentials. When enabled, the API sends only selected preference fields, checks the response shape and diet/allergy terms, and uses the local deterministic rules engine if the request fails or output is rejected.
6. **How is authentication implemented and what remains?** Passwords use PBKDF2-HMAC-SHA256 with unique salts; the API issues signed, expiring tokens. Browser logout removes its token but cannot revoke a copied stateless token, so production should use managed OIDC or add revocation and refresh-token rotation.
7. **How would you scale to more users?** Run stateless API replicas behind a load balancer, use managed PostgreSQL with pooling/indexes, keep files in object storage, and serve static assets via CDN. Queue slow AI/image jobs and add caching only after measuring the bottleneck.
8. **What security controls are present?** Input schemas, salted password hashes, signed expiring tokens, user-scoped queries, image content/size validation, exact configurable CORS, private object keys, and server-only secrets. Rate limiting, managed identity, backups, and richer monitoring remain deployment work.
9. **How would you deploy it?** Publish the Vite build to a static host, containerize FastAPI, configure a managed PostgreSQL URL and private S3-compatible bucket, set a generated JWT secret and exact frontend CORS origin, then verify health and isolation with synthetic accounts.
10. **What are the project limitations?** It has a small illustrative meal catalog and no verified nutrient database, intake tracker, clinical validation, mature identity provider, or live deployment. I describe its output as general education and would not use it as healthcare or allergy-safety software.

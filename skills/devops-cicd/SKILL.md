---
name: devops-cicd
description: Ship code reliably with CI/CD pipelines, trunk-based development, semantic versioning, reproducible builds, containers, blue-green and canary deploys, and infrastructure as code. Use when the user wants to build or review a deployment pipeline, automate tests and builds, containerize an application, manage infrastructure as code, set up GitHub Actions workflows, or choose a release strategy. Trigger on "CI/CD", "pipeline", "GitHub Actions", "Docker", "Kubernetes", "Terraform", "deploy", "blue-green", "canary", "semantic versioning", "trunk-based", "infrastructure as code", "container", "reproducible build", "release strategy". Pairs with cloud-deployment (which owns the target environment and IAM) and security-engineering (which owns secrets and supply-chain scanning). Honest: Cambium writes pipelines and configs the human reviews and runs; it does not push to production or hold cloud credentials.
---

# CI/CD and DevOps: ship code reliably, not heroically

The goal is a boring, repeatable pipeline. If a deploy requires a person to babysit a terminal, it is not
a pipeline yet. Pick the simplest tool that covers the job, encode it in version-controlled config, and
prove it works with automated tests before anything reaches production.

Popularity is a signal, not a reason: the tools below are recommended because they are mature,
well-documented, and widely supported, not because they are new. Encode durable patterns, not fast-moving
library calls. Cambium writes the config; the human reviews and runs it.

## Choose the right tool for each layer

| Layer | Default choice | When to consider alternatives |
|---|---|---|
| CI runner | GitHub Actions | GitLab CI if already on GitLab; Jenkins for complex legacy enterprise requirements |
| Container build | Docker with BuildKit | Podman for rootless builds; Nix for truly hermetic builds |
| Orchestration | Kubernetes (k8s) for scale; Docker Compose for local and small deploys | ECS or Cloud Run if you want managed k8s without the control plane overhead |
| Infrastructure as code | Terraform (HashiCorp, ~42 k GitHub stars) | Pulumi if the team prefers real programming languages; CDK for AWS-only stacks |
| Container registry | GitHub Container Registry (ghcr.io) | AWS ECR, GCR, or Docker Hub depending on cloud vendor |

## Trunk-based development: the branching strategy that ships fast

One main branch, always green, always deployable. Feature branches live for hours or a day or two, not
weeks. Feature flags gate work in progress from users. Long-lived branches are a sign something else is
broken (slow tests, fear of main, no flags).

```
main  ---------o----------o----------o----------o  (every commit deployable)
                \         /
                 feature  (short-lived, < 2 days)
```

## Semantic versioning: make the contract explicit

Use `MAJOR.MINOR.PATCH` (semver.org). Automate it: Conventional Commits plus a tool like
`semantic-release` or `release-please` derive the version number and changelog from commit messages,
removing the human decision from every release.

```yaml
# .github/workflows/release.yml (example, review before use)
on:
  push:
    branches: [main]
jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }
      - uses: google-github-actions/release-please-action@v4
        with:
          release-type: node
```

## Reproducible builds: the same inputs must produce the same output

Pin every dependency version. Use a lockfile (`package-lock.json`, `poetry.lock`, `go.sum`). Set a fixed
build date or use SOURCE_DATE_EPOCH for binaries. Record the exact tool versions (language runtime,
compiler) in the CI config, not just "latest". Use multi-stage Dockerfiles so the build environment
never bleeds into the runtime image.

```dockerfile
# Multi-stage: build stage never ships to production
FROM python:3.12.4-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.12.4-slim AS runtime
WORKDIR /app
# Note: the site-packages path below is version-specific (python3.12); update it to match
# the Python version used in your base image if you change the FROM tag above.
COPY --from=builder /usr/local/lib/python3.12 /usr/local/lib/python3.12
COPY src/ .
CMD ["python", "main.py"]
```

## Pipeline stages: the standard gate sequence

A pipeline that skips any stage is guessing, not shipping:

1. **Lint and format** (seconds): block on style errors; auto-format in CI.
2. **Unit tests** (under 5 minutes): no network, no disk, deterministic.
3. **Build and scan** (under 10 minutes): produce the artifact, run Semgrep or Trivy on the image.
4. **Integration tests** (under 15 minutes): hit real dependencies in ephemeral containers.
5. **Deploy to staging** (automatic on main merge).
6. **Smoke tests on staging** (automatic, blocks prod gate).
7. **Deploy to production** (blue-green or canary, human approval or automatic on green smoke).

## Release strategies: blue-green and canary

**Blue-green:** two identical environments, only one live. Switch traffic at the load balancer; rollback
is a one-line config change, not a redeploy.

**Canary:** route a small percentage of traffic (say 5%) to the new version, watch error rates and
latency, then gradually increase. Kubernetes and AWS CodeDeploy both support this natively.

Use blue-green for low-traffic services where simplicity matters. Use canary for high-traffic services
where a bad deploy would be noticed by users immediately.

## Infrastructure as code: never click in a console

Every resource is a Terraform (or Pulumi) file, committed to version control, reviewed before apply,
and state stored remotely (Terraform Cloud, S3 with DynamoDB lock). Drift between the code and the
real environment is treated as a bug.

```hcl
# example Terraform block; the human runs `terraform apply`, not Cambium
terraform {
  required_version = ">= 1.9.0"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.0" }
  }
  backend "s3" {
    bucket         = "my-tfstate"
    key            = "prod/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "tf-lock"
  }
}
```

## Honest guardrails

- Cambium writes configs and pipelines. The human reviews them and runs them. Cambium does not push to
  production, does not hold cloud credentials, and does not trigger workflows on the user's behalf.
- Never hardcode secrets in a pipeline file. Use the CI platform's secrets store and pass them as
  environment variables. See security-engineering for secrets management patterns.
- Infrastructure state files often contain sensitive values. Encrypt remote state and restrict access.
- Kubernetes adds significant operational overhead. Docker Compose or a managed platform (Cloud Run,
  Fly.io, Render) is the right answer for small teams and early-stage products.
- Fast-moving areas to version-pin carefully: GitHub Actions runner images (`ubuntu-latest` shifts),
  Terraform provider versions, and Kubernetes API deprecations between minor releases.

## Attribution and sources

Patterns encoded from public standards and documentation, nothing invented here. GitHub Actions
(docs.github.com/en/actions), Docker BuildKit (docs.docker.com/build/buildkit), Kubernetes
(kubernetes.io/docs), Terraform (developer.hashicorp.com/terraform), Conventional Commits
(conventionalcommits.org), Semantic Versioning (semver.org), release-please
(github.com/googleapis/release-please), Semgrep (semgrep.dev), Trivy (aquasecurity.github.io/trivy),
Trunk-based Development (trunkbaseddevelopment.com), SOURCE_DATE_EPOCH
(reproducible-builds.org/docs/source-date-epoch).

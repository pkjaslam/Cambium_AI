---
name: cloud-deployment
description: Run applications in the cloud correctly: IAM and least privilege, networking basics, object storage, serverless vs containers vs VMs, choosing a deploy target, and infrastructure as code with Terraform or Pulumi. Use when the user wants to deploy an application to AWS, GCP, or Azure, design cloud architecture, set up IAM roles and policies, choose between Lambda and containers and VMs, configure a VPC or network, or manage object storage. Trigger on "cloud", "AWS", "GCP", "Azure", "deploy to cloud", "IAM", "least privilege", "VPC", "Lambda", "serverless", "S3", "Terraform", "Pulumi", "cloud architecture", "ECS", "Cloud Run", "EC2". Pairs with devops-cicd (which owns the pipeline that delivers to cloud) and security-engineering (which owns secrets and supply-chain). Honest: Cambium gives architecture and config advice only; the human owns the account, the credentials, and the spend. Cambium never provisions or deploys on the user's behalf.
---

# Cloud deployment: architecture first, credentials never

The cloud is infrastructure you rent. Getting it right means designing for least privilege before
anything else, keeping the blast radius of any mistake small, and encoding every resource in version-
controlled infrastructure as code so nothing exists that you cannot see, review, or destroy.

Cambium advises and generates config. The human owns the account, runs the commands, and pays the bill.
Pick the simplest compute option that fits the workload. Popularity is a signal, not a reason.

## IAM and least privilege: the highest-risk area

Misconfigured IAM is consistently cited as a primary cause of cloud breaches. Treat every permission
grant as a permanent decision until reviewed. Start from zero permissions and add only what is proven
necessary.

| Pattern | What it means in practice |
|---|---|
| Least privilege | Grant only the specific actions on the specific resources a principal needs, nothing more. |
| No long-lived user credentials | Use roles and instance profiles, not access keys checked into code. |
| Separate environments | Dev, staging, and prod are separate accounts or projects, not separate folders in one account. |
| MFA on root and admin humans | Non-negotiable. Automate enforcement with a Service Control Policy (SCP) or Org policy. |
| Rotate and audit | Enable CloudTrail (AWS) or Cloud Audit Logs (GCP). Review unused permissions quarterly. |

```json
// Minimal S3 read policy: one bucket, one prefix, no write (review before use)
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": ["s3:GetObject"],
    "Resource": "arn:aws:s3:::my-bucket/data/*"
  }]
}
```

## Choose the right compute target

| Workload | Best fit | Avoid |
|---|---|---|
| Event-driven, short tasks (under 15 min) | Serverless: AWS Lambda, GCP Cloud Functions, Azure Functions | Over-engineering with k8s for a function that runs 10 times a day |
| Stateless HTTP services, teams that know containers | Managed containers: Cloud Run, ECS Fargate, Azure Container Apps | Managing your own EC2 fleet when a managed service exists |
| Stateful services, databases, GPU workloads | VMs: EC2, GCE, Azure VM | Serverless (no persistent local disk) |
| Microservices at scale with dedicated platform team | Kubernetes: GKE, EKS, AKS | Kubernetes for small teams without a dedicated operator |

The default path for a new web service: Cloud Run (GCP) or ECS Fargate (AWS), because the control plane
is managed and you pay per request in low-traffic periods. Add Kubernetes only when you have the load
and the operational capacity to justify it.

## Networking basics: keep the surface area small

- Put compute in a private subnet. Only the load balancer lives in the public subnet.
- Use security groups or firewall rules to allow only the ports the service actually needs.
- Enable VPC flow logs and set up anomaly alerts.
- Prefer VPC peering or Private Link over exposing services to the public internet.
- HTTPS everywhere. Use a managed certificate (ACM, GCP-managed certs) with auto-renewal.

```hcl
# Minimal Terraform security group: inbound 443 only (review before use)
resource "aws_security_group" "web" {
  name   = "web-sg"
  vpc_id = var.vpc_id

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
```

## Object storage

S3 (AWS), GCS (GCP), and Azure Blob Storage all follow the same model: buckets are private by default
and must stay that way unless a specific use case requires public access. Block public access at the
account level, not just the bucket level. Enable versioning for anything that matters. Set lifecycle
policies to delete or archive old objects rather than accruing cost forever.

## Infrastructure as code: the only acceptable way to manage cloud resources

Every resource is a Terraform or Pulumi file, reviewed as a pull request, applied by the human.
Remote state is stored in a locked backend (S3 plus DynamoDB, or Terraform Cloud). Drift between code
and reality is a bug.

For multi-cloud or for teams that prefer typed languages, Pulumi (pulumi.com) supports Python,
TypeScript, and Go against the same provider APIs as Terraform. The pattern is the same: plan, review,
apply, never click.

## Spending: it will surprise you

Cloud cost surprises are common and fast. Set budget alerts on day one (AWS Budgets, GCP Budgets).
Tag every resource with project and environment so costs are attributable. Data transfer costs are
often larger than compute costs; keep compute and storage in the same region, and audit egress monthly.

## Honest guardrails

- Cambium gives architecture and config advice only. The human owns the cloud account, the credentials,
  and the spend. Cambium never provisions resources, never calls a cloud API, and never holds
  access keys or service account credentials.
- IAM mistakes are often silent until they are not. Test least-privilege policies with the AWS IAM
  policy simulator or `gcloud iam list-testable-permissions` before applying.
- "Free tier" can become a large bill. Understand the pricing model for every service you enable.
- Managed services add vendor lock-in. That tradeoff is often worth it for small teams, but name it.
- Fast-moving areas to watch: serverless pricing models change, managed k8s minor versions deprecate
  APIs, and provider Terraform modules move fast. Pin provider and module versions explicitly.

## Attribution and sources

Guidance encoded from public documentation and standards, nothing invented. AWS IAM best practices
(docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html), AWS Well-Architected Framework
(aws.amazon.com/architecture/well-architected), GCP Architecture Framework
(cloud.google.com/architecture/framework), Azure Well-Architected (learn.microsoft.com/azure/
well-architected), Terraform (developer.hashicorp.com/terraform), Pulumi (pulumi.com/docs),
Cloud Run (cloud.google.com/run/docs), ECS Fargate (docs.aws.amazon.com/AmazonECS), Kubernetes
(kubernetes.io/docs), VPC networking (docs.aws.amazon.com/vpc), S3 security
(docs.aws.amazon.com/AmazonS3/latest/userguide/security-best-practices.html).

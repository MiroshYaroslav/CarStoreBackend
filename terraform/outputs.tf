output "alb_dns_name" {
  description = "Public DNS name of the application load balancer."
  value       = aws_lb.main.dns_name
}

output "ecr_repository_url" {
  description = "URL of the application ECR repository."
  value       = aws_ecr_repository.app.repository_url
}

output "github_actions_role_arn" {
  description = "IAM role ARN to configure as the GitHub Actions AWS role."
  value       = aws_iam_role.github_actions.arn
}

resource "aws_ecs_cluster" "main" {
  name = "${local.name}-cluster"
  setting {
    name  = "containerInsights"
    value = "enabled"
  }
  tags = { Name = "${local.name}-cluster" }
}

resource "aws_iam_role" "ecs_task_execution" {
  name = "${local.name}-ecs-execution"
  assume_role_policy = jsonencode({
    Version   = "2012-10-17"
    Statement = [{ Effect = "Allow", Principal = { Service = "ecs-tasks.amazonaws.com" }, Action = "sts:AssumeRole" }]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution" {
  role       = aws_iam_role.ecs_task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_secretsmanager_secret" "db_password" {
  name                    = "${local.name}/postgres-password"
  recovery_window_in_days = 0
}

resource "aws_secretsmanager_secret_version" "db_password" {
  secret_id     = aws_secretsmanager_secret.db_password.id
  secret_string = var.db_password
}

resource "aws_secretsmanager_secret" "app_secret_key" {
  name                    = "${local.name}/app-secret-key"
  recovery_window_in_days = 0
}

resource "aws_secretsmanager_secret_version" "app_secret_key" {
  secret_id     = aws_secretsmanager_secret.app_secret_key.id
  secret_string = var.app_secret_key
}

resource "aws_iam_role_policy" "ecs_read_app_secrets" {
  name = "${local.name}-read-app-secrets"
  role = aws_iam_role.ecs_task_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = ["secretsmanager:GetSecretValue"]
      Resource = [
        aws_secretsmanager_secret.db_password.arn,
        aws_secretsmanager_secret.app_secret_key.arn
      ]
    }]
  })
}

resource "aws_ecs_task_definition" "app" {
  family                   = "${local.name}-app"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.ecs_cpu
  memory                   = var.ecs_memory
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([{
    name         = "bmw-catalog"
    image        = "${aws_ecr_repository.app.repository_url}:${var.app_image_tag}"
    essential    = true
    portMappings = [{ containerPort = 8000, hostPort = 8000, protocol = "tcp" }]
    environment = [
      { name = "ENVIRONMENT", value = var.environment },
      { name = "POSTGRES_USER", value = var.db_username },
      { name = "POSTGRES_DB", value = aws_db_instance.main.db_name },
      { name = "POSTGRES_HOST", value = aws_db_instance.main.address },
      { name = "POSTGRES_PORT", value = "5432" },
      { name = "CORS_ORIGINS", value = jsonencode(["https://auto-catalog.app", "https://auto-catalog-blue.vercel.app"]) },
      { name = "AWS_REGION", value = var.aws_region },
      { name = "AWS_BUCKET_NAME", value = aws_s3_bucket.product_images.id },
      { name = "AWS_CLOUDFRONT_DOMAIN", value = aws_cloudfront_distribution.product_images.domain_name },
      { name = "PRODUCT_IMAGE_UPLOAD_ALLOWED_USER_IDS", value = jsonencode(var.product_image_upload_allowed_user_ids) }
    ]
    secrets = [
      { name = "SECRET_KEY", valueFrom = aws_secretsmanager_secret.app_secret_key.arn },
      { name = "POSTGRES_PASSWORD", valueFrom = aws_secretsmanager_secret.db_password.arn }
    ]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.app.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "ecs"
      }
    }
  }])
  depends_on = [
    aws_iam_role_policy_attachment.ecs_task_execution,
    aws_iam_role_policy.ecs_read_app_secrets
  ]
  tags = { Name = "${local.name}-app-task" }

  lifecycle {
    create_before_destroy = true
  }
}

data "aws_ecs_task_definition" "active" {
  task_definition = aws_ecs_task_definition.app.family
  depends_on      = [aws_ecs_task_definition.app]
}

resource "aws_ecs_service" "app" {
  name            = "${local.name}-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = data.aws_ecs_task_definition.active.arn
  desired_count   = var.ecs_desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.private[*].id
    security_groups  = [aws_security_group.ecs.id]
    assign_public_ip = false
  }
  load_balancer {
    target_group_arn = aws_lb_target_group.app.arn
    container_name   = "bmw-catalog"
    container_port   = 8000
  }
  depends_on = [aws_lb_listener.http, aws_nat_gateway.main]
  tags       = { Name = "${local.name}-service" }
}

resource "aws_cloudwatch_log_group" "app" {
  name              = "/ecs/${local.name}"
  retention_in_days = 30
  tags              = { Name = "${local.name}-logs" }
}

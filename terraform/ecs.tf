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

  container_definitions = jsonencode([
    {
      name         = "bmw-catalog"
      image        = "${aws_ecr_repository.app.repository_url}:${var.app_image_tag}"
      essential    = true
      portMappings = [{ containerPort = 8000, hostPort = 8000, protocol = "tcp" }]

      dependsOn = [
        {
          containerName = "redis-cache"
          condition     = "START"
        }
      ]

      environment = [
        { name = "ENVIRONMENT", value = var.environment },
        { name = "POSTGRES_USER", value = var.db_username },
        { name = "POSTGRES_DB", value = aws_db_instance.main.db_name },
        { name = "POSTGRES_HOST", value = aws_db_instance.main.address },
        { name = "POSTGRES_PORT", value = "5432" },
        { name = "REDIS_URL", value = "redis://127.0.0.1:6379/0" },
        { name = "CACHE_ENABLED", value = tostring(var.cache_enabled) },
        { name = "CORS_ORIGINS", value = jsonencode(["https://auto-catalog.app", "https://auto-catalog-blue.vercel.app"]) },
        { name = "AWS_REGION", value = var.aws_region },
        { name = "AWS_BUCKET_NAME", value = aws_s3_bucket.product_images.id },
        { name = "AWS_CLOUDFRONT_DOMAIN", value = aws_cloudfront_distribution.product_images.domain_name },
        { name = "PRODUCT_IMAGE_UPLOAD_ALLOWED_USER_IDS", value = jsonencode(var.product_image_upload_allowed_user_ids) },
        { name = "SQS_QUEUE_URL", value = aws_sqs_queue.task_queue.id }
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
    },
    {
      name         = "redis-cache"
      image        = "redis:7-alpine"
      command      = ["redis-server", "--maxmemory", "256mb", "--maxmemory-policy", "allkeys-lru", "--save", ""]
      essential    = true
      portMappings = [{ containerPort = 6379, hostPort = 6379, protocol = "tcp" }]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.app.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "redis"
        }
      }
    }
  ])

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
  desired_count   = var.ecs_min_capacity
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

  lifecycle {
    ignore_changes = [desired_count]
  }
}

resource "aws_cloudwatch_log_group" "app" {
  name              = "/ecs/${local.name}"
  retention_in_days = 30
  tags              = { Name = "${local.name}-logs" }
}

resource "aws_appautoscaling_target" "ecs_target" {
  max_capacity       = var.ecs_max_capacity
  min_capacity       = var.ecs_min_capacity
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.app.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "ecs_cpu_policy" {
  name               = "${local.name}-cpu-autoscaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs_target.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_target.scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs_target.service_namespace

  target_tracking_scaling_policy_configuration {
    target_value       = 60.0
    scale_in_cooldown  = 300
    scale_out_cooldown = 60

    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
  }
}

resource "aws_appautoscaling_scheduled_action" "day_scale" {
  name               = "${local.name}-day-scale"
  service_namespace  = aws_appautoscaling_target.ecs_target.service_namespace
  resource_id        = aws_appautoscaling_target.ecs_target.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_target.scalable_dimension
  schedule           = "cron(0 8 * * ? *)"

  scalable_target_action {
    min_capacity = 2
    max_capacity = 4
  }
}

resource "aws_appautoscaling_scheduled_action" "night_scale" {
  name               = "${local.name}-night-scale"
  service_namespace  = aws_appautoscaling_target.ecs_target.service_namespace
  resource_id        = aws_appautoscaling_target.ecs_target.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_target.scalable_dimension
  schedule           = "cron(0 20 * * ? *)"

  scalable_target_action {
    min_capacity = 1
    max_capacity = 2
  }
}

resource "aws_ecs_task_definition" "worker" {
  family                   = "${local.name}-worker"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 256
  memory                   = 512
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = "bmw-catalog-worker"
      image     = "${aws_ecr_repository.app.repository_url}:${var.app_image_tag}"
      essential = true
      # Перевір, щоб шлях відповідав розташуванню файлу воркера у твоєму проєкті
      command   = ["python", "-m", "app.worker"]

      environment = [
        { name = "ENVIRONMENT", value = var.environment },
        { name = "POSTGRES_USER", value = var.db_username },
        { name = "POSTGRES_DB", value = aws_db_instance.main.db_name },
        { name = "POSTGRES_HOST", value = aws_db_instance.main.address },
        { name = "POSTGRES_PORT", value = "5432" },
        { name = "AWS_REGION", value = var.aws_region },
        { name = "SQS_QUEUE_URL", value = aws_sqs_queue.task_queue.id }
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
          "awslogs-stream-prefix" = "worker"
        }
      }
    }
  ])

  depends_on = [
    aws_iam_role_policy_attachment.ecs_task_execution,
    aws_iam_role_policy.ecs_read_app_secrets
  ]
  tags = { Name = "${local.name}-worker-task" }
}

resource "aws_ecs_service" "worker" {
  name            = "${local.name}-worker-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.worker.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.private[*].id
    security_groups  = [aws_security_group.ecs.id]
    assign_public_ip = false
  }

  depends_on = [aws_nat_gateway.main]
  tags       = { Name = "${local.name}-worker-service" }

  lifecycle {
    ignore_changes = [desired_count]
  }
}

resource "aws_appautoscaling_target" "worker_target" {
  max_capacity       = 3
  min_capacity       = 1
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.worker.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "worker_sqs_policy" {
  name               = "${local.name}-worker-sqs-autoscaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.worker_target.resource_id
  scalable_dimension = aws_appautoscaling_target.worker_target.scalable_dimension
  service_namespace  = aws_appautoscaling_target.worker_target.service_namespace

  target_tracking_scaling_policy_configuration {
    target_value       = 10.0
    scale_in_cooldown  = 300
    scale_out_cooldown = 60

    customized_metric_specification {
      metric_name = "ApproximateNumberOfMessagesVisible"
      namespace   = "AWS/SQS"
      statistic   = "Average"

      dimensions {
        name  = "QueueName"
        value = aws_sqs_queue.task_queue.name
      }
    }
  }
}
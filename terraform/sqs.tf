resource "aws_sqs_queue" "task_queue" {
  name                       = "${local.name}-task-queue"
  visibility_timeout_seconds = 300
  message_retention_seconds  = 86400 # 24 години
  tags                       = { Name = "${local.name}-task-queue" }
}

resource "aws_iam_role_policy" "ecs_sqs_access" {
  name = "${local.name}-sqs-access"
  role = aws_iam_role.ecs_task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "sqs:SendMessage",
        "sqs:ReceiveMessage",
        "sqs:DeleteMessage",
        "sqs:GetQueueAttributes"
      ]
      Resource = aws_sqs_queue.task_queue.arn
    }]
  })
}

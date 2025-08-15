# AWS Cost Optimization and Budget Monitoring Configuration
# This module implements comprehensive cost monitoring and optimization strategies
# to keep infrastructure costs under $2K/month while maintaining performance

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Local values for cost optimization
locals {
  monthly_budget_limit = 2000  # $2,000 USD
  warning_threshold = 0.8      # 80% of budget
  critical_threshold = 0.95    # 95% of budget
  
  # Cost allocation tags
  cost_tags = {
    Project = "socialmapper"
    Environment = var.environment
    CostCenter = "engineering"
    Application = "demo-platform"
  }
}

# AWS Budgets for cost monitoring
resource "aws_budgets_budget" "socialmapper_monthly" {
  name         = "${var.environment}-socialmapper-monthly-budget"
  budget_type  = "COST"
  limit_amount = local.monthly_budget_limit
  limit_unit   = "USD"
  time_unit    = "MONTHLY"
  
  time_period_start = formatdate("YYYY-MM-DD_00:00", timestamp())
  
  cost_filters {
    tag {
      key = "Project"
      values = ["socialmapper"]
    }
  }
  
  # Budget notifications
  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                 = local.warning_threshold * 100
    threshold_type            = "PERCENTAGE"
    notification_type         = "ACTUAL"
    subscriber_email_addresses = [var.budget_notification_email]
  }
  
  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                 = local.critical_threshold * 100
    threshold_type            = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = [var.budget_notification_email]
  }
  
  # Forecasted budget alerts
  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                 = local.warning_threshold * 100
    threshold_type            = "PERCENTAGE"
    notification_type         = "FORECASTED"
    subscriber_email_addresses = [var.budget_notification_email]
  }
}

# Service-specific budgets
resource "aws_budgets_budget" "eks_compute_budget" {
  name         = "${var.environment}-socialmapper-eks-budget"
  budget_type  = "COST"
  limit_amount = local.monthly_budget_limit * 0.6  # 60% for EKS compute
  limit_unit   = "USD"
  time_unit    = "MONTHLY"
  
  time_period_start = formatdate("YYYY-MM-DD_00:00", timestamp())
  
  cost_filters {
    service = ["Amazon Elastic Compute Cloud - Compute", "Amazon Elastic Kubernetes Service"]
    tag {
      key = "Project"
      values = ["socialmapper"]
    }
  }
  
  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                 = 80
    threshold_type            = "PERCENTAGE"
    notification_type         = "ACTUAL"
    subscriber_email_addresses = [var.budget_notification_email]
  }
}

resource "aws_budgets_budget" "storage_budget" {
  name         = "${var.environment}-socialmapper-storage-budget"
  budget_type  = "COST"
  limit_amount = local.monthly_budget_limit * 0.15  # 15% for storage
  limit_unit   = "USD"
  time_unit    = "MONTHLY"
  
  time_period_start = formatdate("YYYY-MM-DD_00:00", timestamp())
  
  cost_filters {
    service = [
      "Amazon Simple Storage Service",
      "Amazon Elastic Block Store",
      "Amazon Elastic File System"
    ]
    tag {
      key = "Project"
      values = ["socialmapper"]
    }
  }
  
  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                 = 80
    threshold_type            = "PERCENTAGE"
    notification_type         = "ACTUAL"
    subscriber_email_addresses = [var.budget_notification_email]
  }
}

resource "aws_budgets_budget" "data_transfer_budget" {
  name         = "${var.environment}-socialmapper-data-transfer-budget"
  budget_type  = "COST"
  limit_amount = local.monthly_budget_limit * 0.1  # 10% for data transfer
  limit_unit   = "USD"
  time_unit    = "MONTHLY"
  
  time_period_start = formatdate("YYYY-MM-DD_00:00", timestamp())
  
  cost_filters {
    service = [
      "Amazon CloudFront",
      "AWS Data Transfer"
    ]
    tag {
      key = "Project"
      values = ["socialmapper"]
    }
  }
  
  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                 = 80
    threshold_type            = "PERCENTAGE"
    notification_type         = "ACTUAL"
    subscriber_email_addresses = [var.budget_notification_email]
  }
}

# Cost anomaly detection
resource "aws_ce_anomaly_detector" "socialmapper_anomaly_detector" {
  name         = "${var.environment}-socialmapper-anomaly-detector"
  monitor_type = "DIMENSIONAL"

  specification {
    dimension {
      key           = "SERVICE"
      values        = ["EC2-Instance", "Amazon Elastic Kubernetes Service", "Amazon Relational Database Service"]
      match_options = ["EQUALS"]
    }
  }

  tags = local.cost_tags
}

resource "aws_ce_anomaly_subscription" "socialmapper_anomaly_subscription" {
  name      = "${var.environment}-socialmapper-anomaly-subscription"
  frequency = "DAILY"
  
  monitor_arn_list = [
    aws_ce_anomaly_detector.socialmapper_anomaly_detector.arn,
  ]
  
  subscriber {
    type    = "EMAIL"
    address = var.budget_notification_email
  }

  threshold_expression {
    and {
      dimension {
        key           = "ANOMALY_TOTAL_IMPACT_ABSOLUTE"
        values        = ["100"]
        match_options = ["GREATER_THAN_OR_EQUAL"]
      }
    }
  }
}

# Lambda function for automated cost optimization
resource "aws_iam_role" "cost_optimizer_role" {
  name = "${var.environment}-socialmapper-cost-optimizer-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = local.cost_tags
}

resource "aws_iam_role_policy" "cost_optimizer_policy" {
  name = "${var.environment}-socialmapper-cost-optimizer-policy"
  role = aws_iam_role.cost_optimizer_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "ec2:DescribeInstances",
          "ec2:DescribeSpotInstanceRequests",
          "ec2:ModifyInstanceAttribute",
          "ec2:StopInstances",
          "eks:DescribeCluster",
          "eks:ListNodegroups",
          "eks:DescribeNodegroup",
          "autoscaling:DescribeAutoScalingGroups",
          "autoscaling:UpdateAutoScalingGroup",
          "ce:GetCostAndUsage",
          "ce:GetUsageReport",
          "rds:DescribeDBInstances",
          "rds:ModifyDBInstance",
          "elasticache:DescribeCacheClusters",
          "cloudwatch:PutMetricData"
        ]
        Resource = "*"
      }
    ]
  })
}

# Lambda function code for cost optimization
resource "aws_lambda_function" "cost_optimizer" {
  filename         = "cost_optimizer.zip"
  function_name    = "${var.environment}-socialmapper-cost-optimizer"
  role            = aws_iam_role.cost_optimizer_role.arn
  handler         = "cost_optimizer.lambda_handler"
  runtime         = "python3.9"
  timeout         = 300

  environment {
    variables = {
      ENVIRONMENT = var.environment
      PROJECT = "socialmapper"
      BUDGET_LIMIT = local.monthly_budget_limit
    }
  }

  tags = local.cost_tags

  depends_on = [
    aws_iam_role_policy.cost_optimizer_policy,
    aws_cloudwatch_log_group.cost_optimizer_logs,
  ]
}

# CloudWatch log group for Lambda function
resource "aws_cloudwatch_log_group" "cost_optimizer_logs" {
  name              = "/aws/lambda/${var.environment}-socialmapper-cost-optimizer"
  retention_in_days = 14
  
  tags = local.cost_tags
}

# EventBridge rule to trigger cost optimization daily
resource "aws_cloudwatch_event_rule" "cost_optimizer_schedule" {
  name                = "${var.environment}-socialmapper-cost-optimizer-schedule"
  description         = "Triggers cost optimization Lambda daily"
  schedule_expression = "rate(1 day)"
  
  tags = local.cost_tags
}

resource "aws_cloudwatch_event_target" "cost_optimizer_target" {
  rule      = aws_cloudwatch_event_rule.cost_optimizer_schedule.name
  target_id = "CostOptimizerTarget"
  arn       = aws_lambda_function.cost_optimizer.arn
}

resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.cost_optimizer.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.cost_optimizer_schedule.arn
}

# CloudWatch dashboard for cost monitoring
resource "aws_cloudwatch_dashboard" "cost_monitoring" {
  dashboard_name = "${var.environment}-SocialMapperCostMonitoring"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/Billing", "EstimatedCharges", "Currency", "USD"],
          ]
          view    = "timeSeries"
          stacked = false
          region  = "us-east-1"
          title   = "Estimated Monthly Charges"
          period  = 86400
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/EC2", "CPUUtilization", { "stat" = "Average" }],
            ["AWS/ApplicationELB", "RequestCount", { "stat" = "Sum" }],
          ]
          view   = "timeSeries"
          region = var.aws_region
          title  = "Resource Utilization"
          period = 300
        }
      }
    ]
  })
}

# SNS topic for cost alerts
resource "aws_sns_topic" "cost_alerts" {
  name = "${var.environment}-socialmapper-cost-alerts"
  
  tags = local.cost_tags
}

resource "aws_sns_topic_subscription" "cost_alerts_email" {
  topic_arn = aws_sns_topic.cost_alerts.arn
  protocol  = "email"
  endpoint  = var.budget_notification_email
}

# CloudWatch alarms for cost monitoring
resource "aws_cloudwatch_metric_alarm" "high_cost_alarm" {
  alarm_name          = "${var.environment}-socialmapper-high-cost"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "EstimatedCharges"
  namespace           = "AWS/Billing"
  period              = "86400"
  statistic           = "Maximum"
  threshold           = local.monthly_budget_limit * 0.9
  alarm_description   = "This metric monitors estimated charges"
  alarm_actions       = [aws_sns_topic.cost_alerts.arn]

  dimensions = {
    Currency = "USD"
  }

  tags = local.cost_tags
}

# Cost optimization recommendations
resource "aws_config_configuration_recorder" "cost_optimization" {
  name     = "${var.environment}-socialmapper-cost-recorder"
  role_arn = aws_iam_role.config_role.arn

  recording_group {
    all_supported                 = true
    include_global_resource_types = true
  }
  
  depends_on = [aws_config_delivery_channel.cost_optimization]
}

resource "aws_config_delivery_channel" "cost_optimization" {
  name           = "${var.environment}-socialmapper-cost-delivery"
  s3_bucket_name = aws_s3_bucket.config_bucket.bucket
}

resource "aws_s3_bucket" "config_bucket" {
  bucket        = "${var.environment}-socialmapper-config-${random_string.suffix.result}"
  force_destroy = !var.enable_deletion_protection
  
  tags = local.cost_tags
}

resource "aws_s3_bucket_public_access_block" "config_bucket" {
  bucket = aws_s3_bucket.config_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_iam_role" "config_role" {
  name = "${var.environment}-socialmapper-config-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "config.amazonaws.com"
        }
      }
    ]
  })

  tags = local.cost_tags
}

resource "aws_iam_role_policy_attachment" "config_role_policy" {
  role       = aws_iam_role.config_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWS_ConfigServiceRolePolicy"
}

# Variables for cost optimization module
variable "budget_notification_email" {
  description = "Email address for budget notifications"
  type        = string
  default     = "admin@socialmapper.com"
}

variable "enable_cost_optimization_lambda" {
  description = "Enable automated cost optimization Lambda function"
  type        = bool
  default     = true
}

variable "cost_optimization_schedule" {
  description = "Schedule for cost optimization checks"
  type        = string
  default     = "rate(1 day)"
}

# Random string for unique resource naming
resource "random_string" "suffix" {
  length  = 8
  special = false
  upper   = false
}

# Data source for AWS account ID
data "aws_caller_identity" "current" {}

# Outputs
output "monthly_budget_id" {
  description = "ID of the monthly budget"
  value       = aws_budgets_budget.socialmapper_monthly.id
}

output "cost_anomaly_detector_arn" {
  description = "ARN of the cost anomaly detector"
  value       = aws_ce_anomaly_detector.socialmapper_anomaly_detector.arn
}

output "cost_optimizer_function_name" {
  description = "Name of the cost optimizer Lambda function"
  value       = aws_lambda_function.cost_optimizer.function_name
}

output "cost_dashboard_url" {
  description = "URL of the cost monitoring dashboard"
  value       = "https://console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards:name=${aws_cloudwatch_dashboard.cost_monitoring.dashboard_name}"
}

# Tags for all resources
resource "null_resource" "apply_cost_tags" {
  triggers = {
    always_run = timestamp()
  }
  
  provisioner "local-exec" {
    command = <<-EOT
      echo "Cost optimization configuration applied with tags:"
      echo "Project: ${local.cost_tags.Project}"
      echo "Environment: ${local.cost_tags.Environment}"
      echo "CostCenter: ${local.cost_tags.CostCenter}"
      echo "Application: ${local.cost_tags.Application}"
      echo "Monthly Budget Limit: $${local.monthly_budget_limit}"
    EOT
  }
}
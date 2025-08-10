# Redis (ElastiCache) Configuration for Session Management

# ElastiCache Subnet Group
resource "aws_elasticache_subnet_group" "redis" {
  name       = "${local.name}-redis-subnet-group"
  subnet_ids = aws_subnet.private[*].id

  tags = local.common_tags
}

# ElastiCache Parameter Group
resource "aws_elasticache_parameter_group" "redis" {
  name   = "${local.name}-redis-params"
  family = "redis7.x"

  # Optimize for session storage
  parameter {
    name  = "maxmemory-policy"
    value = "allkeys-lru"
  }

  parameter {
    name  = "timeout"
    value = "300"
  }

  parameter {
    name  = "tcp-keepalive"
    value = "300"
  }

  tags = local.common_tags
}

# Security Group for Redis
resource "aws_security_group" "redis" {
  name_prefix = "${local.name}-redis-"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.eks_node_group.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "${local.name}-redis-sg"
  })
}

# ElastiCache Redis Cluster
resource "aws_elasticache_replication_group" "redis" {
  replication_group_id       = "${local.name}-redis"
  description                = "Redis cluster for SocialMapper session storage"
  
  node_type                  = var.redis_node_type
  port                       = 6379
  parameter_group_name       = aws_elasticache_parameter_group.redis.name
  subnet_group_name          = aws_elasticache_subnet_group.redis.name
  security_group_ids         = [aws_security_group.redis.id]
  
  num_cache_clusters         = var.redis_num_cache_nodes
  
  # Backup configuration
  automatic_failover_enabled = var.redis_num_cache_nodes > 1
  multi_az_enabled          = var.redis_num_cache_nodes > 1
  snapshot_retention_limit   = 3
  snapshot_window           = "03:00-05:00"
  maintenance_window        = "mon:05:00-mon:06:00"
  
  # Security
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  auth_token                = random_password.redis_auth_token.result
  
  # Logging
  log_delivery_configuration {
    destination      = aws_cloudwatch_log_group.redis.name
    destination_type = "cloudwatch-logs"
    log_format      = "text"
    log_type        = "slow-log"
  }

  tags = merge(local.common_tags, {
    Name = "${local.name}-redis"
  })
}

# Random password for Redis auth
resource "random_password" "redis_auth_token" {
  length  = 32
  special = true
}

# CloudWatch Log Group for Redis
resource "aws_cloudwatch_log_group" "redis" {
  name              = "/aws/elasticache/redis/${local.name}"
  retention_in_days = 7
  kms_key_id        = aws_kms_key.eks.arn

  tags = local.common_tags
}

# CloudWatch Alarms for Redis
resource "aws_cloudwatch_metric_alarm" "redis_cpu" {
  alarm_name          = "${local.name}-redis-cpu-utilization"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ElastiCache"
  period              = 300
  statistic           = "Average"
  threshold           = 75
  alarm_description   = "This metric monitors redis cpu utilization"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    CacheClusterId = aws_elasticache_replication_group.redis.id
  }

  tags = local.common_tags
}

resource "aws_cloudwatch_metric_alarm" "redis_memory" {
  alarm_name          = "${local.name}-redis-memory-utilization"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "DatabaseMemoryUsagePercentage"
  namespace           = "AWS/ElastiCache"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "This metric monitors redis memory utilization"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    CacheClusterId = aws_elasticache_replication_group.redis.id
  }

  tags = local.common_tags
}

# Store Redis connection info in Systems Manager
resource "aws_ssm_parameter" "redis_endpoint" {
  name  = "/${var.environment}/socialmapper/redis/endpoint"
  type  = "String"
  value = aws_elasticache_replication_group.redis.configuration_endpoint_address
  
  tags = local.common_tags
}

resource "aws_ssm_parameter" "redis_auth_token" {
  name  = "/${var.environment}/socialmapper/redis/auth-token"
  type  = "SecureString"
  value = random_password.redis_auth_token.result
  
  tags = local.common_tags
}
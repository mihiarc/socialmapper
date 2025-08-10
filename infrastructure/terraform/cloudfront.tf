# CloudFront CDN Configuration for Global Performance

# S3 bucket for static assets and logs
resource "aws_s3_bucket" "static_assets" {
  bucket        = "${local.name}-static-assets-${random_string.suffix.result}"
  force_destroy = !var.enable_deletion_protection

  tags = local.common_tags
}

resource "aws_s3_bucket_versioning" "static_assets" {
  bucket = aws_s3_bucket.static_assets.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "static_assets" {
  bucket = aws_s3_bucket.static_assets.bucket

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "static_assets" {
  bucket = aws_s3_bucket.static_assets.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Origin Access Identity for CloudFront
resource "aws_cloudfront_origin_access_identity" "main" {
  comment = "OAI for ${local.name}"
}

# S3 bucket policy for CloudFront access
resource "aws_s3_bucket_policy" "static_assets" {
  bucket = aws_s3_bucket.static_assets.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowCloudFrontAccess"
        Effect = "Allow"
        Principal = {
          AWS = aws_cloudfront_origin_access_identity.main.iam_arn
        }
        Action   = "s3:GetObject"
        Resource = "${aws_s3_bucket.static_assets.arn}/*"
      }
    ]
  })
}

# WAF Web ACL for CloudFront
resource "aws_wafv2_web_acl" "main" {
  name  = "${local.name}-waf"
  scope = "CLOUDFRONT"

  default_action {
    allow {}
  }

  # Rate limiting rule
  rule {
    name     = "RateLimitRule"
    priority = 1

    override_action {
      none {}
    }

    statement {
      rate_based_statement {
        limit              = 2000  # Requests per 5-minute period
        aggregate_key_type = "IP"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "RateLimitRule"
      sampled_requests_enabled   = true
    }

    action {
      block {}
    }
  }

  # Block known bad IPs
  rule {
    name     = "AWSManagedRulesKnownBadInputsRuleSet"
    priority = 2

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesKnownBadInputsRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "AWSManagedRulesKnownBadInputsRuleSet"
      sampled_requests_enabled   = true
    }
  }

  # SQL injection protection
  rule {
    name     = "AWSManagedRulesSQLiRuleSet"
    priority = 3

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesSQLiRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "AWSManagedRulesSQLiRuleSet"
      sampled_requests_enabled   = true
    }
  }

  # Common rule set
  rule {
    name     = "AWSManagedRulesCommonRuleSet"
    priority = 4

    override_action {
      count {}  # Count mode for common rules to avoid false positives
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesCommonRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "AWSManagedRulesCommonRuleSet"
      sampled_requests_enabled   = true
    }
  }

  tags = local.common_tags

  depends_on = [aws_cloudwatch_log_group.waf]
}

# CloudWatch Log Group for WAF
resource "aws_cloudwatch_log_group" "waf" {
  name              = "/aws/wafv2/webacl/${local.name}"
  retention_in_days = 30
  kms_key_id        = aws_kms_key.eks.arn

  tags = local.common_tags
}

# CloudFront Distribution
resource "aws_cloudfront_distribution" "main" {
  comment             = "SocialMapper Demo Platform CDN"
  default_root_object = "index.html"
  enabled             = true
  is_ipv6_enabled     = true
  price_class         = "PriceClass_All"  # Global distribution
  web_acl_id          = aws_wafv2_web_acl.main.arn

  # ALB Origin (for API and dynamic content)
  origin {
    domain_name = aws_lb.main.dns_name
    origin_id   = "ALB-${local.name}"

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }

    custom_header {
      name  = "X-Forwarded-Host"
      value = var.domain_name
    }
  }

  # S3 Origin (for static assets)
  origin {
    domain_name = aws_s3_bucket.static_assets.bucket_regional_domain_name
    origin_id   = "S3-${local.name}"

    s3_origin_config {
      origin_access_identity = aws_cloudfront_origin_access_identity.main.cloudfront_access_identity_path
    }
  }

  # Default cache behavior for UI
  default_cache_behavior {
    allowed_methods        = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods         = ["GET", "HEAD", "OPTIONS"]
    target_origin_id       = "ALB-${local.name}"
    compress               = true
    viewer_protocol_policy = "redirect-to-https"

    forwarded_values {
      query_string = true
      headers      = ["Host", "Origin", "Access-Control-Request-Headers", "Access-Control-Request-Method"]

      cookies {
        forward = "all"
      }
    }

    # Cache policy for UI
    min_ttl     = 0
    default_ttl = 300     # 5 minutes
    max_ttl     = 31536000 # 1 year
  }

  # API cache behavior (no caching for dynamic content)
  ordered_cache_behavior {
    path_pattern     = "/api/*"
    allowed_methods  = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods   = ["GET", "HEAD", "OPTIONS"]
    target_origin_id = "ALB-${local.name}"
    compress         = true

    forwarded_values {
      query_string = true
      headers      = ["*"]

      cookies {
        forward = "all"
      }
    }

    min_ttl                = 0
    default_ttl            = 0
    max_ttl                = 0
    viewer_protocol_policy = "redirect-to-https"
  }

  # Static assets cache behavior (aggressive caching)
  ordered_cache_behavior {
    path_pattern     = "/assets/*"
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "S3-${local.name}"
    compress         = true

    forwarded_values {
      query_string = false
      
      cookies {
        forward = "none"
      }
    }

    min_ttl                = 86400      # 1 day
    default_ttl            = 2592000    # 30 days
    max_ttl                = 31536000   # 1 year
    viewer_protocol_policy = "redirect-to-https"
  }

  # Health check behavior
  ordered_cache_behavior {
    path_pattern     = "/health"
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "ALB-${local.name}"
    compress         = false

    forwarded_values {
      query_string = false
      
      cookies {
        forward = "none"
      }
    }

    min_ttl                = 0
    default_ttl            = 60  # 1 minute
    max_ttl                = 300 # 5 minutes
    viewer_protocol_policy = "redirect-to-https"
  }

  # Geographic restrictions
  restrictions {
    geo_restriction {
      restriction_type = "none"
      # For demo, allow all countries
      # In production, you might want to restrict to specific regions
      # restriction_type = "whitelist"
      # locations        = ["US", "CA", "GB", "DE", "FR", "JP", "AU"]
    }
  }

  # SSL certificate
  viewer_certificate {
    acm_certificate_arn            = var.cert_arn != "" ? var.cert_arn : null
    cloudfront_default_certificate = var.cert_arn == ""
    ssl_support_method             = var.cert_arn != "" ? "sni-only" : null
    minimum_protocol_version       = var.cert_arn != "" ? "TLSv1.2_2021" : null
  }

  # Aliases
  aliases = var.cert_arn != "" ? [var.domain_name] : []

  # Custom error pages
  custom_error_response {
    error_code            = 403
    response_code         = 404
    response_page_path    = "/404.html"
    error_caching_min_ttl = 300
  }

  custom_error_response {
    error_code            = 404
    response_code         = 404
    response_page_path    = "/404.html"
    error_caching_min_ttl = 300
  }

  custom_error_response {
    error_code            = 500
    response_code         = 500
    response_page_path    = "/500.html"
    error_caching_min_ttl = 60
  }

  # Logging configuration
  logging_config {
    include_cookies = false
    bucket          = aws_s3_bucket.cloudfront_logs.bucket_domain_name
    prefix          = "cloudfront-logs/"
  }

  tags = local.common_tags
}

# S3 bucket for CloudFront logs
resource "aws_s3_bucket" "cloudfront_logs" {
  bucket        = "${local.name}-cloudfront-logs-${random_string.suffix.result}"
  force_destroy = !var.enable_deletion_protection

  tags = local.common_tags
}

resource "aws_s3_bucket_server_side_encryption_configuration" "cloudfront_logs" {
  bucket = aws_s3_bucket.cloudfront_logs.bucket

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "cloudfront_logs" {
  bucket = aws_s3_bucket.cloudfront_logs.id

  rule {
    id     = "delete_old_logs"
    status = "Enabled"

    expiration {
      days = 90
    }

    noncurrent_version_expiration {
      noncurrent_days = 30
    }
  }
}

# Route 53 DNS record (if using custom domain)
data "aws_route53_zone" "main" {
  count = var.cert_arn != "" ? 1 : 0
  name  = var.domain_name
}

resource "aws_route53_record" "main" {
  count   = var.cert_arn != "" ? 1 : 0
  zone_id = data.aws_route53_zone.main[0].zone_id
  name    = var.domain_name
  type    = "A"

  alias {
    name                   = aws_cloudfront_distribution.main.domain_name
    zone_id                = aws_cloudfront_distribution.main.hosted_zone_id
    evaluate_target_health = false
  }
}

# CloudWatch Alarms for CloudFront
resource "aws_cloudwatch_metric_alarm" "cloudfront_origin_latency" {
  alarm_name          = "${local.name}-cloudfront-origin-latency"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "OriginLatency"
  namespace           = "AWS/CloudFront"
  period              = 300
  statistic           = "Average"
  threshold           = 5000  # 5 seconds
  alarm_description   = "This metric monitors CloudFront origin latency"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    DistributionId = aws_cloudfront_distribution.main.id
    Region         = "Global"
  }

  tags = local.common_tags
}

resource "aws_cloudfront_monitoring_subscription" "main" {
  distribution_id = aws_cloudfront_distribution.main.id

  monitoring_subscription {
    realtime_metrics_subscription_config {
      realtime_metrics_subscription_status = "Enabled"
    }
  }
}
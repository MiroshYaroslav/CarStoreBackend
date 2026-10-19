resource "aws_s3_bucket" "product_images" {
  bucket        = "${local.name}-${data.aws_caller_identity.current.account_id}-product-images"
  force_destroy = true

  tags = { Name = "${local.name}-product-images" }
}

resource "aws_s3_bucket_public_access_block" "product_images" {
  bucket                  = aws_s3_bucket.product_images.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_ownership_controls" "product_images" {
  bucket = aws_s3_bucket.product_images.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "product_images" {
  bucket = aws_s3_bucket.product_images.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_cloudfront_origin_access_control" "product_images" {
  name                              = "${local.name}-product-images"
  description                       = "CloudFront access to the private product image bucket."
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

resource "aws_cloudfront_distribution" "product_images" {
  enabled         = true
  comment         = "${local.name} product images"
  price_class     = "PriceClass_100"
  is_ipv6_enabled = true

  origin {
    domain_name              = aws_s3_bucket.product_images.bucket_regional_domain_name
    origin_id                = "${local.name}-product-images"
    origin_access_control_id = aws_cloudfront_origin_access_control.product_images.id
  }

  default_cache_behavior {
    target_origin_id       = "${local.name}-product-images"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]
    compress               = true
    cache_policy_id        = "658327ea-f89d-4fab-a63d-7e88639e58f6"
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }

  tags = { Name = "${local.name}-product-images-cdn" }
}

resource "aws_s3_bucket_policy" "product_images" {
  bucket = aws_s3_bucket.product_images.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "AllowCloudFrontReadProductImages"
      Effect    = "Allow"
      Principal = { Service = "cloudfront.amazonaws.com" }
      Action    = "s3:GetObject"
      Resource  = "${aws_s3_bucket.product_images.arn}/products/*"
      Condition = {
        StringEquals = {
          "AWS:SourceArn" = aws_cloudfront_distribution.product_images.arn
        }
      }
    }]
  })
}

resource "aws_iam_role" "ecs_task" {
  name = "${local.name}-task"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
  tags = { Name = "${local.name}-task-role" }
}

resource "aws_iam_role_policy" "ecs_upload_product_images" {
  name = "${local.name}-upload-product-images"
  role = aws_iam_role.ecs_task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["s3:PutObject"]
      Resource = "${aws_s3_bucket.product_images.arn}/products/*"
    }]
  })
}

output "product_images_cloudfront_domain" {
  description = "CloudFront domain used to serve public product images from the private S3 bucket."
  value       = aws_cloudfront_distribution.product_images.domain_name
}

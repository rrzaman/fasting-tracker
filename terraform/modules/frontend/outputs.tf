output "cloudfront_url" {
  description = "CloudFront HTTPS URL for the dashboard"
  value       = "https://${aws_cloudfront_distribution.frontend.domain_name}"
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID for cache invalidation"
  value       = aws_cloudfront_distribution.frontend.id
}

output "frontend_bucket" {
  description = "S3 bucket name for frontend files"
  value       = aws_s3_bucket.frontend.bucket
}

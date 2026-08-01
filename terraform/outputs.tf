output "vpc_id" {
  description = "VPC Identifier"
  value       = aws_vpc.main.id
}

output "ecs_cluster_name" {
  description = "ECS Fargate Cluster Name"
  value       = aws_ecs_cluster.main.name
}

output "rds_endpoint" {
  description = "RDS PostgreSQL Endpoint Connection String"
  value       = aws_db_instance.postgres.endpoint
}

output "s3_bucket_name" {
  description = "S3 Bucket Name for Production Assets"
  value       = aws_s3_bucket.assets.id
}

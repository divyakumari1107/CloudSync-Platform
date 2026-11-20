output "ec2_id" {
  value = aws_instance.primary_node.id
}

output "ec2_public_ip" {
  value = aws_instance.primary_node.public_ip
}

output "s3_bucket_name" {
  value = aws_s3_bucket.replication_vault.id
}

output "s3_bucket_arn" {
  value = aws_s3_bucket.replication_vault.arn
}

output "cloudwatch_alarm_arn" {
  value = aws_cloudwatch_metric_alarm.primary_health_alarm.arn
}

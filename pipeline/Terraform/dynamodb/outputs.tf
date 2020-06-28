output "table_name" {
  value = aws_dynamodb_table.t.id
}

output "table_arn" {
  value = aws_dynamodb_table.t.arn
}
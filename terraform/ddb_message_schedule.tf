resource "aws_dynamodb_table" "ddb_message_schedule" {
  name           = "PollexyMessageSchedule"
  read_capacity  = 20
  write_capacity = 20
  hash_key       = "uuid"
  range_key      = "person_name"

  attribute {
    name = "uuid"
    type = "S"
  }

  attribute {
    name = "person_name"
    type = "S"
  }

  ttl {
    attribute_name = "TimeToExist"
    enabled = false
  }

 tags {
    Name        = "pollexy-message-schedule"
    Session     = "re:Invent 2017 ML310"
  }
}

output "message_schedule_table" {
    value = "${aws_dynamodb_table.ddb_message_schedule.name}"
}

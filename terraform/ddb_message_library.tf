resource "aws_dynamodb_table" "ddb_message_library" {
  name           = "PollexyMessageLibrary"
  read_capacity  = 20
  write_capacity = 20
  hash_key       = "Name"

  attribute {
    name = "Name"
    type = "S"
  }

  ttl {
    attribute_name = "TimeToExist"
    enabled = false
  }

 tags {
    Name        = "pollexy-message-library"
    Session     = "re:Invent 2017 ML310"
  }
}

output "message_library_table" {
    value = "${aws_dynamodb_table.ddb_message_library.name}"
}

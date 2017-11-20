resource "aws_dynamodb_table" "ddb_people" {
  name           = "PollexyPeople"
  read_capacity  = 20
  write_capacity = 20
  hash_key       = "PersonName"

  attribute {
    name = "PersonName"
    type = "S"
  }

  ttl {
    attribute_name = "TimeToExist"
    enabled = false
  }

 tags {
    Name        = "pollexy-people"
    Session     = "re:Invent 2017 ML310"
  }
}

output "people_table" {
    value = "${aws_dynamodb_table.ddb_people.name}"
}

resource "aws_dynamodb_table" "ddb_locations" {
  name           = "PollexyLocations"
  read_capacity  = 20
  write_capacity = 20
  hash_key       = "LocationName"

  attribute {
    name = "LocationName"
    type = "S"
  }

  ttl {
    attribute_name = "TimeToExist"
    enabled = false
  }

 tags {
    Name        = "pollexy-locations"
    Session     = "re:Invent 2017 ML310"
  }
}

output "location_table" {
    value = "${aws_dynamodb_table.ddb_locations.name}"
}

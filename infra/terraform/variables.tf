variable "project" {
  type    = string
  default = "docintel"
}

variable "region" {
  type    = string
  default = "us-east-1"
}

variable "tags" {
  type    = map(string)
  default = {}
}

variable "bedrock_model_id" {
  type    = string
  default = "meta.llama3-70b-instruct-v1:0"
}

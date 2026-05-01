variable "project_name" {
  type = string
}

variable "callback_urls" {
  description = "Allowed callback URLs for Cognito"
  type        = list(string)
}

provider "aws" {
  profile = "villasv"
  region  = "us-east-1"
}

variable "CONSUMER_KEY" {}
variable "CONSUMER_SECRET" {}
variable "ACCESS_TOKEN" {}
variable "ACCESS_TOKEN_SECRET" {}

data "archive_file" "package" {
  type        = "zip"
  source_dir  = "../src"
  output_path = "./.terraform/package.zip"
}

resource "aws_lambda_function" "inovespa_function" {
  function_name = "InovespaBot"
  role          = "${aws_iam_role.inovespa_role.arn}"

  filename         = "${data.archive_file.package.output_path}"
  source_code_hash = "${data.archive_file.package.output_base64sha256}"
  handler          = "function.handler"
  runtime          = "python3.8"

  environment {
    variables = {
      CONSUMER_KEY = "${var.CONSUMER_KEY}"
      CONSUMER_SECRET = "${var.CONSUMER_SECRET}"
      ACCESS_TOKEN = "${var.ACCESS_TOKEN}"
      ACCESS_TOKEN_SECRET = "${var.ACCESS_TOKEN_SECRET}"
    }
  }
}

resource "aws_iam_role" "inovespa_role" {
  name = "lambda-test-role"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
EOF
}

resource "aws_cloudwatch_event_rule" "inovespa_schedule" {
  name                = "inovespa-event-rule"
  schedule_expression = "cron(0 13 ? * 1-5 *)"
}

resource "aws_cloudwatch_event_target" "cloudwatch_lambda_target" {
  rule      = "${aws_cloudwatch_event_rule.inovespa_schedule.name}"
  arn       = "${aws_lambda_function.inovespa_function.arn}"
}

resource "aws_lambda_permission" "cloudwatch_lambda_permission" {
  action        = "lambda:InvokeFunction"
  principal     = "events.amazonaws.com"
  source_arn    = "${aws_cloudwatch_event_rule.inovespa_schedule.arn}"
  function_name = "${aws_lambda_function.inovespa_function.function_name}"
}

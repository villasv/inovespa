provider "aws" {
  profile = "villasv"
  region  = "us-east-1"
}

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

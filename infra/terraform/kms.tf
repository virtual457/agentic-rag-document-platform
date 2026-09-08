resource "aws_kms_key" "main" {
  description             = "${var.project} data encryption key"
  deletion_window_in_days = 7
  enable_key_rotation     = true
  tags                    = local.tags
}

resource "aws_kms_alias" "main" {
  name          = "alias/${var.project}"
  target_key_id = aws_kms_key.main.key_id
}

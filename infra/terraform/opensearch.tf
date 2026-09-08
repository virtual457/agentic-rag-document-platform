resource "aws_opensearchserverless_security_policy" "encryption" {
  name = "${var.project}-encryption"
  type = "encryption"
  policy = jsonencode({
    Rules      = [{ Resource = ["collection/${var.project}-vectors"], ResourceType = "collection" }]
    AWSOwnedKey = true
  })
}

resource "aws_opensearchserverless_security_policy" "network" {
  name = "${var.project}-network"
  type = "network"
  policy = jsonencode([{
    Rules = [
      { Resource = ["collection/${var.project}-vectors"], ResourceType = "collection" },
      { Resource = ["collection/${var.project}-vectors"], ResourceType = "dashboard" }
    ]
    AllowFromPublic = true
  }])
}

resource "aws_opensearchserverless_collection" "vectors" {
  name = "${var.project}-vectors"
  type = "VECTORSEARCH"
  tags = local.tags

  depends_on = [
    aws_opensearchserverless_security_policy.encryption,
    aws_opensearchserverless_security_policy.network,
  ]
}

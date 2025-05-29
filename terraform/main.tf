provider "aws" {
  access_key = var.ACCESS_KEY_ID
  secret_key = var.SECRET_ACCESS_KEY
region = "eu-west-2"
}

# Reference the existing ECS cluster
data "aws_ecs_cluster" "c14-ecs-cluster" {
  cluster_name = "c14-ecs-cluster"
}

# Create an ECR Repository
resource "aws_ecr_repository" "c14-gem-lo-pubmed-ecr" {
  name                 = "c14-gem-lo-pubmed-ecr"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

# Output the repository URL - ECR repo
output "repository_url" {
  value = aws_ecr_repository.c14-gem-lo-pubmed-ecr.repository_url
}

# ECS tasks set up
data "aws_iam_role" "ecs_task_execution_role" {
  name = "ecsTaskExecutionRole"
}

# Task Definition
resource "aws_ecs_task_definition" "c14-gem-lo-pubmed-task-definition" {
  family                   = "c14-gem-lo-pubmed-task"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"  
  cpu                      = "256"      
  memory                   = "512"     
  execution_role_arn       = data.aws_iam_role.ecs_task_execution_role.arn  
  task_role_arn            = data.aws_iam_role.ecs_task_execution_role.arn   

  container_definitions = jsonencode([
    {
      name      = "c14-gem-lo-pubmed-etl"
      image     = "129033205317.dkr.ecr.eu-west-2.amazonaws.com/c14-gem-lo-pubmed_pipeline_email:latest"
      cpu       = 256       
      memory    = 512            
      essential = true      
      environment = [
        {  
          name  = "ACCESS_KEY_ID"
          value = var.ACCESS_KEY_ID
        }, 
        {
          name  = "SECRET_ACCESS_KEY"
          value = var.SECRET_ACCESS_KEY
        },
        {  
          name  = "SENDER_EMAIL"
          value = var.SENDER_EMAIL
        }, 
        {
          name  = "RECIPIENT_EMAIL"
          value = var.RECIPIENT_EMAIL
        },
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = "/ecs/c14-gem-lo-pubmed-etl"
          "awslogs-region"        = "eu-west-2"       
          "awslogs-stream-prefix" = "ecs"
          "awslogs-create-group" = "true"
        }
      }
    }
  ])
}

resource "aws_iam_role_policy" "ecs_task_execution_policy" {
  name = "ecs_task_execution_policy"
  role = data.aws_iam_role.ecs_task_execution_role.name
  policy = jsonencode({
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": [
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "s3:GetObject",
          "s3:PutObject"
        ],
        "Resource": "*"
      }
    ]
  })
}




# EventBridge rule to trigger on new XML file creation
resource "aws_cloudwatch_event_rule" "c14-gem-lo-pubmed-event-rule" {
  name        = "c14-gem-lo-pubmed-event-rule"
  description = "Event rule for new XML files in S3 bucket"
  event_pattern = jsonencode({
    "source": ["aws.s3"],
    "detail-type": ["Object Created"],
    "detail": {
      "bucket": {
        "name": ["sigma-pharmazer-input"]
      },
      "object": {
        "key": ["c14-gem-lo-pubmed.xml"]
      }
    }
  })
}

# IAM Role for EventBridge to start ECS tasks
resource "aws_iam_role" "ecs_events_role" {
  name = "c14-gem-lo-pubmed-ecs-events-role"
  assume_role_policy = jsonencode({
    "Version": "2012-10-17",
    "Statement": [
      {
        "Action": "sts:AssumeRole",
        "Effect": "Allow",
        "Principal": {
          "Service": "events.amazonaws.com"
        }
      }
    ]
  })
}

# IAM Policy for the role
# Define a managed policy
resource "aws_iam_policy" "ecs_events_role_policy" {
  name        = "c14-gem-lo-pubmed-ecs-events-role-policy"
  description = "Policy for EventBridge to trigger ECS tasks"
  policy = jsonencode({
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": [
          "ecs:RunTask"
        ],
        "Resource": [
          "arn:aws:ecs:*:129033205317:task-definition/c14-gem-lo-pubmed-task:*",
          "arn:aws:ecs:*:129033205317:task-definition/c14-gem-lo-pubmed-task"
        ],
        "Condition": {
          "ArnLike": {
            "ecs:cluster": "arn:aws:ecs:*:129033205317:cluster/c14-ecs-cluster"
          }
        }
      },
      {
        "Effect": "Allow",
        "Action": "iam:PassRole",
        "Resource": [
          "*"
        ],
        "Condition": {
          "StringLike": {
            "iam:PassedToService": "ecs-tasks.amazonaws.com"
          }
        }
      }
    ]
  })
}

# Attach the managed policy to the role
resource "aws_iam_role_policy_attachment" "ecs_events_role_policy_attachment" {
  role       = aws_iam_role.ecs_events_role.name
  policy_arn = aws_iam_policy.ecs_events_role_policy.arn
}

# CloudWatch Event Target definition to launch the ECS task
resource "aws_cloudwatch_event_target" "ecs_task_target" {
  rule      = aws_cloudwatch_event_rule.c14-gem-lo-pubmed-event-rule.name
  arn       = data.aws_ecs_cluster.c14-ecs-cluster.arn
  role_arn  = aws_iam_role.ecs_events_role.arn
  ecs_target {
    launch_type = "FARGATE"
    task_definition_arn = aws_ecs_task_definition.c14-gem-lo-pubmed-task-definition.arn
    network_configuration {
      subnets         = ["subnet-0497831b67192adc2", "subnet-0acda1bd2efbf3922", "subnet-0465f224c7432a02e"]
      security_groups = [aws_security_group.c14-gem-lo-pubmed-sg.id]
      assign_public_ip = true
    }
  }
}

# Security Group for ECS Tasks
resource "aws_security_group" "c14-gem-lo-pubmed-sg" {
  name        = "c14-gem-lo-pubmed-sg"
  description = "Security group for ECS Fargate tasks"
  vpc_id      = var.VPC_ID 
  egress {
    from_port   = 0
    to_port     = 65525
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  ingress {
    from_port   = 0
    to_port     = 65525
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
terraform {
  required_version = ">= 1.5"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
    
    http = {
      source  = "hashicorp/http"
      version = ">= 3.0"
    }
    
    local = {
      source  = "hashicorp/local"
      version = ">= 2.0"
    }
    
    shell = {
      source  = "scottwinkler/shell"
      version = ">= 1.7.0"
    }
  }
} 
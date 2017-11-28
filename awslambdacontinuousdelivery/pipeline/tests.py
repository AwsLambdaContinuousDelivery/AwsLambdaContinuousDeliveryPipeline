from awacs.aws import Statement, Allow, Action
from awslambdacontinuousdelivery.tools import alphanum
from awslambdacontinuousdelivery.tools.iam import defaultAssumeRolePolicyDocument

from troposphere import Template, Join, Sub, Ref
from troposphere.codebuild import Project, Environment, Source, Artifacts
from troposphere.codepipeline import (Stages, Actions, ActionTypeID
  , InputArtifacts)
from troposphere.iam import Role, Policy

from typing import List

import awacs.aws

def getBuildRole(stage: str = "") -> Role:
  statement = Statement( Action = [ Action("*") ]
                       , Effect = Allow
                       , Resource = ["*"]
                       )
  policy_doc = awacs.aws.Policy( Statement = [ statement ] )
  policy = Policy( PolicyName = Sub("${AWS::StackName}-TestBuilderPolicy")
                 , PolicyDocument = policy_doc
                 )
  assume = defaultAssumeRolePolicyDocument("codebuild.amazonaws.com")
  return Role( "TestBuilderRole" + stage
             , RoleName = Sub("LambdaTestBuilderRole-${AWS::StackName}"+stage)
             , AssumeRolePolicyDocument = assume
             , Policies = [policy]
             )


def getTestBuildCode() -> List[str]:
  return [ "version: 0.2"
         , "\n"
         , "phases:"
         , "  install:"
         , "    commands:"
         , "      - apk update"
         , "      - apk upgrade"
         , "      - apk add --no-cache openssl"
         , "      - pip3 install boto3"
         , "  build:" 
         , "    commands:"
         , "      - wget https://raw.githubusercontent.com/AwsLambdaContinuousDelivery/AwsLambdaTesting/dev/testRunner.py"
         ]


def buildCfWithDockerAction( buildRef, inputName: str) -> Action:
  actionId = ActionTypeID( Category = "Build"
                         , Owner = "AWS"
                         , Version = "1"
                         , Provider = "CodeBuild"
                         )
  return Actions( Name = Sub("${AWS::StackName}-TestCfBuilderAction")
                , ActionTypeId = actionId
                , InputArtifacts = [ InputArtifacts( Name = inputName ) ]
                , RunOrder = "2"
                , Configuration = { "ProjectName" : Ref(buildRef) }
                )


def getBuildSpec(stage: str) -> List[str]:
  spec = getTestBuildCode()
  spec.append("\n")
  spec.append(
        Join(" ", [ "      - python3 testRunner.py -p $(pwd)/ --stage"
                  , stage
                  , "--stack"
                  , Sub("${AWS::StackName}")
                  ]
            )
        )
  return spec


def getCodeBuild(serviceRole: Role, stage: str, buildspec: List[str]) -> Project:
  env = Environment( ComputeType = "BUILD_GENERAL1_SMALL"
                   , Image = "frolvlad/alpine-python3"
                   , Type = "LINUX_CONTAINER"
                   , PrivilegedMode = False
                   )
  source = Source( Type = "CODEPIPELINE"
                 , BuildSpec = Join("\n", buildspec )
                 )
  artifacts = Artifacts( Type = "CODEPIPELINE" )
  return Project( alphanum("TestBuild" + stage)
                , Name = Sub("${AWS::StackName}-" + stage)
                , Environment = env
                , Source = source
                , Artifacts = artifacts
                , ServiceRole = Ref(serviceRole)
                )


def getTest(t: Template, inputArt: str, stage: str) -> Action:
  role = t.add_resource(getBuildRole(stage))
  buildspec = getBuildSpec(stage)
  cb = getCodeBuild(role, stage, buildspec)
  build_ref = t.add_resource(cb)
  return buildCfWithDockerAction(build_ref, inputArt)
from awacs.aws import Statement, Allow, Action
from awslambdacontinuousdelivery.tools import alphanum
from awslambdacontinuousdelivery.tools.iam import defaultAssumeRolePolicyDocument

from troposphere import Template, Ref, Sub, Join
from troposphere.codebuild import ( Project
  , Environment, Source, Artifacts )
from troposphere.codepipeline import ( InputArtifacts
  , Actions, Stages, ActionTypeID, OutputArtifacts )
from troposphere.iam import Role, Policy

from typing import List

import awacs.aws

def getBuildCode() -> List[str]:
  return [ "version: 0.2"
         , "\n"
         , "phases:"
         , "  install:"
         , "    commands:"
         , "      - apk update"
         , "      - apk upgrade"
         , "      - apk add --no-cache bash git openssl"
         , "  pre_build:"
         , "    commands:"
         , "      - pip3 install troposphere"
         , "      - pip3 install awacs"
         , "      - git clone https://github.com/AwsLambdaContinuousDelivery/AwsLambdaContinuousDeliveryTools.git"
         , "      - cd AwsLambdaContinuousDeliveryTools"
         , "      - pip3 install ."
         , "      - cd .."
         , "      - rm -rf AwsLambdaContinuousDeliveryTools"
         , "      - wget https://raw.githubusercontent.com/AwsLambdaContinuousDelivery/AwsLambdaContinuousDeliveryLambdaCfGenerator/dev/createCF.py"
         , "  build:"
         , "    commands:"
         ]


def getBuildRole() -> Role:
  statement = Statement( Action = [ Action("*") ]
                       , Effect = Allow
                       , Resource = ["*"]
                       )
  policy_doc = awacs.aws.Policy( Statement = [ statement ] )
  policy = Policy( PolicyName = Sub("${AWS::StackName}-CodeBuildPolicy")
                 , PolicyDocument = policy_doc
                 )
  assume = defaultAssumeRolePolicyDocument("codebuild.amazonaws.com")
  return Role( "CodeBuildRole"
             , RoleName = Sub("${AWS::StackName}-LambdaCodeBuildRole")
             , AssumeRolePolicyDocument = assume
             , Policies = [policy]
             )


def getBuildSpec(input: str, stages: List[str]) -> List[str]:
  file_code = getBuildCode()
  stage_cmds = []
  for s in stages:
    x = Join(" ", [ "      - python3 createCF.py --path $(pwd)/ --stage"
                  , s.capitalize()
                  , "--stack"
                  , Sub("${AWS::StackName}")
                  , ">> stack" + s.capitalize() + ".json"
                  ]
         )
    stage_cmds.append(x)

  prod = Join(" ", [ "      - python3 createCF.py --path $(pwd)/ --stage"
                   , "PROD --stack"
                   , Sub("${AWS::StackName}")
                   , ">> stackPROD.json"
                   ]
             )
  stage_cmds.append(prod)
  build_cmd = Join("\n", stage_cmds)
  artifacts = [ "artifacts:"
              , "  files:"
              , "    - stackPROD.json"
              ]
  for s in stages:
    artifacts.append("    - stack" + s.capitalize() + ".json")
  artifacts = Join("\n",artifacts)

  file_code.append("\n")
  file_code.append(build_cmd)
  file_code.append("\n")
  file_code.append(artifacts)
  return file_code


def buildCfWithDockerAction(buildRef, inputName, outputName) -> Actions:
  actionId = ActionTypeID( Category = "Build"
                         , Owner = "AWS"
                         , Version = "1"
                         , Provider = "CodeBuild"
                         )
  return Actions( Name = Sub("${AWS::StackName}-CfBuilderAction")
                , ActionTypeId = actionId
                , InputArtifacts = [InputArtifacts( Name = inputName )]
                , OutputArtifacts =[OutputArtifacts( Name = outputName)]
                , RunOrder = "1"
                , Configuration = { "ProjectName" : Ref(buildRef) }
                )


def buildStage(buildRef, inputName: str, outputName: str) -> Stages:
    action = buildCfWithDockerAction(buildRef, inputName, outputName)
    return Stages( "CfBuild"
                 , Name = "Build"
                 , Actions = [ action ]
                 )


def getCodeBuild(serviceRole: Role, buildspec: List[str]) -> Project:
  env = Environment( ComputeType = "BUILD_GENERAL1_SMALL"
                   , Image = "frolvlad/alpine-python3"
                   , Type = "LINUX_CONTAINER"
                   , PrivilegedMode = False
                   )
  source = Source( Type = "CODEPIPELINE"
                 , BuildSpec = Join("\n", buildspec )
                 )
  artifacts = Artifacts( Type = "CODEPIPELINE" )
  return Project( "BackEndLambdaBuilder"
                , Name = Sub("${AWS::StackName}-LambdaBuilder")
                , Environment = env
                , Source = source
                , Artifacts = artifacts
                , ServiceRole = Ref(serviceRole)
                )


def getBuild( template: Template
            , inputName: str
            , outputName: str
            , stages: List[str]
            ) -> Stages:
  role = template.add_resource(getBuildRole())
  spec = getBuildSpec(inputName, stages)
  cb = getCodeBuild(role, spec)
  build_ref = template.add_resource(cb)
  return buildStage(build_ref, inputName, outputName)

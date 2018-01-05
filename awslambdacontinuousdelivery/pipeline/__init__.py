
from awslambdacontinuousdelivery.pipeline.source import *
from awslambdacontinuousdelivery.python.build import buildStage
from awslambdacontinuousdelivery.pipeline.tests import *
from awslambdacontinuousdelivery.pipeline.deploy import *
from awslambdacontinuousdelivery.tools import alphanum
from awslambdacontinuousdelivery.tools.iam import *

from troposphere import *
from troposphere.codepipeline import (
  Pipeline, Stages, Actions, ActionTypeID, OutputArtifacts, InputArtifacts,
  ArtifactStore )
from troposphere.s3 import Bucket

def createCodepipelineRole(name: str) -> Role:
  assume = defaultAssumeRolePolicyDocument("codepipeline.amazonaws.com")
  policy = oneClickCodePipeServicePolicy()
  return Role( alphanum(name)
             , RoleName = Sub("${AWS::StackName}PipelineRole")
             , AssumeRolePolicyDocument = assume
             , Policies = [policy]
             )

def createArtifactStoreS3Location():
  return Bucket(
      "ArtifactStoreS3Location"
    , AccessControl = "Private"
    )


def createPipeline(stages: List[str] = [], github: bool = False) -> str:
  template = Template()
  stackName = Sub("${AWS::StackName}")
  source = "SourceFiles"
  interimArt = "FunctionDeployCode"
  CfTemplate = "CfOutputTemplate"

  s3 = template.add_resource(createArtifactStoreS3Location())
  pipelineRole = template.add_resource(
      createCodepipelineRole("PipelineRole"))
  
  deployRes = getDeployResources(template)
  
  pipe_stages = []
  pipe_stages.append(getSource(template, github, source))
  pipe_stages.append(buildStage(template, source, interimArt, CfTemplate, stages))

  for s in stages:
    pipe_stages.append(
      getDeploy(template,CfTemplate,s.capitalize(),deployRes, interimArt, source))
  pipe_stages.append(
      getDeploy(template, CfTemplate,"PROD", deployRes, interimArt, source))

  artifactstore = ArtifactStore( Type = "S3", Location = Ref(s3))

  pipeline = Pipeline( "FunctionsPipeline"
                     , Name = Sub("${AWS::StackName}-Pipeline")
                     , RoleArn = GetAtt(pipelineRole, "Arn")
                     , Stages = pipe_stages
                     , ArtifactStore = artifactstore
                     )
  template.add_resource(pipeline)
  return template.to_json()


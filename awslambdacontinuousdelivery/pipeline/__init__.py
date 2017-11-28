
from awslambdacontinuousdelivery.pipeline.source import *
from awslambdacontinuousdelivery.pipeline.build import *
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


def createPipeline(prefix: str, stages: List[str] = []) -> str:
  template = Template()
  repo = template.add_parameter(
    Parameter( "repo"
             , Description="url of the repository"
             , Type="String"
             ) 
    )
  branch = template.add_parameter(
    Parameter( "branch"
             , Description="branch triggering deployment"
             , Type="String"
             ) 
    )
  repo = Ref(repo)
  branch = Ref(branch)
  stackName = Sub("${AWS::StackName}")
  sfiles_name = "SourceFiles"
  build_cf_name = "CfOutputTemplate"

  s3 = template.add_resource(createArtifactStoreS3Location())
  pipelineRole = template.add_resource(
      createCodepipelineRole("PipelineRole"))
  
  deployRes = getDeployResources(template)
  
  pipe_stages = []
  pipe_stages.append(getSource(sfiles_name, repo, branch))
  pipe_stages.append(getBuild(template, sfiles_name, build_cf_name, stages))
  for s in stages:
    pipe_stages.append(getDeploy(template, build_cf_name, s.capitalize(), deployRes, sfiles_name))
  pipe_stages.append(getDeploy(template, build_cf_name,"PROD", deployRes))

  artifactstore = ArtifactStore( Type = "S3", Location = Ref(s3))

  pipeline = Pipeline( "FunctionsPipeline"
                     , Name = Sub("${AWS::StackName}-Pipeline")
                     , RoleArn = GetAtt(pipelineRole, "Arn")
                     , Stages = pipe_stages
                     , ArtifactStore = artifactstore
                     )
  template.add_resource(pipeline)
  return template.to_json()


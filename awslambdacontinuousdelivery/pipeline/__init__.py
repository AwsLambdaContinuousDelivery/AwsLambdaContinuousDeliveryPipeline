# By Janos Potecki
# University College London
# January 2018

from awslambdacontinuousdelivery.source.codecommit import getCodeCommit
from awslambdacontinuousdelivery.source.github import getGitHub
from awslambdacontinuousdelivery.python.build import getBuild
from awslambdacontinuousdelivery.deploy import getDeploy
from awslambdacontinuousdelivery.python.test.unittest import getUnittest
from awslambdacontinuousdelivery.notifications import addFailureNotifications
from awslambdacontinuousdelivery.notifications.sns import getEmailTopic, getTopicPolicy
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

def getSource(t: Template, github: bool, outputfiles: str) -> Stages:
  if github:
    return getGitHub(t, outputfiles)
  return getCodeCommit(t, outputfiles)


def createPipelineTemplate( stages: List[str] = []
                          , github: bool = False
                          ) -> Template:
  template = Template()
  stackName = Sub("${AWS::StackName}")
  source = "SourceFiles"
  interimArt = "FunctionDeployCode"
  CfTemplate = "CfOutputTemplate"

  s3 = template.add_resource(createArtifactStoreS3Location())
  pipelineRole = template.add_resource(
      createCodepipelineRole("PipelineRole"))

  pipe_stages = []
  pipe_stages.append(getSource(template, github, source)) # also own package
  pipe_stages.append(getUnittest(template, source))
  pipe_stages.append(getBuild(template, source, interimArt, CfTemplate, stages))

  for s in stages:
    pipe_stages.append(
      getDeploy(template, CfTemplate, s.capitalize(), interimArt, source, add_tests = True))
  pipe_stages.append(
      getDeploy(template, CfTemplate, "PROD", interimArt))

  artifactstore = ArtifactStore( Type = "S3", Location = Ref(s3))

  pipeline = Pipeline( "FunctionsPipeline"
                     , Name = Sub("${AWS::StackName}-Pipeline")
                     , RoleArn = GetAtt(pipelineRole, "Arn")
                     , Stages = pipe_stages
                     , ArtifactStore = artifactstore
                     )
  template.add_resource(pipeline)

  # Add notifications in case something fails
  email = Parameter( "FailureNotificationEmailAddressParameter"
                   , Type = "String"
                   ,  Description = "E-Mail Address getting notified if any stage fails"
                   )
  email = template.add_parameter(email)
  emailTopic = getEmailTopic("StateFailures", Ref(email))
  notificationRole = addFailureNotifications(template, Ref(pipeline), emailTopic)
  
  return template

def createPipeline(stages: List[str] = [], github: bool = False) -> str:
  return createPipelineTemplate(stages, github).to_json()

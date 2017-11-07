from troposphere import Template
from troposphereWrapper.pipeline import *


def getSource(outputfiles: str) -> Stages:
  return sourceStage("FlightZipperBackEndFunctions", "master", outputfiles)


def sourceStage(repo: str, branch: str, outputfiles: str) -> Stages:
  actionid = CodePipelineActionTypeIdBuilder() \
      .setCodeCommitSource("1") \
      .build()
  
  action = CodePipelineActionBuilder() \
      .setName("BackendCloudformationLambdaSource") \
      .setConfiguration({"BranchName" : branch, "RepositoryName" : repo}) \
      .setActionType(actionid) \
      .addOutput(OutputArtifacts( Name = outputfiles)) \
      .build()

  return CodePipelineStageBuilder() \
      .setName("Source") \
      .addAction(action) \
      .build()
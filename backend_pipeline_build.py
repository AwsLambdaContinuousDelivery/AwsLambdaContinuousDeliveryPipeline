from troposphere import Template, Ref

from troposphereWrapper.codebuild import *
from troposphereWrapper.pipeline import *
from troposphereWrapper.iam import *

from typing import List


def getBuildRole() -> Role:
  codebuildPolicy = PolicyBuilder() \
      .setName("CodeBuildPolicy") \
      .addStatement(
        StatementBuilder() \
          .setEffect(Effects.Allow) \
          .addAction(awacs.aws.Action("*")) \
          .addResource("*")
          .build() \
          ) \
      .build()
  return RoleBuilder() \
    .setName("ElmCodeBuildRole") \
    .setAssumePolicy(
      RoleBuilderHelper() \
        .defaultAssumeRolePolicyDocument("codebuild.amazonaws.com")
      ) \
    .addPolicy(codebuildPolicy) \
    .build()


def getBuildSpec(input: str) -> List[str]:
  # TODO: pass in the content in order to build the cloud formation file
  folder = ""
  return [ "version: 0.2"
         , "phases:"
         , "  build:"
         , "    commands:"
         , "      - python3 createCF.py " + folder
         , "artifacts:"
         , "  files:"
         , "    - /*"
         , "  discard-path: yes"
         ]


def buildCfWithDockerAction(buildRef, inputName, outputName):
    actionid = CodePipelineActionTypeIdBuilder() \
      .setCodeBuildSource("1") \
      .build()
    return CodePipelineActionBuilder() \
      .setName("BuildCfWithDockerAction") \
      .setActionType(actionid) \
      .addInput(InputArtifacts( Name = inputName )) \
      .addOutput(OutputArtifacts( Name = outputName )) \
      .setConfiguration( { "ProjectName" : Ref(buildRef) } ) \
      .build()


def buildStage(buildRef, inputName: str, outputName: str) -> Stages:
    action = buildCfWithDockerAction( \
                  buildRef, inputName, outputName)
    return CodePipelineStageBuilder() \
      .setName("Build") \
      .addAction(action) \
      .build()


def getCodeBuild(serviceRole: Role, buildspec: List[str]):
  name = "FrontEndElmAppBuilder"
  env = CodeBuildEnvBuilder() \
        .setComputeType("BUILD_GENERAL1_SMALL") \
        .setImage("janosp/lambdacicdbuilder") \
        .setType("LINUX_CONTAINER") \
        .addEnvVars( { "Name": "APP_NAME", "Value": name } ) \
        .build()
  source = CodeBuildSourceBuilder() \
        .setType(CBSourceType.CodePipeline) \
        .setBuildSpec(Join("", buildspec)) \
        .build()
  artifacts = CodeBuildArtifactsBuilder() \
        .setType(CBArtifactType.CodePipeline) \
        .build()
  return CodeBuildBuilder() \
        .setArtifacts(artifacts) \
        .setEnvironment(env) \
        .setSource(source) \
        .setName(name) \
        .setServiceRole(Ref(serviceRole)) \
        .build()


def getBuild(template: Template, inputName: str, outputName: str) -> Stages:
  role = getBuildRole()
  spec = getBuildSpec(inputName)
  cb = getCodeBuild(role, spec)
  build_ref = template.add_resource(cb)
  return buildStage(build_ref, inputName, outputName)

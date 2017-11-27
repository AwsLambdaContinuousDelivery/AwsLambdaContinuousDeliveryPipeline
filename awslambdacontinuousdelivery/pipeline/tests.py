
from awacs.awslambda import *
from troposphere.codepipeline import *
from troposphere.iam import Role
from troposphere import Template, Join, Sub, Ref
from troposphere.codebuild import *
from troposphereWrapper.codebuild import *
from troposphereWrapper.pipeline import *
from troposphereWrapper.iam import *
from typing import List

#TODO: a lot of dublication with the build stage here, 
# I should do the build stage more generic
# or introduce helpers
def getBuildRole(stackName: str) -> Role:
  codebuildPolicy = PolicyBuilder() \
      .setName(stackName + "TstCBPolicy") \
      .addStatement(
        StatementBuilder() \
          .setEffect(Effects.Allow) \
          .addAction(awacs.aws.Action("*")) \
          .addResource("*")
          .build() \
          ) \
      .build()
  return RoleBuilder() \
    .setName(stackName + "TstCBRole") \
    .setAssumePolicy(
      RoleBuilderHelper() \
        .defaultAssumeRolePolicyDocument("codebuild.amazonaws.com")
      ) \
    .addPolicy(codebuildPolicy) \
    .build()


def getCodeFromFile(filepath: str) -> List[str]:
  with open (filepath, "r") as xs:
    code = xs.readlines()
  return code

def buildCfWithDockerAction( buildRef, inputName: str) -> Action:
    actionid = CodePipelineActionTypeIdBuilder() \
      .setCodeBuildSource("1") \
      .build()
    return CodePipelineActionBuilder() \
      .setName("TestCfWithDockerAction") \
      .setActionType(actionid) \
      .addInput(InputArtifacts( Name = inputName )) \
      .setConfiguration( { "ProjectName" : Ref(buildRef) } ) \
      .setRunOrder(2)\
      .build()


def getBuildSpec(stage: str) -> List[str]:
  spec = getCodeFromFile("codebuild_test_spec.yaml")
  spec.append(
        Join(" ", [ "\n      - python3 testRunner.py -p $(pwd)/ --stage"
                  , stage
                  , "--stack"
                  , Sub("${AWS::StackName}")
                  ]
            )
        )
  return spec

def getCodeBuild(serviceRole: Role, name: str, buildspec: List[str]) -> Project:
  env = Environment( ComputeType = "BUILD_GENERAL1_SMALL"
                   , Image = "frolvlad/alpine-python3"
                   , Type = "LINUX_CONTAINER"
                   , PrivilegedMode = False
                   )
  source = CodeBuildSourceBuilder() \
        .setType(CBSourceType.CodePipeline) \
        .setBuildSpec(Join("", buildspec)) \
        .build()
  artifacts = Artifacts( Type = "CODEPIPELINE")

  return Project( name,
                  Name = Sub(name + "-${AWS::StackName}")
                , Environment = env
                , Source = source
                , Artifacts = artifacts
                , ServiceRole = Ref(serviceRole)
                )


def getTest(t: Template, inputArt: str, stackName: str, stage: str) -> Action:
  name = stackName + stage
  role = t.add_resource(getBuildRole(name))
  buildspec = getBuildSpec(stage)
  cb = getCodeBuild(role, name, buildspec)
  build_ref = t.add_resource(cb)
  return buildCfWithDockerAction(build_ref, inputArt)
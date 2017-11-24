
from awacs.awslambda import *
from troposphere.codepipeline import *
from troposphere.iam import Role
from troposphere import Template

from typing import List

def getCodeBuild(serviceRole: Role, buildspec: List[str]):
  name = "BackEndLambdaBuilder"
  env = CodeBuildEnvBuilder() \
        .setComputeType("BUILD_GENERAL1_SMALL") \
        .setImage("frolvlad/alpine-python3") \
        .setType("LINUX_CONTAINER") \
        .setPrivilegedMode(False) \
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


def getTest(t: Template, inputArt: str, stackName: str) -> Stages:
  pass
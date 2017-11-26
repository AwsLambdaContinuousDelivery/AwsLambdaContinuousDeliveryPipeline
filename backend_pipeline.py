import yaml, sys

from troposphere import *

from troposphereWrapper.pipeline import *

from backend_pipeline_source import *
from backend_pipeline_build import *
from backend_pipeline_test import *
from backend_pipeline_deploy import *

from helpers import *

import argparse

def createArtifactStoreS3Location():
  return s3.Bucket(
      "ArtifactStoreS3Location"
    , AccessControl = "Private"
    )


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("-t", "--testPath", help="Path of the folder with the source-code of the aws lambda functions")




  template = Template()
  sfiles_name = "CloudFormationSourceLambdaFiles"
  build_cf_name = "CfOutputTemplate"
  stackName = "FZBackendFunctions"
  s3 = template.add_resource(createArtifactStoreS3Location())
  pipelineRole = template.add_resource(
      createCodepipelineRole("FZBackendFunctionsPipelineRole"))
  deployRes = getDeployResources(template)
  pipe = PipelineBuilder() \
    .setName("FlightZipperBackendFunctionsPipeline") \
    .setArtStorage(CodePipelineArtifactStore().setS3Bucket(s3).build()) \
    .setCodePipelineServiceRole(pipelineRole) \
    .addStage(getSource(sfiles_name)) \
    .addStage(getBuild(template, sfiles_name, build_cf_name)) \
    .addStage(getDeploy(template, build_cf_name, "Alpha", stackName,deployRes, sfiles_name))\
    .addStage(getDeploy(template, build_cf_name, "PROD", stackName, deployRes))\
    .build()
  template.add_resource(pipe)
  print(template.to_json())


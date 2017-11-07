import yaml, sys

from troposphere import *

from troposphereWrapper.pipeline import *

from backend_pipeline_source import *
from backend_pipeline_build import *
from backend_pipeline_deploy import *
from helpers import *

def createArtifactStoreS3Location():
  return s3.Bucket(
      "ArtifactStoreS3Location"
    , AccessControl = "Private"
    )


if __name__ == "__main__":
  template = Template()
  source_files_name = "CloudFormationSourceLambdaFiles"
  build_cf_name = "CfOutputTemplate"
  stackName = "FZBackendFunctions"
  s3 = template.add_resource(createArtifactStoreS3Location())
  pipelineRole = template.add_resource(
      createCodepipelineRole("FZBackendFunctionsPipelineRole"))
  pipe = PipelineBuilder() \
    .setName("FlightZipperBackendFunctionsPipeline") \
    .setArtStorage(CodePipelineArtifactStore().setS3Bucket(s3).build()) \
    .setCodePipelineServiceRole(pipelineRole) \
    .addStage(getSource(source_files_name)) \
    .addStage(getBuild(template, source_files_name, build_cf_name)) \
    .addStage(getProdDeploy(template, build_cf_name, stackName)) \
    .build()
  template.add_resource(pipe)
  print(template.to_json())


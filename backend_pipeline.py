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
  parser.add_argument("-p", "--prefix", help = "Prefix for the Lambda Stacks", type = str, required=True)
  parser.add_argument("--github", help = "source is GitHub", type = bool)
  parser.add_argument("--codecommit", help = "source is CodeCommit", type = bool)
  parser.add_argument("--stages", nargs="+", help="Set flag and add all stage names EXCEPT PROD, if no flag is set, then there will be just a PROD stage", required=False)
  
  args = parser.parse_args()

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
  if not args.stages:
    args.stages = []
  repo = Ref(repo)
  branch = Ref(branch)
  stackName = args.prefix
  sfiles_name = stackName + "SourceFiles"
  build_cf_name = stackName + "CfOutputTemplate"

  s3 = template.add_resource(createArtifactStoreS3Location())
  pipelineRole = template.add_resource(
      createCodepipelineRole(stackName + "PipelineRole"))
  
  deployRes = getDeployResources(template, stackName)
  
  pipe = PipelineBuilder() \
    .setName(stackName + "FunctionsPipeline") \
    .setArtStorage(CodePipelineArtifactStore().setS3Bucket(s3).build()) \
    .setCodePipelineServiceRole(pipelineRole) \
    .addStage(getSource(sfiles_name, repo, branch)) \
    .addStage(getBuild(template, sfiles_name, build_cf_name, args.stages))
  if args.stages:
    for s in args.stages:
      pipe.addStage(getDeploy(template, build_cf_name, s.capitalize(), stackName, deployRes, sfiles_name))
  pipe.addStage(getDeploy(template, build_cf_name,"PROD", stackName, deployRes))
  template.add_resource(pipe.build())
  print(template.to_json())


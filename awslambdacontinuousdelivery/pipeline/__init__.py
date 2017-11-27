from troposphereWrapper.iam import *

def createCodepipelineRole(name: str) -> Role:
  return RoleBuilder() \
      .setName(name) \
      .setAssumePolicy(
        RoleBuilderHelper() \
        .defaultAssumeRolePolicyDocument("codepipeline.amazonaws.com")
          ) \
      .addPolicy(RoleBuilderHelper().oneClickCodePipeServicePolicy()) \
      .build()
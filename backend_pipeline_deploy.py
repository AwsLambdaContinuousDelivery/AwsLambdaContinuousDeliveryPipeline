from troposphere import Template, GetAtt, Ref, Sub

from awacs.ec2 import *
from awacs.iam import *
from awacs.awslambda import *
from troposphere.iam import Role
from troposphereWrapper.pipeline import *
from troposphereWrapper.iam import *

from typing import Tuple

def getDeployResources(t: Template) -> Tuple[ActionTypeID, Role]:
  policyDoc = PolicyDocumentBuilder() \
    .addStatement(StatementBuilder() \
        .addAction(awacs.ec2.Action("*")) \
        .addAction(awacs.awslambda.GetFunction) \
        .addAction(awacs.awslambda.CreateFunction) \
        .addAction(awacs.awslambda.GetFunctionConfiguration) \
        .addAction(awacs.awslambda.DeleteFunction) \
        .addAction(awacs.awslambda.UpdateFunctionCode) \
        .addAction(awacs.awslambda.UpdateFunctionConfiguration) \
        .addAction(awacs.awslambda.CreateAlias) \
        .addAction(awacs.awslambda.DeleteAlias) \
        .setEffect(Effects.Allow) \
        .addResource("*") \
        .build() 
      ) \
    .addStatement(StatementBuilder() \
        .addAction(awacs.iam.DeleteRole) \
        .addAction(awacs.iam.DeleteRolePolicy) \
        .addAction(awacs.iam.GetRole) \
        .addAction(awacs.iam.PutRolePolicy) \
        .addAction(awacs.iam.CreateRole) \
        .addAction(awacs.iam.PassRole)
        .setEffect(Effects.Allow) \
        .addResource("*") \
        .build()
      ) \
    .build()

  policy = Policy( PolicyDocument = policyDoc
                 , PolicyName = "CFDeployPolicy"
                 )

  role = t.add_resource( RoleBuilder() \
          .setName("CFDeplyRole") \
          .setAssumePolicy(RoleBuilderHelper() \
            .defaultAssumeRolePolicyDocument("cloudformation.amazonaws.com")) \
          .addPolicy(policy) \
          .build()
         )

  actionId = CodePipelineActionTypeIdBuilder() \
      .setCategory(ActionIdCategory.Deploy) \
      .setOwner(ActionIdOwner.AWS) \
      .setProvider("CloudFormation") \
      .setVersion("1") \
      .build()
  return [actionId, role]


def getDeploy( t: Template
             , inName: str
             , stage: str
             , sName: str
             , resource: Tuple[ActionTypeID, Role]
             ) -> Stages:
  [actionId, role] = resource
  config = { "ActionMode" : "CREATE_UPDATE"
           , "RoleArn" : GetAtt(role, "Arn")
           , "StackName" : sName + stage
           , "Capabilities": "CAPABILITY_NAMED_IAM"
           , "TemplatePath" : inName + "::stack" + stage + ".json"
           }
  action = CodePipelineActionBuilder() \
      .setName("Deploy" + sName + stage) \
      .setActionType(actionId) \
      .addInput(InputArtifacts(Name = inName)) \
      .addOutput(OutputArtifacts(Name = stage)) \
      .setConfiguration(config) \
      .build()
  
  return CodePipelineStageBuilder() \
      .setName(stage + "_Deploy") \
      .addAction(action) \
      .build()
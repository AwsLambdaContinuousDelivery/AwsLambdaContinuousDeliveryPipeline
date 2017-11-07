from troposphere import Template, GetAtt, Ref, Sub

from awacs.ec2 import *
from troposphere.iam import Role
from troposphereWrapper.pipeline import *
from troposphereWrapper.iam import *



def getProdDeploy(t: Template, inName: str, sName: str) -> Stages:
  policyDoc = PolicyDocumentBuilder() \
    .addStatement(StatementBuilder() \
        .addAction(awacs.ec2.Action("*")) \
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
  config =  { "ActionMode" : "CREATE_UPDATE"
            , "RoleArn" : GetAtt(role, "Arn")
            , "StackName" : sName
            , "Capabilities": "CAPABILITY_NAMED_IAM"
            , "TemplatePath" : inName + "::stack.json"
            }

  actionId = CodePipelineActionTypeIdBuilder() \
      .setCategory(ActionIdCategory.Deploy) \
      .setOwner(ActionIdOwner.AWS) \
      .setProvider("CloudFormation") \
      .setVersion("1") \
      .build()

  action = CodePipelineActionBuilder() \
      .setName("Deploy" + sName) \
      .setActionType(actionId) \
      .addInput(InputArtifacts(Name = inName)) \
      .setConfiguration(config) \
      .build()
  
  return CodePipelineStageBuilder() \
      .setName("DeployStage") \
      .addAction(action) \
      .build()
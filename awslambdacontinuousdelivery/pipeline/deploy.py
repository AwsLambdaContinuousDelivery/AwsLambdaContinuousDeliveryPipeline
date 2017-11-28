

from awacs.aws import Allow
from awacs.iam import *
from awacs.awslambda import *

from awslambdacontinuousdelivery.tools import alphanum
from awslambdacontinuousdelivery.tools.iam import defaultAssumeRolePolicyDocument
from awslambdacontinuousdelivery.pipeline.tests import getTest

from troposphere import Template, GetAtt, Ref, Sub
from troposphere.codepipeline import ( ActionTypeID
  , Actions, Stages, OutputArtifacts, InputArtifacts )
from troposphere.iam import Role, Policy

from typing import Tuple

import awacs.aws
import awacs.ec2
import re

def getDeployResources(t: Template) -> Tuple[ActionTypeID, Role]:
  statements = [
      awacs.aws.Statement(
          Action = [ awacs.ec2.Action("*")
                   , awacs.awslambda.GetFunction
                   , awacs.awslambda.CreateFunction
                   , awacs.awslambda.GetFunctionConfiguration
                   , awacs.awslambda.DeleteFunction
                   , awacs.awslambda.UpdateFunctionCode
                   , awacs.awslambda.UpdateFunctionConfiguration
                   , awacs.awslambda.CreateAlias
                   , awacs.awslambda.DeleteAlias
                   ]
        , Resource = [ "*" ]
        , Effect = awacs.aws.Allow
        )
    , awacs.aws.Statement(
          Action = [ awacs.iam.DeleteRole
                   , awacs.iam.DeleteRolePolicy
                   , awacs.iam.GetRole
                   , awacs.iam.PutRolePolicy
                   , awacs.iam.CreateRole
                   , awacs.iam.PassRole
                   ]
        , Resource = [ "*" ]
        , Effect = awacs.aws.Allow
        )
    ]
  policy_doc = awacs.aws.Policy( Statement = statements )
  policy = Policy( PolicyDocument = policy_doc
                 , PolicyName = "CloudFormationDeployPolicy"
                 )
  assume = defaultAssumeRolePolicyDocument("cloudformation.amazonaws.com")
  role = t.add_resource(
         Role( "CFDeployRole"
             , RoleName = Sub("${AWS::StackName}-CFDeployRole")
             , AssumeRolePolicyDocument = assume
             , Policies = [policy]
             )
      )
  actionId = ActionTypeID( Category = "Deploy"
                         , Owner = "AWS"
                         , Version = "1"
                         , Provider = "CloudFormation"
                         )
  return (actionId, role)


def getDeploy( t: Template
             , inName: str
             , stage: str
             , resource: Tuple[ActionTypeID, Role]
             , code: str = None
             ) -> Stages:
  [actionId, role] = resource
  config = { "ActionMode" : "CREATE_UPDATE"
           , "RoleArn" : GetAtt(role, "Arn")
           , "StackName" : Sub("".join(["${AWS::StackName}Functions", stage]))
           , "Capabilities": "CAPABILITY_NAMED_IAM"
           , "TemplatePath" : inName + "::stack" + stage + ".json"
           }
  actions = [ Actions( Name = "Deploy" + stage
                     , ActionTypeId = actionId
                     , InputArtifacts = [InputArtifacts( Name = inName )]
                     , RunOrder = "1"
                     , Configuration = config
                     )
            ]
  if code is not None:
    actions.append(getTest(t, code, stage))
  return Stages( stage + "Deploy"
               , Name = stage + "_Deploy"
               , Actions = actions
               )
from troposphere import Template, Sub
from troposphere.codepipeline import ( Stages
                                     , Actions
                                     , ActionTypeID
                                     , OutputArtifacts
                                     )

def getSource(outputfiles: str, repo: str, branch: str) -> Stages:
  actionId = ActionTypeID( Category = "Source"
                         , Owner = "AWS"
                         , Version = "1"
                         , Provider = "CodeCommit"
                         )
  action = Actions( Name = Sub("${AWS::StackName}-LambdaSource")
                  , ActionTypeId = actionId
                  , Configuration = {"BranchName" : branch, "RepositoryName" : repo}
                  , OutputArtifacts = [OutputArtifacts( Name = outputfiles)]
                  , RunOrder = "1"
                  )
  return Stages( Name = "Source"
               , Actions = [ action ]
               )

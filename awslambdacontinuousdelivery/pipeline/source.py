from troposphere import Template, Sub, Parameter, Ref
from troposphere.codepipeline import ( Stages
                                     , Actions
                                     , ActionTypeID
                                     , OutputArtifacts
                                     )

def getGitHub(t: Template, outputfiles: str) -> Stages:
  owner = t.add_parameter( 
    Parameter( "GitHubOwner"
             , Description="GitHub repository owner"
             , Type="String"
             ) 
    )
  repo = t.add_parameter( 
    Parameter( "GitHubRepo"
             , Description="GitHub repository name"
             , Type="String"
             ) 
    )
  branch = t.add_parameter( 
    Parameter( "GitHubBranch"
             , Description="GitHub repository branch"
             , Type="String"
             ) 
    )
  token = t.add_parameter( 
    Parameter( "GitHubToken"
             , Description="GitHub repository OAuth token"
             , Type="String"
             ) 
    )
  actionId = ActionTypeID( Category = "Source"
                         , Owner = "ThirdParty"
                         , Version = "1"
                         , Provider = "GitHub"
                         )
  action = Actions( Name = Sub("${AWS::StackName}-LambdaSource")
                  , ActionTypeId = actionId
                  , Configuration = { "Owner" : Ref(owner)
                                    , "Repo" : Ref(repo)
                                    , "Branch" : Ref(branch)
                                    , "OAuthToken": Ref(branch)
                                    }
                  , OutputArtifacts = [OutputArtifacts( Name = outputfiles)]
                  , RunOrder = "1"
                  )
  return Stages( Name = "Source"
               , Actions = [ action ]
               )


def getCodeCommit(t: Template, outputfiles: str) -> Stages:
  repo = t.add_parameter(
    Parameter( "CodeCommitRepo"
             , Description="Name of the CodeCommit Repository"
             , Type="String"
             ) 
    )
  branch = t.add_parameter(
    Parameter( "Branch"
             , Description="Branch triggering the deployment"
             , Type="String"
             ) 
    )
  actionId = ActionTypeID( Category = "Source"
                         , Owner = "AWS"
                         , Version = "1"
                         , Provider = "CodeCommit"
                         )
  action = Actions( Name = Sub("${AWS::StackName}-LambdaSource")
                  , ActionTypeId = actionId
                  , Configuration = {"BranchName" : Ref(branch)
                                    , "RepositoryName" : Ref(repo)
                                    }
                  , OutputArtifacts = [OutputArtifacts( Name = outputfiles)]
                  , RunOrder = "1"
                  )
  return Stages( Name = "Source"
               , Actions = [ action ]
               )

def getSource(t: Template, github: bool, outputfiles: str) -> Stages:
  if github:
    return getGitHub(t, outputfiles)
  return getCodeCommit(t, outputfiles)
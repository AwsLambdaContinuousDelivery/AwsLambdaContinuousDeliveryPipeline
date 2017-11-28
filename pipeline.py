from awslambdacontinuousdelivery.pipeline import createPipeline

import argparse
import sys

if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  # parser.add_argument("-p", "--prefix", help = "Prefix for the Lambda Stacks", type = str, required=True)
  parser.add_argument("--github", help = "source is GitHub", type = bool)
  parser.add_argument("--codecommit", help = "source is CodeCommit", type = bool)
  parser.add_argument("--stages", nargs="+", help="Set flag and add all stage names EXCEPT PROD, if no flag is set, then there will be just a PROD stage", required=False)
  args = parser.parse_args()
  if not args.stages:
    args.stages = []
  print(createPipeline("AutoPipeline", args.stages))
from awslambdacontinuousdelivery.pipeline import createPipeline

import argparse
import sys

from cfn_flip import to_yaml

if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("--github", help = "source is GitHub", required = False, action = "store_true", default = False)
  parser.add_argument("--stages", nargs="+", help="Set flag and add all stage names EXCEPT PROD, if no flag is set, then there will be just a PROD stage", required=False)
  args = parser.parse_args()
  if not args.stages:
    args.stages = []
  some_json = createPipeline(args.stages, args.github)
  print(some_json)
  # print(to_yaml(some_json, clean_up=True))
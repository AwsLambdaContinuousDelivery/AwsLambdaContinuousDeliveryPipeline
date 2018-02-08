#!/usr/bin/env python

from distutils.core import setup

setup( name='pyAwsLambdaContinuousDeliveryPipeline'
     , version = '0.0.1'
     , description = 'pyAwsLambdaContinuousDeliveryPipeline'
     , author = 'Janos Potecki'
     , url = 'https://github.com/AwsLambdaContinuousDelivery/AwsLambdaContinuousDeliveryPipeline'
     , packages = ['awslambdacontinuousdelivery.pipeline']
     , license='MIT'
     , install_requires = [ 
          'troposphere'
        , 'awacs'
        ]
     )

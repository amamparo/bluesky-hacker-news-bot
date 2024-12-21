from os import getcwd

from aws_cdk import Stack, App, Duration
from aws_cdk.aws_ecr_assets import Platform
from aws_cdk.aws_events import Rule, Schedule
from aws_cdk.aws_events_targets import LambdaFunction
from aws_cdk.aws_lambda import DockerImageFunction, DockerImageCode
from aws_cdk.aws_secretsmanager import Secret
from constructs import Construct


class BotStack(Stack):
    def __init__(self, scope: Construct):
        super().__init__(scope, 'bsky-hn-bot')
        secret = Secret(self, 'secret', secret_name='bsky-hn-bot')

        function = DockerImageFunction(
            self,
            'function',
            memory_size=256,
            code=DockerImageCode.from_image_asset(
                directory=getcwd(),
                platform=Platform.LINUX_AMD64,
                cmd=['src.main.lambda_handler']
            ),
            environment={
                'SECRET_ARN': secret.secret_arn
            },
            timeout=Duration.minutes(1),
        )

        secret.grant_read(function)

        Rule(self, 'schedule', schedule=Schedule.rate(Duration.hours(1))).add_target(LambdaFunction(function))


if __name__ == '__main__':
    app = App()
    BotStack(app)
    app.synth()

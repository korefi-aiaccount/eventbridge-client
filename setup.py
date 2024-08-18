from setuptools import setup, find_packages

setup(
    name="eventbridge_client",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "boto3",
        "jsonschema",
        "requests",
    ],
    author="Apurv Hajare",
    author_email="apurv@karboncard.com",
    description="A simple EventBridge client for producing and consuming events",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://bitbucket.org/credit-application/eventbridge-client",
)
